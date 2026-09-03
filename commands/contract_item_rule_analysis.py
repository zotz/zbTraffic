
# File: commands/contract_item_rule_analysis.py

"""
Analyze contract item scheduling rules.
"""

import sys
from datetime import datetime, timedelta

from traffic.database import get_connection
from traffic.contract_item_rules import list_contract_item_rules

def analyze_limits(rule):

    min_day = rule["min_spots_per_day"]
    max_day = rule["max_spots_per_day"]
    min_week = rule["min_spots_per_week"]
    max_week = rule["max_spots_per_week"]

    results = []

    if min_day is None and max_day is None:

        results.append(
            "Daily: no limits."
        )

    elif min_day is not None and max_day is None:

        results.append(
            f"Daily: minimum {min_day}, no maximum."
        )

    elif min_day is None and max_day is not None:

        results.append(
            f"Daily: no minimum, maximum {max_day}."
        )

    elif min_day > max_day:

        results.append(
            f"Daily: INVALID - minimum {min_day} "
            f"exceeds maximum {max_day}."
        )

    elif min_day == max_day:

        results.append(
            f"Daily: exact value {min_day}."
        )

    else:

        results.append(
            f"Daily: {min_day} to {max_day}."
        )


    if min_week is None and max_week is None:

        results.append(
            "Weekly: no limits."
        )

    elif min_week is not None and max_week is None:

        results.append(
            f"Weekly: minimum {min_week}, no maximum."
        )

    elif min_week is None and max_week is not None:

        results.append(
            f"Weekly: no minimum, maximum {max_week}."
        )

    elif min_week > max_week:

        results.append(
            f"Weekly: INVALID - minimum {min_week} "
            f"exceeds maximum {max_week}."
        )

    elif min_week == max_week:

        results.append(
            f"Weekly: exact value {min_week}."
        )

    else:

        results.append(
            f"Weekly: {min_week} to {max_week}."
        )

    return results


def get_daily_scheduled_count(contract_item_id, air_date):

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
            air_date
        )
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count

def get_weekly_scheduled_count(contract_item_id, week_start):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM spots
        WHERE contract_item_id = ?
          AND air_date >= ?
          AND air_date < date(?, '+7 days')
          AND status IN ('Scheduled', 'Exported', 'Completed')
        """,
        (
            contract_item_id,
            str(week_start),
            str(week_start)
        )
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count


def get_scheduled_dates(contract_item_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DISTINCT air_date
        FROM spots
        WHERE contract_item_id = ?
          AND status IN ('Scheduled', 'Exported', 'Completed')
        ORDER BY air_date
        """,
        (contract_item_id,)
    )

    dates = [row[0] for row in cursor.fetchall()]

    connection.close()

    return dates

def get_week_start(air_date):

    date = datetime.strptime(
        air_date,
        "%Y-%m-%d"
    ).date()

    return date - timedelta(days=date.weekday())





def main():

    rules = list_contract_item_rules()

    total_items = 0
    items_with_violations = 0

    daily_min_violations = 0
    daily_max_violations = 0
    weekly_min_violations = 0
    weekly_max_violations = 0


    for rule in rules:

        total_items += 1
        item_has_violation = False

        print(
            f"Contract Item {rule['contract_item_id']}: "
            f"Min/Day={rule['min_spots_per_day']} "
            f"Max/Day={rule['max_spots_per_day']} "
            f"Min/Week={rule['min_spots_per_week']} "
            f"Max/Week={rule['max_spots_per_week']}"
        )

        dates = get_scheduled_dates(rule["contract_item_id"])

        week_starts = sorted(
            set(
                get_week_start(air_date)
                for air_date in dates
            )
        )



        for air_date in dates:

            count = get_daily_scheduled_count(
                rule["contract_item_id"],
                air_date
            )

            if rule["min_spots_per_day"] is not None and count < rule["min_spots_per_day"]:
                daily_min_violations += 1
                item_has_violation = True
                result = "BELOW MINIMUM"

            elif rule["max_spots_per_day"] is not None and count > rule["max_spots_per_day"]:
                daily_max_violations += 1
                item_has_violation = True
                result = "ABOVE MAXIMUM"

            else:
                result = "OK"

            print(
                f"  {air_date}: {count} scheduled ({result})"
            )

        for week_start in week_starts:

            weekly_count = get_weekly_scheduled_count(
                rule["contract_item_id"],
                week_start
            )

            if rule["min_spots_per_week"] is not None and weekly_count < rule["min_spots_per_week"]:
                weekly_min_violations += 1
                item_has_violation = True
                weekly_result = "BELOW MINIMUM"

            elif rule["max_spots_per_week"] is not None and weekly_count > rule["max_spots_per_week"]:
                weekly_max_violations += 1
                item_has_violation = True
                weekly_result = "ABOVE MAXIMUM"

            else:
                weekly_result = "OK"

            print(
                f"  Week starting {week_start}: "
                f"{weekly_count} scheduled ({weekly_result})"
            )

        if item_has_violation:
            items_with_violations += 1


        results = analyze_limits(rule)



        for result in results:

            print(
                f"  {result}"
            )



    print()
    print("=" * 60)
    print("Contract Item Rule Analysis Summary")
    print("=" * 60)
    print()
    print(f"Contract items analyzed:       {total_items}")
    print(f"Items with violations:         {items_with_violations}")
    print(f"Items with no violations:      {total_items - items_with_violations}")
    print()
    print(f"Daily minimum violations:      {daily_min_violations}")
    print(f"Daily maximum violations:      {daily_max_violations}")
    print(f"Weekly minimum violations:     {weekly_min_violations}")
    print(f"Weekly maximum violations:     {weekly_max_violations}")


if __name__ == "__main__":
    main()
