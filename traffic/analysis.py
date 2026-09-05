# File: traffic/analysis.py

"""
Reusable contract item scheduling analysis.

This module contains the non-CLI analysis logic used to determine:

    - Contract weeks anchored to the contract item start date
    - Eligible days within each contract week
    - Partial-week eligible-day fractions
    - Effective weekly minimums
    - Weekly maximums
    - Daily-derived flight minimums and maximums
    - Weekly-derived flight minimums and maximums
    - Effective flight minimum and maximum
    - Mathematical "IMPOSSIBLE ON ITS FACE" conditions
    - Current daily and weekly scheduling violations

Multiple rules on the same contract item are intentionally analyzed
independently. We do not assume that multiple rules are additive.

This module returns structured data and does not print anything.
"""

from datetime import datetime, timedelta


from traffic.database import get_connection
from traffic.contract_item_rules import list_contract_item_rules


# Scheduled spots are included in current schedule analysis.
SCHEDULED_STATUSES = (
    "Scheduled",
    "Exported",
    "Completed",
)


DAY_NAMES = (
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun",
)


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def parse_date(value):
    """Convert a YYYY-MM-DD value to a datetime.date object."""

    if value is None:
        return None

    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return value

    try:
        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()

    except (TypeError, ValueError):
        return None


def format_date(value):
    """Return a date as YYYY-MM-DD."""

    if value is None:
        return ""

    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")

    parsed = parse_date(value)

    if parsed is None:
        return str(value)

    return parsed.strftime("%Y-%m-%d")


def parse_days_of_week(value):
    """
    Parse a stored days-of-week value.

    The existing application stores day names such as:

        Mon,Tue,Fri

    Return a tuple of Python weekday numbers:

        Mon = 0
        Tue = 1
        ...
        Sun = 6
    """

    if not value:
        #return ()
        return tuple(range(7))

    if isinstance(value, (list, tuple, set)):
        values = value

    else:
        values = str(value).replace(" ", "").split(",")

    result = []

    for value in values:

        if isinstance(value, int):

            if 0 <= value <= 6:
                result.append(value)

            continue

        value = str(value)

        if value in DAY_NAMES:
            result.append(
                DAY_NAMES.index(value)
            )

    return tuple(result)


def day_name(weekday):
    """Return the three-letter day name for a Python weekday number."""

    if 0 <= weekday <= 6:
        return DAY_NAMES[weekday]

    return ""


def ceil_division(value, divisor):
    """Return ceil(value / divisor) using integer arithmetic."""

    if divisor == 0:
        return 0

    return (value + divisor - 1) // divisor


# ---------------------------------------------------------------------------
# Contract item lookup
# ---------------------------------------------------------------------------

def get_contract_item(contract_item_id):
    """
    Return contract item information.

    Returns:
        sqlite3.Row, or None.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            ci.id,
            ci.contract_id,
            ci.quantity,
            ci.start_date,
            ci.end_date,
            ci.commercial_title,
            c.description AS contract_description,
            c.contract_number,
            cu.company_name AS customer_name
        FROM contract_items ci
        JOIN contracts c
            ON c.id = ci.contract_id
        JOIN customers cu
            ON cu.id = c.customer_id
        WHERE ci.id = ?
        """,
        (
            contract_item_id,
        )
    )

    item = cursor.fetchone()

    connection.close()

    return item


# ---------------------------------------------------------------------------
# Contract week handling
# ---------------------------------------------------------------------------

def get_contract_week_groups(start_date, end_date):
    """
    Divide a contract item's flight into contract weeks.

    Contract weeks are anchored to the contract item's start date.

    The first week begins on start_date and runs for seven days.
    Subsequent weeks continue in seven-day blocks.

    The final week may therefore be a partial week.
    """

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    if start_date is None or end_date is None:
        return []

    if end_date < start_date:
        return []

    weeks = []

    week_start = start_date
    week_number = 1

    while week_start <= end_date:

        week_end = min(
            week_start + timedelta(days=6),
            end_date
        )

        full_week = (
            week_end - week_start
        ).days == 6

        weeks.append(
            {
                "number": week_number,
                "start": week_start,
                "end": week_end,
                "is_partial": not full_week,
            }
        )

        week_start = week_end + timedelta(days=1)
        week_number += 1

    return weeks


def get_eligible_dates(week, eligible_weekdays):
    """
    Return eligible dates within a contract week.
    """

    dates = []

    current = week["start"]

    while current <= week["end"]:

        if current.weekday() in eligible_weekdays:
            dates.append(current)

        current += timedelta(days=1)

    return dates


# ---------------------------------------------------------------------------
# Current schedule counts
# ---------------------------------------------------------------------------

def get_daily_scheduled_count(
    contract_item_id,
    air_date,
):
    """
    Count scheduled/exported/completed spots for a CI on one date.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM spots
        WHERE contract_item_id = ?
          AND air_date = ?
          AND status IN (?, ?, ?)
        """,
        (
            contract_item_id,
            format_date(air_date),
            SCHEDULED_STATUSES[0],
            SCHEDULED_STATUSES[1],
            SCHEDULED_STATUSES[2],
        )
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count


def get_weekly_scheduled_count(
    contract_item_id,
    start_date,
    end_date,
):
    """
    Count scheduled/exported/completed spots for a CI during a week.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM spots
        WHERE contract_item_id = ?
          AND air_date >= ?
          AND air_date <= ?
          AND status IN (?, ?, ?)
        """,
        (
            contract_item_id,
            format_date(start_date),
            format_date(end_date),
            SCHEDULED_STATUSES[0],
            SCHEDULED_STATUSES[1],
            SCHEDULED_STATUSES[2],
        )
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count


# ---------------------------------------------------------------------------
# Mathematical feasibility
# ---------------------------------------------------------------------------

def calculate_rule_math(rule, weeks, quantity):
    """
    Calculate flight-level mathematical constraints for one rule.

    Daily constraints and weekly constraints are NOT added together.

    Instead:

        effective minimum = stronger of daily/weekly minimums

        effective maximum = tighter of daily/weekly maximums
    """

    eligible_weekdays = parse_days_of_week(
        rule["days_of_week"]
    )

    normal_eligible_days = len(eligible_weekdays)

    # ------------------------------------------------------------------
    # Determine eligible dates in each contract week.
    # ------------------------------------------------------------------

    week_data = []

    total_eligible_days = 0

    for week in weeks:

        eligible_dates = get_eligible_dates(
            week,
            eligible_weekdays,
        )

        eligible_count = len(eligible_dates)

        total_eligible_days += eligible_count

        week_data.append(
            {
                "week": week,
                "eligible_dates": eligible_dates,
                "eligible_count": eligible_count,
            }
        )

    # ------------------------------------------------------------------
    # Daily-derived flight constraints.
    # ------------------------------------------------------------------

    min_day = rule["min_spots_per_day"]
    max_day = rule["max_spots_per_day"]

    daily_minimum = None
    daily_maximum = None

    if min_day is not None:

        daily_minimum = (
            total_eligible_days * min_day
        )

    if max_day is not None:

        daily_maximum = (
            total_eligible_days * max_day
        )

    # ------------------------------------------------------------------
    # Weekly-derived flight constraints.
    # ------------------------------------------------------------------

    min_week = rule["min_spots_per_week"]
    max_week = rule["max_spots_per_week"]

    weekly_minimum = None
    weekly_maximum = None

    weekly_minimum_parts = []
    weekly_maximum_parts = []

    if min_week is not None:

        weekly_minimum = 0

        for data in week_data:

            week = data["week"]
            eligible_count = data["eligible_count"]

            # If the entire set of rule-eligible days for the week
            # occurs inside the week, this is effectively a full week.
            #
            # This also handles a contract item shorter than seven days
            # when all of its rule-eligible days are present.

            if eligible_count == normal_eligible_days:

                effective_min = min_week

                fraction = (
                    f"{eligible_count}/{normal_eligible_days}"
                )

                effectively_full = True

            elif week["is_partial"] and normal_eligible_days > 0:

                effective_min = ceil_division(
                    min_week * eligible_count,
                    normal_eligible_days,
                )

                fraction = (
                    f"{eligible_count}/{normal_eligible_days}"
                )

                effectively_full = False

            else:

                effective_min = min_week

                fraction = (
                    f"{eligible_count}/{normal_eligible_days}"
                )

                effectively_full = False

            weekly_minimum += effective_min

            weekly_minimum_parts.append(
                {
                    "week_number": week["number"],
                    "effective_minimum": effective_min,
                    "eligible_count": eligible_count,
                    "normal_eligible_days": normal_eligible_days,
                    "fraction": fraction,
                    "effectively_full": effectively_full,
                }
            )

    if max_week is not None:

        # Weekly maximum is deliberately NOT prorated.

        weekly_maximum = 0

        for data in week_data:

            week_number = data["week"]["number"]

            weekly_maximum += max_week

            weekly_maximum_parts.append(
                {
                    "week_number": week_number,
                    "maximum": max_week,
                }
            )

    # ------------------------------------------------------------------
    # Effective flight constraints.
    # ------------------------------------------------------------------

    minimum_candidates = [
        value
        for value in (
            daily_minimum,
            weekly_minimum,
        )
        if value is not None
    ]

    maximum_candidates = [
        value
        for value in (
            daily_maximum,
            weekly_maximum,
        )
        if value is not None
    ]

    effective_minimum = (
        max(minimum_candidates)
        if minimum_candidates
        else None
    )

    effective_maximum = (
        min(maximum_candidates)
        if maximum_candidates
        else None
    )

    # ------------------------------------------------------------------
    # Impossible-on-face tests.
    # ------------------------------------------------------------------

    impossible_reasons = []

    if min_day is not None and max_day is not None:

        if min_day > max_day:

            impossible_reasons.append(
                f"minimum per day ({min_day}) exceeds "
                f"maximum per day ({max_day})"
            )

    if min_week is not None and max_week is not None:

        if min_week > max_week:

            impossible_reasons.append(
                f"minimum per week ({min_week}) exceeds "
                f"maximum per week ({max_week})"
            )

    if (
        effective_minimum is not None
        and effective_maximum is not None
        and effective_minimum > effective_maximum
    ):

        impossible_reasons.append(
            f"effective flight minimum ({effective_minimum}) "
            f"exceeds effective flight maximum ({effective_maximum})"
        )

    if (
        effective_minimum is not None
        and quantity < effective_minimum
    ):

        impossible_reasons.append(
            f"quantity ({quantity}) is less than "
            f"required minimum ({effective_minimum})"
        )

    if (
        effective_maximum is not None
        and quantity > effective_maximum
    ):

        impossible_reasons.append(
            f"quantity ({quantity}) exceeds "
            f"maximum ({effective_maximum})"
        )

    return {
        "eligible_weekdays": eligible_weekdays,
        "normal_eligible_days": normal_eligible_days,
        "week_data": week_data,
        "total_eligible_days": total_eligible_days,

        "daily_minimum": daily_minimum,
        "daily_maximum": daily_maximum,

        "weekly_minimum": weekly_minimum,
        "weekly_maximum": weekly_maximum,

        "weekly_minimum_parts": weekly_minimum_parts,
        "weekly_maximum_parts": weekly_maximum_parts,

        "effective_minimum": effective_minimum,
        "effective_maximum": effective_maximum,

        "impossible_reasons": impossible_reasons,
    }


# ---------------------------------------------------------------------------
# Current schedule analysis
# ---------------------------------------------------------------------------

def analyze_current_schedule(
    rule,
    contract_item_id,
    math_data,
):
    """
    Analyze the current scheduled spots against this rule.

    This is separate from mathematical feasibility.
    """

    daily_min = rule["min_spots_per_day"]
    daily_max = rule["max_spots_per_day"]

    weekly_min = rule["min_spots_per_week"]
    weekly_max = rule["max_spots_per_week"]

    daily_violations = []
    weekly_violations = []

    # ------------------------------------------------------------------
    # Daily checks
    # ------------------------------------------------------------------

    for data in math_data["week_data"]:

        for air_date in data["eligible_dates"]:

            count = get_daily_scheduled_count(
                contract_item_id,
                air_date,
            )

            result = "OK"

            if daily_min is not None and count < daily_min:

                result = "BELOW MINIMUM"

                daily_violations.append(
                    {
                        "date": air_date,
                        "count": count,
                        "result": result,
                    }
                )

            elif daily_max is not None and count > daily_max:

                result = "ABOVE MAXIMUM"

                daily_violations.append(
                    {
                        "date": air_date,
                        "count": count,
                        "result": result,
                    }
                )

    # ------------------------------------------------------------------
    # Weekly checks
    # ------------------------------------------------------------------

    for data in math_data["week_data"]:

        week = data["week"]

        count = get_weekly_scheduled_count(
            contract_item_id,
            week["start"],
            week["end"],
        )

        effective_min = None

        for part in math_data["weekly_minimum_parts"]:

            if part["week_number"] == week["number"]:

                effective_min = part["effective_minimum"]
                break

        result = "OK"

        if (
            effective_min is not None
            and count < effective_min
        ):

            result = "BELOW MINIMUM"

            weekly_violations.append(
                {
                    "week": week,
                    "count": count,
                    "effective_minimum": effective_min,
                    "result": result,
                }
            )

        elif (
            weekly_max is not None
            and count > weekly_max
        ):

            result = "ABOVE MAXIMUM"

            weekly_violations.append(
                {
                    "week": week,
                    "count": count,
                    "effective_minimum": effective_min,
                    "result": result,
                }
            )

    return {
        "daily_violations": daily_violations,
        "weekly_violations": weekly_violations,
    }


# ---------------------------------------------------------------------------
# Contract current status analysis
# ---------------------------------------------------------------------------

def analyze_current_status(contract_item_id, quantity):
    """
    Analyze the current spot status for a Contract Item.

    Returns:
        dict containing counts by status and an overall scheduling state.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM spots
        WHERE contract_item_id = ?
        GROUP BY status
        """,
        (contract_item_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    counts = {
        "Pending": 0,
        "Scheduled": 0,
        "Exported": 0,
        "Completed": 0,
        "Cancelled": 0,
    }

    for row in rows:
        status = row["status"]
        if status in counts:
            counts[status] = row["count"]

    active_count = (
        counts["Pending"]
        + counts["Scheduled"]
        + counts["Exported"]
        + counts["Completed"]
    )

    if active_count == 0:
        scheduling_state = "Not Scheduled"
    elif active_count < quantity:
        scheduling_state = "Partially Scheduled"
    else:
        scheduling_state = "Fully Scheduled"

    return {
        "counts": counts,
        "active_count": active_count,
        "scheduling_state": scheduling_state,
    }



# ---------------------------------------------------------------------------
# Contract item analysis
# ---------------------------------------------------------------------------

def analyze_contract_item(contract_item_id):
    """
    Analyze one contract item.

    This is the primary reusable entry point for GUI and other
    application code.

    Returns a structured dictionary containing:

        - contract item information
        - flight dates
        - contract week structure
        - analysis of every active rule
        - mathematical feasibility
        - current schedule violations
        - item-level result
    """

    item = get_contract_item(
        contract_item_id
    )

    if item is None:

        return {
            "status": "not_found",
            "contract_item_id": contract_item_id,
        }

    quantity = item["quantity"]

    current_status = analyze_current_status(
        contract_item_id,
        quantity,
    )

    start_date = parse_date(
        item["start_date"]
    )

    end_date = parse_date(
        item["end_date"]
    )

    if start_date is None or end_date is None:

        return {
            "status": "invalid",
            "reason": "incomplete_date_range",
            "contract_item_id": contract_item_id,
            "contract_item": item,
            "quantity": quantity,
        }

    if end_date < start_date:

        return {
            "status": "invalid",
            "reason": "end_date_before_start_date",
            "contract_item_id": contract_item_id,
            "contract_item": item,
            "quantity": quantity,
            "start_date": start_date,
            "end_date": end_date,
        }

    weeks = get_contract_week_groups(
        start_date,
        end_date,
    )

    item_rules = list_contract_item_rules(
        contract_item_id=contract_item_id
    )

    rule_results = []

    item_is_impossible = False
    item_has_violations = False

    for rule_number, rule in enumerate(
        item_rules,
        start=1,
    ):

        math_data = calculate_rule_math(
            rule,
            weeks,
            quantity,
        )

        current = analyze_current_schedule(
            rule,
            contract_item_id,
            math_data,
        )

        impossible = bool(
            math_data["impossible_reasons"]
        )

        has_violations = bool(
            current["daily_violations"]
            or current["weekly_violations"]
        )

        if impossible:
            item_is_impossible = True

        if has_violations:
            item_has_violations = True

        rule_results.append(
            {
                "rule_number": rule_number,
                "rule": rule,
                "math": math_data,
                "current_schedule": current,
                "impossible": impossible,
                "has_violations": has_violations,
            }
        )

    return {
        "status": "ok",
        "contract_item_id": contract_item_id,
        "contract_item": item,
        "quantity": quantity,
        "start_date": start_date,
        "end_date": end_date,
        "weeks": weeks,
        "rules": rule_results,
        "item_is_impossible": item_is_impossible,
        "item_has_violations": item_has_violations,
        "current_status": current_status,
    }
