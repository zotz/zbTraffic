# File: commands/contract_item_rule_analysis.py

"""
Analyze contract item scheduling rules.

This utility examines each contract item rule independently and reports:

    - Contract weeks anchored to the contract item's start date
    - Eligible days within each contract week
    - Partial-week eligible-day fractions
    - Effective weekly minimums, including prorating of the final partial week
    - Weekly maximums (not prorated)
    - Daily-derived flight minimums and maximums
    - Weekly-derived flight minimums and maximums
    - Effective flight minimum and maximum
    - Contract item quantity compared with those limits
    - Mathematical "IMPOSSIBLE ON ITS FACE" conditions
    - Current daily and weekly scheduling violations

Multiple rules on the same contract item are intentionally analyzed
independently. We do not assume that multiple rules are additive.
"""


import math
from datetime import datetime, timedelta

from traffic.database import get_connection
from traffic.contract_item_rules import list_contract_item_rules


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

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
    """Convert a YYYY-MM-DD value to a date object."""

    if value is None:
        return None

    if hasattr(value, "year"):
        return value

    return datetime.strptime(str(value), "%Y-%m-%d").date()


def format_date(value):
    """Return a date as YYYY-MM-DD."""

    if value is None:
        return ""

    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")

    return str(value)


def parse_days_of_week(value):
    """
    Return weekday numbers represented by days_of_week.

    Monday = 0 ... Sunday = 6.

    Blank/NULL means all seven days.
    """

    if not value:
        return set(range(7))

    requested = {
        part.strip().lower()
        for part in str(value).split(",")
        if part.strip()
    }

    aliases = {
        "mon": 0,
        "monday": 0,
        "tue": 1,
        "tues": 1,
        "tuesday": 1,
        "wed": 2,
        "wednesday": 2,
        "thu": 3,
        "thur": 3,
        "thurs": 3,
        "thursday": 3,
        "fri": 4,
        "friday": 4,
        "sat": 5,
        "saturday": 5,
        "sun": 6,
        "sunday": 6,
    }

    result = set()

    for day in requested:
        if day in aliases:
            result.add(aliases[day])

    return result


def day_name(weekday):
    """Return Mon/Tue/etc."""

    return DAY_NAMES[weekday]


def ceil_division(value, divisor):
    """
    Return ceil(value / divisor).

    Kept as a helper because the prorating calculation should be
    visibly integer-safe.
    """

    return (value + divisor - 1) // divisor


# ---------------------------------------------------------------------------
# Contract item information
# ---------------------------------------------------------------------------

def get_contract_item(contract_item_id):
    """Return contract item information."""

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
        (contract_item_id,)
    )

    row = cursor.fetchone()

    connection.close()

    return row


# ---------------------------------------------------------------------------
# Contract weeks
# ---------------------------------------------------------------------------

def get_contract_week_groups(start_date, end_date):
    """
    Return contract-week groups anchored to start_date.

    Example:

        start = Saturday 2026-08-15

        Week 1 = 2026-08-15 through 2026-08-21
        Week 2 = 2026-08-22 through 2026-08-28
        ...

    There is deliberately NO calendar/Monday week calculation here.
    """

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    weeks = []

    current_start = start_date
    week_number = 1

    while current_start <= end_date:

        nominal_end = current_start + timedelta(days=6)

        actual_end = min(
            nominal_end,
            end_date
        )

        is_partial = actual_end < nominal_end

        weeks.append(
            {
                "number": week_number,
                "start": current_start,
                "end": actual_end,
                "is_partial": is_partial,
                "calendar_days": (
                    actual_end - current_start
                ).days + 1,
            }
        )

        current_start = current_start + timedelta(days=7)
        week_number += 1

    return weeks


def get_eligible_dates(week, eligible_weekdays):
    """Return eligible dates within a contract week."""

    dates = []

    current = week["start"]

    while current <= week["end"]:

        if current.weekday() in eligible_weekdays:
            dates.append(current)

        current += timedelta(days=1)

    return dates


# ---------------------------------------------------------------------------
# Scheduled counts
# ---------------------------------------------------------------------------

def get_daily_scheduled_count(contract_item_id, air_date):
    """Return scheduled/exported/completed count for one date."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM spots
        WHERE contract_item_id = ?
          AND air_date = ?
          AND status IN ('Scheduled', 'Exported', 'Completed')
        """,
        (
            contract_item_id,
            format_date(air_date),
        )
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count


def get_weekly_scheduled_count(
    contract_item_id,
    week_start,
    week_end,
):
    """Return scheduled/exported/completed count within a contract week."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM spots
        WHERE contract_item_id = ?
          AND air_date >= ?
          AND air_date <= ?
          AND status IN ('Scheduled', 'Exported', 'Completed')
        """,
        (
            contract_item_id,
            format_date(week_start),
            format_date(week_end),
        )
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count


# ---------------------------------------------------------------------------
# Rule descriptions
# ---------------------------------------------------------------------------

def describe_daily_limits(rule):
    """Return human-readable daily constraint description."""

    min_day = rule["min_spots_per_day"]
    max_day = rule["max_spots_per_day"]

    if min_day is None and max_day is None:
        return "Daily: no limits."

    if min_day is not None and max_day is None:
        return (
            f"Daily: minimum {min_day}, no maximum."
        )

    if min_day is None and max_day is not None:
        return (
            f"Daily: no minimum, maximum {max_day}."
        )

    if min_day > max_day:
        return (
            f"Daily: INVALID - minimum {min_day} "
            f"exceeds maximum {max_day}."
        )

    if min_day == max_day:
        return (
            f"Daily: exact value {min_day}."
        )

    return (
        f"Daily: {min_day} to {max_day}."
    )


def describe_weekly_limits(rule):
    """Return human-readable weekly constraint description."""

    min_week = rule["min_spots_per_week"]
    max_week = rule["max_spots_per_week"]

    if min_week is None and max_week is None:
        return "Weekly: no limits."

    if min_week is not None and max_week is None:
        return (
            f"Weekly: minimum {min_week}, no maximum."
        )

    if min_week is None and max_week is not None:
        return (
            f"Weekly: no minimum, maximum {max_week}."
        )

    if min_week > max_week:
        return (
            f"Weekly: INVALID - minimum {min_week} "
            f"exceeds maximum {max_week}."
        )

    if min_week == max_week:
        return (
            f"Weekly: exact value {min_week}."
        )

    return (
        f"Weekly: {min_week} to {max_week}."
    )


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
        #
        # Even the final partial contract week retains the configured
        # weekly maximum.

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
# Output helpers
# ---------------------------------------------------------------------------

def print_constraint_summary(rule, math_data, quantity):
    """Print the flight-level mathematical constraint summary."""

    print()
    print("  Constraint summary:")
    print()

    total_days = math_data["total_eligible_days"]

    min_day = rule["min_spots_per_day"]
    max_day = rule["max_spots_per_day"]

    # Daily minimum

    if min_day is not None:

        print(
            f"    Flight minimum from daily:"
        )

        print(
            f"      {total_days} eligible contract days "
            f"× {min_day} spots/day = "
            f"{math_data['daily_minimum']}"
        )

    else:

        print(
            "    Flight minimum from daily: none"
        )

    # Daily maximum

    if max_day is not None:

        print(
            f"    Flight maximum from daily:"
        )

        print(
            f"      {total_days} eligible contract days "
            f"× {max_day} spots/day = "
            f"{math_data['daily_maximum']}"
        )

    else:

        print(
            "    Flight maximum from daily: unlimited"
        )

    # Weekly minimum

    if rule["min_spots_per_week"] is not None:

        print()
        print(
            "    Flight minimum from weekly:"
        )

        for part in math_data["weekly_minimum_parts"]:

            if part["effectively_full"]:

                print(
                    f"      Week {part['week_number']}: "
                    f"{part['eligible_count']}/"
                    f"{part['normal_eligible_days']} eligible days "
                    f"→ effectively full week → "
                    f"{part['effective_minimum']}"
                )

            else:

                print(
                    f"      Week {part['week_number']}: "
                    f"{part['eligible_count']}/"
                    f"{part['normal_eligible_days']} eligible days "
                    f"→ prorated minimum "
                    f"{part['effective_minimum']}"
                )

        print(
            "      --------------------------------"
        )

        if len(math_data["weekly_minimum_parts"]) == 1:

            print(
                f"      Weekly minimum total = "
                f"{math_data['weekly_minimum']}"
            )

        else:

            full_values = [
                part["effective_minimum"]
                for part in math_data["weekly_minimum_parts"]
            ]

            print(
                "      "
                + " + ".join(str(value) for value in full_values)
                + f" = {math_data['weekly_minimum']}"
            )

    else:

        print()
        print(
            "    Flight minimum from weekly: none"
        )

    # Weekly maximum

    if rule["max_spots_per_week"] is not None:

        print()
        print(
            "    Flight maximum from weekly:"
        )

        for part in math_data["weekly_maximum_parts"]:

            print(
                f"      Week {part['week_number']}: "
                f"{part['maximum']}"
                f" (weekly maximum is not prorated)"
            )

        print(
            "      --------------------------------"
        )

        max_values = [
            part["maximum"]
            for part in math_data["weekly_maximum_parts"]
        ]

        if len(max_values) == 1:

            print(
                f"      Weekly maximum total = "
                f"{math_data['weekly_maximum']}"
            )

        else:

            print(
                "      "
                + " + ".join(str(value) for value in max_values)
                + f" = {math_data['weekly_maximum']}"
            )

    else:

        print()
        print(
            "    Flight maximum from weekly: unlimited"
        )

    # Effective constraints

    print()
    print(
        "    Effective flight minimum:"
    )

    minimum_sources = []

    if math_data["daily_minimum"] is not None:
        minimum_sources.append(
            f"daily {math_data['daily_minimum']}"
        )

    if math_data["weekly_minimum"] is not None:
        minimum_sources.append(
            f"weekly {math_data['weekly_minimum']}"
        )

    if minimum_sources:

        print(
            "      stronger of "
            + " and ".join(minimum_sources)
            + f" = {math_data['effective_minimum']}"
        )

    else:

        print(
            "      none"
        )

    print()
    print(
        "    Effective flight maximum:"
    )

    maximum_sources = []

    if math_data["daily_maximum"] is not None:
        maximum_sources.append(
            f"daily {math_data['daily_maximum']}"
        )

    if math_data["weekly_maximum"] is not None:
        maximum_sources.append(
            f"weekly {math_data['weekly_maximum']}"
        )

    if maximum_sources:

        print(
            "      tighter of "
            + " and ".join(maximum_sources)
            + f" = {math_data['effective_maximum']}"
        )

    else:

        print(
            "      unlimited"
        )

    # Quantity

    print()
    print(
        f"    Contract item quantity: {quantity}"
    )

    if math_data["effective_minimum"] is not None:

        if quantity < math_data["effective_minimum"]:

            print(
                f"      TOO LOW: quantity {quantity} "
                f"< required minimum "
                f"{math_data['effective_minimum']}"
            )

        else:

            print(
                f"      Meets minimum: quantity {quantity} "
                f">= {math_data['effective_minimum']}"
            )

    if math_data["effective_maximum"] is not None:

        if quantity > math_data["effective_maximum"]:

            print(
                f"      TOO HIGH: quantity {quantity} "
                f"> maximum "
                f"{math_data['effective_maximum']}"
            )

        else:

            print(
                f"      Within maximum: quantity {quantity} "
                f"<= {math_data['effective_maximum']}"
            )


def print_week_structure(weeks):
    """Print contract weeks."""

    print()
    print("  Contract weeks:")

    for week in weeks:

        if week["is_partial"]:

            label = (
                f"FINAL PARTIAL — "
                f"{week['calendar_days']}/7 calendar days"
            )

        else:

            label = "FULL"

        print(
            f"    Week {week['number']}: "
            f"{format_date(week['start'])} through "
            f"{format_date(week['end'])} "
            f"[{label}]"
        )


def print_rule_week_analysis(
    rule,
    contract_item_id,
    math_data,
):
    """Print detailed per-week analysis for one rule."""

    print()
    print("  Rule week analysis:")
    print()

    eligible_weekdays = math_data["eligible_weekdays"]

    if rule["days_of_week"]:

        print(
            f"    Rule days: {rule['days_of_week']}"
        )

    else:

        print(
            "    Rule days: all days"
        )

    print(
        f"    Normal eligible days per contract week: "
        f"{math_data['normal_eligible_days']}"
    )

    for data in math_data["week_data"]:

        week = data["week"]
        eligible_dates = data["eligible_dates"]
        eligible_count = data["eligible_count"]

        date_names = [
            day_name(date.weekday())
            for date in eligible_dates
        ]

        names = ", ".join(date_names)

        fraction = (
            f"{eligible_count}/"
            f"{math_data['normal_eligible_days']}"
        )

        effectively_full = (
            eligible_count
            == math_data["normal_eligible_days"]
        )

        if effectively_full:

            fraction_text = (
                f"{fraction} eligible days "
                f"[EFFECTIVELY FULL]"
            )

        else:

            fraction_text = (
                f"{fraction} eligible days"
            )

        print(
            f"    Week {week['number']}: "
            f"{format_date(week['start'])} through "
            f"{format_date(week['end'])}"
        )

        print(
            f"      Eligible dates: "
            f"{names if names else 'none'}"
        )

        print(
            f"      Eligible-day fraction: "
            f"{fraction_text}"
        )

        scheduled = get_weekly_scheduled_count(
            contract_item_id,
            week["start"],
            week["end"],
        )

        if rule["min_spots_per_week"] is not None:

            effective_min = None

            for part in math_data["weekly_minimum_parts"]:

                if part["week_number"] == week["number"]:

                    effective_min = part["effective_minimum"]
                    break

            print(
                f"      Effective weekly minimum: "
                f"{effective_min}"
            )

        else:

            effective_min = None

            print(
                "      Effective weekly minimum: none"
            )

        if rule["max_spots_per_week"] is not None:

            print(
                f"      Weekly maximum: "
                f"{rule['max_spots_per_week']}"
            )

        else:

            print(
                "      Weekly maximum: unlimited"
            )

        # Physical capacity is based on maximum constraints.
        daily_capacity = None
        weekly_capacity = None

        if rule["max_spots_per_day"] is not None:

            daily_capacity = (
                eligible_count
                * rule["max_spots_per_day"]
            )

        if rule["max_spots_per_week"] is not None:

            weekly_capacity = (
                rule["max_spots_per_week"]
            )

        if (
            daily_capacity is not None
            and weekly_capacity is not None
        ):

            physical_capacity = min(
                daily_capacity,
                weekly_capacity,
            )

        elif daily_capacity is not None:

            physical_capacity = daily_capacity

        elif weekly_capacity is not None:

            physical_capacity = weekly_capacity

        else:

            physical_capacity = None

        if physical_capacity is not None:

            if (
                daily_capacity is not None
                and weekly_capacity is not None
            ):

                print(
                    f"      Physical capacity: "
                    f"min("
                    f"{eligible_count} eligible days × "
                    f"{rule['max_spots_per_day']}/day = "
                    f"{daily_capacity}, "
                    f"{weekly_capacity}/week"
                    f") = {physical_capacity}"
                )

            else:

                print(
                    f"      Physical capacity: "
                    f"{physical_capacity}"
                )

        else:

            print(
                "      Physical capacity: unlimited"
            )

        if (
            effective_min is not None
            and scheduled < effective_min
        ):

            result = "BELOW MINIMUM"

        elif (
            rule["max_spots_per_week"] is not None
            and scheduled > rule["max_spots_per_week"]
        ):

            result = "ABOVE MAXIMUM"

        else:

            result = "OK"

        print(
            f"      Scheduled: {scheduled} ({result})"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    rules = list_contract_item_rules()

    # Group rules by contract item.
    items = {}

    for rule in rules:

        contract_item_id = rule["contract_item_id"]

        items.setdefault(
            contract_item_id,
            []
        ).append(rule)

    total_items = 0

    items_with_violations = 0
    items_impossible = 0

    daily_min_violations = 0
    daily_max_violations = 0
    weekly_min_violations = 0
    weekly_max_violations = 0

    total_rules = 0

    for contract_item_id, item_rules in items.items():

        item = get_contract_item(contract_item_id)

        if item is None:

            print()
            print(
                f"Contract Item {contract_item_id}: "
                "unable to retrieve contract item."
            )

            continue

        total_items += 1

        quantity = item["quantity"]

        start_date = parse_date(
            item["start_date"]
        )

        end_date = parse_date(
            item["end_date"]
        )

        if start_date is None or end_date is None:

            print()
            print("=" * 72)
            print(
                f"Contract Item {contract_item_id}"
            )
            print("=" * 72)
            print(
                "  Cannot analyze: contract item has "
                "no complete start/end date range."
            )

            continue

        weeks = get_contract_week_groups(
            start_date,
            end_date,
        )

        print()
        print("=" * 72)
        print(
            f"Contract Item {contract_item_id}"
        )
        print("=" * 72)

        print(
            f"  Customer:   {item['customer_name']}"
        )

        print(
            f"  Contract:   {item['contract_id']}"
        )

        if item["contract_number"]:

            print(
                f"  Contract #: {item['contract_number']}"
            )

        print(
            f"  Commercial: {item['commercial_title']}"
        )

        print(
            f"  Quantity:   {quantity}"
        )

        print(
            f"  Flight:     "
            f"{format_date(start_date)} through "
            f"{format_date(end_date)}"
        )

        print(
            f"  Flight days: "
            f"{(end_date - start_date).days + 1}"
        )

        print_week_structure(weeks)

        item_has_violation = False
        item_is_impossible = False

        # --------------------------------------------------------------
        # Analyze each rule independently.
        # --------------------------------------------------------------

        for rule_number, rule in enumerate(
            item_rules,
            start=1,
        ):

            total_rules += 1

            print()
            print(
                f"  {'-' * 64}"
            )

            print(
                f"  Rule {rule_number} "
                f"(Rule ID {rule['id']})"
            )

            print(
                f"  {'-' * 64}"
            )

            print(
                f"  {describe_daily_limits(rule)}"
            )

            print(
                f"  {describe_weekly_limits(rule)}"
            )

            math_data = calculate_rule_math(
                rule,
                weeks,
                quantity,
            )

            # ----------------------------------------------------------
            # Constraint mathematics
            # ----------------------------------------------------------

            print_constraint_summary(
                rule,
                math_data,
                quantity,
            )

            # ----------------------------------------------------------
            # Impossible-on-face result
            # ----------------------------------------------------------

            if math_data["impossible_reasons"]:

                item_is_impossible = True

                print()
                print(
                    "    RESULT: IMPOSSIBLE ON ITS FACE"
                )

                for reason in math_data["impossible_reasons"]:

                    print(
                        f"      - {reason}"
                    )

            else:

                minimum_text = (
                    str(math_data["effective_minimum"])
                    if math_data["effective_minimum"] is not None
                    else "none"
                )

                maximum_text = (
                    str(math_data["effective_maximum"])
                    if math_data["effective_maximum"] is not None
                    else "unlimited"
                )

                print(
                    f"    Mathematical quantity range: "
                    f"{minimum_text} to {maximum_text}"
                )

            # ----------------------------------------------------------
            # Current schedule
            # ----------------------------------------------------------

            current = analyze_current_schedule(
                rule,
                contract_item_id,
                math_data,
            )

            if current["daily_violations"]:

                item_has_violation = True

                for violation in current["daily_violations"]:

                    if violation["result"] == "BELOW MINIMUM":

                        daily_min_violations += 1

                    elif violation["result"] == "ABOVE MAXIMUM":

                        daily_max_violations += 1

            if current["weekly_violations"]:

                item_has_violation = True

                for violation in current["weekly_violations"]:

                    if violation["result"] == "BELOW MINIMUM":

                        weekly_min_violations += 1

                    elif violation["result"] == "ABOVE MAXIMUM":

                        weekly_max_violations += 1

            print_rule_week_analysis(
                rule,
                contract_item_id,
                math_data,
            )

        # --------------------------------------------------------------
        # Item-level result
        #
        # Multiple rules are not combined mathematically here.
        # If any rule is intrinsically impossible, the item is flagged.
        # --------------------------------------------------------------

        if item_is_impossible:

            items_impossible += 1

            print()
            print(
                "  ITEM RESULT: IMPOSSIBLE ON ITS FACE"
            )

            print(
                "  At least one rule cannot be satisfied by "
                "the contract item quantity."
            )

        elif item_has_violation:

            items_with_violations += 1

            print()
            print(
                "  ITEM RESULT: VIOLATIONS FOUND"
            )

        else:

            print()
            print(
                "  ITEM RESULT: NO CURRENT VIOLATIONS"
            )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    print()
    print("=" * 72)
    print("Contract Item Rule Analysis Summary")
    print("=" * 72)
    print()

    print(
        f"Contract items analyzed:       {total_items}"
    )

    print(
        f"Rules analyzed:                {total_rules}"
    )

    print(
        f"Items impossible on its face:  {items_impossible}"
    )

    print(
        f"Items with violations:         {items_with_violations}"
    )

    print(
        f"Items with no violations:      "
        f"{total_items - items_impossible - items_with_violations}"
    )

    print()

    print(
        f"Daily minimum violations:      "
        f"{daily_min_violations}"
    )

    print(
        f"Daily maximum violations:      "
        f"{daily_max_violations}"
    )

    print(
        f"Weekly minimum violations:     "
        f"{weekly_min_violations}"
    )

    print(
        f"Weekly maximum violations:     "
        f"{weekly_max_violations}"
    )


if __name__ == "__main__":
    main()