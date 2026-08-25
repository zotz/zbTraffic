#!/usr/bin/env python3

# File: tests/scheduler_big_regression_test.py

import os
import sys
from collections import defaultdict


#
# Make the project root importable when this script is run as:
#
#     python3 tests/scheduler_big_regression_test.py
#

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from traffic.database import get_connection


CONTRACT_NUMBER = "ZZL-2026-001"
COMMERCIAL_TITLE = "zbT Zephyr Life 30"

EXPECTED_QUANTITY = 15


passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed
    global failed

    if condition:
        print(f"PASS: {name}")
        passed += 1

    else:
        print(f"FAIL: {name}")

        if detail:
            print(f"      {detail}")

        failed += 1


def main():

    connection = get_connection()
    cursor = connection.cursor()

    print()
    print("=" * 60)
    print("Big Dataset Scheduler Regression Test")
    print("=" * 60)
    print()


    #
    # Find the contract by contract number.
    #

    cursor.execute(
        """
        SELECT
            id,
            customer_id,
            salesperson_id,
            station_id,
            contract_number,
            description,
            start_date,
            end_date,
            status
        FROM contracts
        WHERE contract_number = ?
        """,
        (
            CONTRACT_NUMBER,
        )
    )

    contract = cursor.fetchone()

    if contract is None:

        print(
            f"ERROR: Contract '{CONTRACT_NUMBER}' was not found."
        )

        connection.close()
        return 1


    contract_id = contract["id"]


    print(
        f"Contract: {contract['contract_number']}"
    )

    print(
        f"Description: {contract['description']}"
    )

    print(
        f"Flight: "
        f"{contract['start_date']} "
        f"-> "
        f"{contract['end_date']}"
    )

    print()


    #
    # Find the contract item.
    #
    # We identify it by the contract and commercial title,
    # rather than assuming a particular database ID.
    #

    cursor.execute(
        """
        SELECT
            id,
            commercial_id,
            commercial_title,
            quantity,
            start_date,
            end_date
        FROM contract_items
        WHERE contract_id = ?
        AND commercial_title = ?
        """,
        (
            contract_id,
            COMMERCIAL_TITLE,
        )
    )

    contract_item = cursor.fetchone()

    if contract_item is None:

        print(
            "ERROR: Could not find the Zephyr Life "
            "contract item."
        )

        connection.close()
        return 1


    contract_item_id = contract_item["id"]


    print(
        f"Contract item: {contract_item_id}"
    )

    print(
        f"Commercial: "
        f"{contract_item['commercial_title']}"
    )

    print(
        f"Quantity: "
        f"{contract_item['quantity']}"
    )

    print(
        f"Contract item flight: "
        f"{contract_item['start_date']} "
        f"-> "
        f"{contract_item['end_date']}"
    )

    print()


    #
    # Use the contract item's actual flight dates.
    #

    start_date = contract_item["start_date"]
    end_date = contract_item["end_date"]


    #
    # Test 1
    #
    # Expected quantity.
    #

    test(
        f"Expected quantity is {EXPECTED_QUANTITY}",
        contract_item["quantity"] == EXPECTED_QUANTITY,
        (
            f"expected={EXPECTED_QUANTITY}, "
            f"actual={contract_item['quantity']}"
        )
    )


    #
    # Test 2
    #
    # Contract item should have no rules.
    #

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM contract_item_rules
        WHERE contract_item_id = ?
        """,
        (
            contract_item_id,
        )
    )

    rule_count = cursor.fetchone()[0]


    test(
        "Contract item has no rules",
        rule_count == 0,
        f"rules={rule_count}"
    )


    #
    # Get all spots for this contract item.
    #

    cursor.execute(
        """
        SELECT
            id,
            contract_item_id,
            commercial_id,
            avail_id,
            air_date,
            air_time,
            status
        FROM spots
        WHERE contract_item_id = ?
        ORDER BY air_date, air_time, id
        """,
        (
            contract_item_id,
        )
    )

    spots = cursor.fetchall()


    #
    # Only count scheduled spots.
    #

    scheduled_spots = [
        spot
        for spot in spots
        if spot["status"] == "Scheduled"
    ]


    #
    # Test 3
    #
    # Exactly EXPECTED_QUANTITY spots should have been scheduled.
    #

    test(
        f"Scheduled quantity is {EXPECTED_QUANTITY}",
        len(scheduled_spots) == EXPECTED_QUANTITY,
        (
            f"expected={EXPECTED_QUANTITY}, "
            f"scheduled={len(scheduled_spots)}"
        )
    )



    #
    # Test 4
    #
    # Every scheduled spot must belong to this contract item.
    #

    wrong_contract_items = [
        spot["id"]
        for spot in scheduled_spots
        if spot["contract_item_id"] != contract_item_id
    ]


    test(
        "Every scheduled spot belongs to the contract item",
        len(wrong_contract_items) == 0,
        f"wrong spots={wrong_contract_items}"
    )


    #
    # Test 5
    #
    # All scheduled dates must be inside the contract item flight.
    #

    outside_flight = [
        spot
        for spot in scheduled_spots
        if (
            spot["air_date"] < start_date
            or spot["air_date"] > end_date
        )
    ]


    test(
        "All scheduled dates are within the flight",
        len(outside_flight) == 0,
        (
            "outside-flight spot IDs="
            + str(
                [
                    spot["id"]
                    for spot in outside_flight
                ]
            )
        )
    )


    #
    # Test 6
    #
    # Every scheduled spot must reference an existing avail.
    #

    missing_avails = []


    for spot in scheduled_spots:

        cursor.execute(
            """
            SELECT
                id
            FROM avails
            WHERE id = ?
            """,
            (
                spot["avail_id"],
            )
        )

        avail = cursor.fetchone()

        if avail is None:
            missing_avails.append(spot["id"])


    test(
        "Every scheduled spot has a valid avail",
        len(missing_avails) == 0,
        f"missing avail for spots={missing_avails}"
    )


    #
    # Test 7
    #
    # Make sure no avail has been overfilled.
    #

    cursor.execute(
        """
        SELECT
            a.id,
            a.length_seconds,
            COALESCE(
                SUM(ci.spot_length_seconds),
                0
            ) AS scheduled_seconds

        FROM avails a

        JOIN spots s
            ON s.avail_id = a.id

        JOIN contract_items ci
            ON ci.id = s.contract_item_id

        WHERE s.status = 'Scheduled'

        GROUP BY
            a.id,
            a.length_seconds

        HAVING
            scheduled_seconds > a.length_seconds

        ORDER BY a.id
        """
    )

    overfilled_avails = cursor.fetchall()


    test(
        "No avails are overfilled",
        len(overfilled_avails) == 0,
        (
            "overfilled avails="
            + str(
                [
                    row["id"]
                    for row in overfilled_avails
                ]
            )
        )
    )


    #
    # Distribution report.
    #
    # This is intentionally NOT a pass/fail test yet.
    #
    # We want to see what the current scheduler does before
    # deciding what distribution behavior we actually want.
    #

    distribution = defaultdict(int)


    for spot in scheduled_spots:
        distribution[spot["air_date"]] += 1


    print()
    print("-" * 60)
    print("Zephyr Life Spot Distribution By Day")
    print("-" * 60)


    if distribution:

        for air_date in sorted(distribution):

            print(
                f"{air_date}: "
                f"{distribution[air_date]}"
            )

    else:

        print("No scheduled spots found.")


    #
    # Print the actual spot IDs as an additional diagnostic.
    #

    print()
    print("Scheduled Spot IDs:")

    print(
        [
            spot["id"]
            for spot in scheduled_spots
        ]
    )


    #
    # Summary.
    #

    print()
    print("=" * 60)
    print("Big Dataset Scheduler Regression Results")
    print("=" * 60)

    print(
        f"Tests passed: {passed}"
    )

    print(
        f"Tests failed: {failed}"
    )


    if failed == 0:

        print()
        print("ALL BIG DATASET SCHEDULER TESTS PASSED")
        print()

        connection.close()
        return 0


    print()
    print("BIG DATASET SCHEDULER TESTS FAILED")
    print()

    connection.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
