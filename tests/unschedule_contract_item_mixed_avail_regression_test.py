#!/usr/bin/env python3

# File: tests/unschedule_contract_item_mixed_avail_regression_test.py

"""
Regression test for contract-item-level unscheduling when multiple
contract items occupy the same avails.

This test verifies that:

    1. CI A and CI B each have their expected number of spots.
    2. Some avails contain both A and B spots.
    3. Descheduling CI A:
         - removes all A spots
         - leaves all B spots untouched
         - changes A-only avails to Open
         - changes mixed A+B avails to Partial
         - leaves B-only avails Filled
    4. Descheduling CI B:
         - removes all remaining B spots
         - leaves all test avails Open
         - leaves no test spots behind
    5. Cleanup removes all test data.

The test uses the default active station rather than creating a test station.
"""

import os
import sys
from datetime import datetime

#
# Make the project root importable regardless of the current working
# directory.
#
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from traffic.database import get_connection
from traffic.spots import unschedule_contract_item
from traffic.avails import update_avail_status


passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed

    if condition:
        print(f"PASS: {name}")
        passed += 1
    else:
        print(f"FAIL: {name}")
        if detail:
            print(f"      {detail}")
        failed += 1


def main():
    
    global passed
    global failed


    #
    # ----------------------------------------------------------
    # IDs for test data.
    # ----------------------------------------------------------
    #

    customer_a_id = None
    customer_b_id = None

    commercial_a_id = None
    commercial_b_id = None

    salesperson_a_id = None
    salesperson_b_id = None

    contract_a_id = None
    contract_b_id = None

    contract_item_a_id = None
    contract_item_b_id = None

    rule_a_id = None
    rule_b_id = None

    test_avail_ids = []
    test_spot_ids = []

    #
    # Labels make the avail expectations easy to read later.
    #
    avail_by_label = {}

    connection = None

    try:

        #
        # ------------------------------------------------------
        # Create test data.
        # ------------------------------------------------------
        #

        connection = get_connection()
        cursor = connection.cursor()

        #
        # Use the first active station in the real database.
        #
        cursor.execute(
            """
            SELECT id
            FROM stations
            WHERE active = 1
            ORDER BY id
            LIMIT 1
            """
        )

        station = cursor.fetchone()

        if station is None:
            print("ERROR: No active station exists.")
            return 1

        station_id = station["id"]

        #
        # Find a real salesperson.
        #
        cursor.execute(
            """
            SELECT id
            FROM salespeople
            ORDER BY id
            LIMIT 1
            """
        )

        salesperson = cursor.fetchone()

        if salesperson is None:
            print("ERROR: No salesperson exists.")
            return 1

        salesperson_a_id = salesperson["id"]
        salesperson_b_id = salesperson["id"]

        #
        # ------------------------------------------------------
        # Customers.
        # ------------------------------------------------------
        #

        cursor.execute(
            """
            INSERT INTO customers (
                company_name,
                active,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "Unschedule Mixed Test Customer A",
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        customer_a_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO customers (
                company_name,
                active,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "Unschedule Mixed Test Customer B",
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        customer_b_id = cursor.lastrowid

        #
        # ------------------------------------------------------
        # Commercials.
        # ------------------------------------------------------
        #

        cursor.execute(
            """
            INSERT INTO commercials (
                customer_id,
                title,
                length_seconds,
                active,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                customer_a_id,
                "Unschedule Mixed Test Commercial A",
                30,
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        commercial_a_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO commercials (
                customer_id,
                title,
                length_seconds,
                active,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                customer_b_id,
                "Unschedule Mixed Test Commercial B",
                30,
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        commercial_b_id = cursor.lastrowid

        #
        # ------------------------------------------------------
        # Contracts.
        # ------------------------------------------------------
        #

        cursor.execute(
            """
            INSERT INTO contracts (
                customer_id,
                salesperson_id,
                station_id,
                contract_number,
                description,
                start_date,
                end_date,
                status,
                active,
                payment_timing,
                payment_terms_days,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_a_id,
                salesperson_a_id,
                station_id,
                "UNSCHED-MIX-A",
                "Unschedule mixed avail regression A",
                "2026-10-05",
                "2026-10-06",
                "Active",
                1,
                "POSTPAID",
                30,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        contract_a_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO contracts (
                customer_id,
                salesperson_id,
                station_id,
                contract_number,
                description,
                start_date,
                end_date,
                status,
                active,
                payment_timing,
                payment_terms_days,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_b_id,
                salesperson_b_id,
                station_id,
                "UNSCHED-MIX-B",
                "Unschedule mixed avail regression B",
                "2026-10-05",
                "2026-10-06",
                "Active",
                1,
                "POSTPAID",
                30,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        contract_b_id = cursor.lastrowid

        #
        # ------------------------------------------------------
        # Contract items.
        # ------------------------------------------------------
        #

        cursor.execute(
            """
            INSERT INTO contract_items (
                contract_id,
                commercial_id,
                commercial_title,
                description,
                quantity,
                pricing_type,
                unit_price,
                spot_length_seconds,
                start_date,
                end_date,
                priority,
                active,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract_a_id,
                commercial_a_id,
                "Unschedule Mixed Test Commercial A",
                "Mixed avail regression CI A",
                4,
                "PER_SPOT",
                10000,
                30,
                "2026-10-05",
                "2026-10-06",
                1,
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        contract_item_a_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO contract_items (
                contract_id,
                commercial_id,
                commercial_title,
                description,
                quantity,
                pricing_type,
                unit_price,
                spot_length_seconds,
                start_date,
                end_date,
                priority,
                active,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract_b_id,
                commercial_b_id,
                "Unschedule Mixed Test Commercial B",
                "Mixed avail regression CI B",
                4,
                "PER_SPOT",
                10000,
                30,
                "2026-10-05",
                "2026-10-06",
                1,
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        contract_item_b_id = cursor.lastrowid

        #
        # ------------------------------------------------------
        # Contract item rules.
        #
        # The rules are fixture data here. The regression is
        # testing unscheduling, not scheduling.
        # ------------------------------------------------------
        #

        cursor.execute(
            """
            INSERT INTO contract_item_rules (
                contract_item_id,
                days_of_week,
                start_time,
                end_time,
                min_spots_per_day,
                max_spots_per_day,
                min_spots_per_week,
                max_spots_per_week,
                allow_news,
                allow_special_events,
                active,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract_item_a_id,
                "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
                "01:00:00",
                "04:00:00",
                None,
                4,
                None,
                4,
                1,
                1,
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        rule_a_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO contract_item_rules (
                contract_item_id,
                days_of_week,
                start_time,
                end_time,
                min_spots_per_day,
                max_spots_per_day,
                min_spots_per_week,
                max_spots_per_week,
                allow_news,
                allow_special_events,
                active,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract_item_b_id,
                "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
                "01:00:00",
                "04:00:00",
                None,
                4,
                None,
                4,
                1,
                1,
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )

        rule_b_id = cursor.lastrowid

        #
        # ------------------------------------------------------
        # Create test avails.
        #
        # Six avails:
        #
        #   A-only-1    A
        #   A-only-2    A
        #   B-only-1    B
        #   B-only-2    B
        #   Mixed-1     A + B
        #   Mixed-2     A + B
        #
        # This gives us exclusive and shared occupancy, with
        # exactly four spots belonging to each contract item.
        # ------------------------------------------------------
        #

        avail_definitions = [
            (
                "A-only-1",
                "2026-10-05",
                "01:00:00",
            ),
            (
                "A-only-2",
                "2026-10-05",
                "03:00:00",
            ),
            (
                "B-only-1",
                "2026-10-05",
                "02:00:00",
            ),
            (
                "B-only-2",
                "2026-10-05",
                "04:00:00",
            ),
            (
                "Mixed-1",
                "2026-10-06",
                "01:00:00",
            ),
            (
                "Mixed-2",
                "2026-10-06",
                "02:00:00",
            ),
        ]

        for label, air_date, start_time in avail_definitions:

            cursor.execute(
                """
                INSERT INTO avails (
                    station_id,
                    air_date,
                    start_time,
                    length_seconds,
                    status,
                    created_date,
                    modified_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    station_id,
                    air_date,
                    start_time,
                    60,
                    "Open",
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                )
            )

            avail_id = cursor.lastrowid

            avail_by_label[label] = avail_id
            test_avail_ids.append(avail_id)

        #
        # ------------------------------------------------------
        # Create spots.
        #
        # CI A = 4 spots:
        #
        #   A-only-1
        #   A-only-2
        #   Mixed-1
        #   Mixed-2
        #
        # CI B = 4 spots:
        #
        #   B-only-1
        #   B-only-2
        #   Mixed-1
        #   Mixed-2
        #
        # Therefore:
        #
        #   A-only-*  contain only A
        #   B-only-*  contain only B
        #   Mixed-*   contain exactly one A and one B
        #
        # ------------------------------------------------------
        #

        spot_definitions = [
            (
                contract_item_a_id,
                commercial_a_id,
                "A-only-1",
                "01:00:00",
            ),
            (
                contract_item_a_id,
                commercial_a_id,
                "A-only-2",
                "03:00:00",
            ),
            (
                contract_item_a_id,
                commercial_a_id,
                "Mixed-1",
                "01:00:00",
            ),
            (
                contract_item_a_id,
                commercial_a_id,
                "Mixed-2",
                "02:00:00",
            ),

            (
                contract_item_b_id,
                commercial_b_id,
                "B-only-1",
                "02:00:00",
            ),
            (
                contract_item_b_id,
                commercial_b_id,
                "B-only-2",
                "04:00:00",
            ),
            (
                contract_item_b_id,
                commercial_b_id,
                "Mixed-1",
                "01:00:00",
            ),
            (
                contract_item_b_id,
                commercial_b_id,
                "Mixed-2",
                "02:00:00",
            ),
        ]


        for (
            contract_item_id,
            commercial_id,
            label,
            air_time,
        ) in spot_definitions:

            avail_id = avail_by_label[label]

            cursor.execute(
                """
                SELECT air_date
                FROM avails
                WHERE id = ?
                """,
                (avail_id,)
            )

            air_date = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO spots (
                    station_id,
                    contract_item_id,
                    commercial_id,
                    avail_id,
                    air_date,
                    air_time,
                    status,
                    created_date,
                    modified_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    station_id,
                    contract_item_id,
                    commercial_id,
                    avail_id,
                    air_date,
                    air_time,
                    "Scheduled",
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                )
            )

            test_spot_ids.append(cursor.lastrowid)






        #
        # Recalculate all test avail statuses.
        #
        for avail_id in test_avail_ids:
            update_avail_status(
                avail_id,
                connection=connection
            )

        connection.commit()
        connection.close()
        connection = None

        #
        # ------------------------------------------------------
        # Verify initial spot counts.
        # ------------------------------------------------------
        #

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE contract_item_id = ?
            """,
            (contract_item_a_id,)
        )

        a_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE contract_item_id = ?
            """,
            (contract_item_b_id,)
        )

        b_count = cursor.fetchone()[0]

        test(
            "CI A has exactly four spots before deschedule",
            a_count == 4,
            f"found {a_count}"
        )

        test(
            "CI B has exactly four spots before deschedule",
            b_count == 4,
            f"found {b_count}"
        )

        #
        # ------------------------------------------------------
        # Verify initial avail statuses.
        # ------------------------------------------------------
        #

        expected_initial = {
            "A-only-1": "Partial",
            "A-only-2": "Partial",
            "B-only-1": "Partial",
            "B-only-2": "Partial",
            "Mixed-1": "Filled",
            "Mixed-2": "Filled",
        }

        for label, expected_status in expected_initial.items():

            avail_id = avail_by_label[label]

            cursor.execute(
                """
                SELECT status
                FROM avails
                WHERE id = ?
                """,
                (avail_id,)
            )

            actual_status = cursor.fetchone()[0]

            test(
                f"Initial status of {label} is {expected_status}",
                actual_status == expected_status,
                f"found {actual_status}"
            )

        connection.close()
        connection = None

        #
        # ----------------------------------------------------------
        # Deschedule CI A.
        # ----------------------------------------------------------
        #

        print()
        print("Descheduling Contract Item A...")
        print()

        result_a = unschedule_contract_item(
            contract_item_a_id
        )

        test(
            "Deschedule A succeeds",
            result_a.get("status") == "success",
            str(result_a)
        )

        #
        # ----------------------------------------------------------
        # Verify A is completely gone while B remains.
        # ----------------------------------------------------------
        #

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE contract_item_id = ?
            """,
            (contract_item_a_id,)
        )

        a_remaining = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE contract_item_id = ?
            """,
            (contract_item_b_id,)
        )

        b_remaining = cursor.fetchone()[0]

        test(
            "CI A has zero spots after deschedule",
            a_remaining == 0,
            f"found {a_remaining}"
        )

        test(
            "CI B still has four spots after A deschedule",
            b_remaining == 4,
            f"found {b_remaining}"
        )

        #
        # A-only becomes Open.
        #
        # B-only remains Filled.
        #
        # Mixed avails become Partial because the A spots were
        # removed while B spots remain.
        #

        expected_after_a = {
            "A-only-1": "Open",
            "A-only-2": "Open",
            "B-only-1": "Partial",
            "B-only-2": "Partial",
            "Mixed-1": "Partial",
            "Mixed-2": "Partial",
        }

        for label, expected_status in expected_after_a.items():

            avail_id = avail_by_label[label]

            cursor.execute(
                """
                SELECT status
                FROM avails
                WHERE id = ?
                """,
                (avail_id,)
            )

            actual_status = cursor.fetchone()[0]

            test(
                f"After A deschedule, {label} is {expected_status}",
                actual_status == expected_status,
                f"found {actual_status}"
            )

        #
        # ------------------------------------------------------
        # Verify every remaining B spot is still Scheduled and
        # still assigned to its original avail.
        # ------------------------------------------------------
        #

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE contract_item_id = ?
              AND status = 'Scheduled'
              AND avail_id IS NOT NULL
            """,
            (contract_item_b_id,)
        )

        b_scheduled_assigned = cursor.fetchone()[0]

        test(
            "All B spots remain Scheduled and assigned",
            b_scheduled_assigned == 4,
            f"found {b_scheduled_assigned}"
        )

        #
        # Verify the B spots are on the expected avails.
        #
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE contract_item_id = ?
              AND avail_id IN (?, ?, ?, ?)
            """,
            (
                contract_item_b_id,
                avail_by_label["B-only-1"],
                avail_by_label["B-only-2"],
                avail_by_label["Mixed-1"],
                avail_by_label["Mixed-2"],
            )
        )

        b_expected_avails = cursor.fetchone()[0]

        test(
            "All B spots remain on their original test avails",
            b_expected_avails == 4,
            f"found {b_expected_avails}"
        )

        connection.close()
        connection = None

        #
        # ----------------------------------------------------------
        # Deschedule CI B.
        # ----------------------------------------------------------
        #

        print()
        print("Descheduling Contract Item B...")
        print()

        result_b = unschedule_contract_item(
            contract_item_b_id
        )

        test(
            "Deschedule B succeeds",
            result_b.get("status") == "success",
            str(result_b)
        )

        #
        # ----------------------------------------------------------
        # Verify everything is gone.
        # ----------------------------------------------------------
        #

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE contract_item_id = ?
            """,
            (contract_item_a_id,)
        )

        a_final = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE contract_item_id = ?
            """,
            (contract_item_b_id,)
        )

        b_final = cursor.fetchone()[0]

        test(
            "CI A still has zero spots",
            a_final == 0,
            f"found {a_final}"
        )

        test(
            "CI B has zero spots after deschedule",
            b_final == 0,
            f"found {b_final}"
        )

        #
        # All test avails should now be Open.
        #
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM avails
            WHERE id IN ({})
              AND status = 'Open'
            """.format(
                ",".join("?" for _ in test_avail_ids)
            ),
            tuple(test_avail_ids)
        )

        open_count = cursor.fetchone()[0]

        test(
            "All test avails are Open after both deschedules",
            open_count == len(test_avail_ids),
            f"found {open_count}"
        )

        #
        # There should be no spots left on the test avails.
        #
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE avail_id IN ({})
            """.format(
                ",".join("?" for _ in test_avail_ids)
            ),
            tuple(test_avail_ids)
        )

        remaining_test_spots = cursor.fetchone()[0]

        test(
            "No spots remain on test avails",
            remaining_test_spots == 0,
            f"found {remaining_test_spots}"
        )

        connection.close()
        connection = None

    except Exception as exc:

        print()
        print(f"ERROR: {type(exc).__name__}: {exc}")
        failed += 1

    finally:

        #
        # ----------------------------------------------------------
        # Cleanup.
        # ----------------------------------------------------------
        #

        print()
        print("Cleaning up unschedule mixed-avail regression test data...")
        print()

        cleanup_connection = None

        try:

            cleanup_connection = get_connection()
            cleanup_cursor = cleanup_connection.cursor()

            #
            # Delete any remaining spots belonging to either CI.
            #
            if contract_item_a_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM spots
                    WHERE contract_item_id = ?
                    """,
                    (contract_item_a_id,)
                )

            if contract_item_b_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM spots
                    WHERE contract_item_id = ?
                    """,
                    (contract_item_b_id,)
                )

            #
            # Delete rules.
            #
            if rule_a_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM contract_item_rules
                    WHERE id = ?
                    """,
                    (rule_a_id,)
                )

            if rule_b_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM contract_item_rules
                    WHERE id = ?
                    """,
                    (rule_b_id,)
                )

            #
            # Delete contract items.
            #
            if contract_item_a_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM contract_items
                    WHERE id = ?
                    """,
                    (contract_item_a_id,)
                )

            if contract_item_b_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM contract_items
                    WHERE id = ?
                    """,
                    (contract_item_b_id,)
                )

            #
            # Delete contracts.
            #
            if contract_a_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM contracts
                    WHERE id = ?
                    """,
                    (contract_a_id,)
                )

            if contract_b_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM contracts
                    WHERE id = ?
                    """,
                    (contract_b_id,)
                )

            #
            # Delete commercials.
            #
            if commercial_a_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM commercials
                    WHERE id = ?
                    """,
                    (commercial_a_id,)
                )

            if commercial_b_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM commercials
                    WHERE id = ?
                    """,
                    (commercial_b_id,)
                )

            #
            # Delete test avails.
            #
            for avail_id in test_avail_ids:
                cleanup_cursor.execute(
                    """
                    DELETE FROM avails
                    WHERE id = ?
                    """,
                    (avail_id,)
                )

            #
            # Delete customers.
            #
            if customer_a_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM customers
                    WHERE id = ?
                    """,
                    (customer_a_id,)
                )

            if customer_b_id is not None:
                cleanup_cursor.execute(
                    """
                    DELETE FROM customers
                    WHERE id = ?
                    """,
                    (customer_b_id,)
                )

            cleanup_connection.commit()

            print("Cleanup complete.")

        except Exception as cleanup_exc:

            print(
                f"Cleanup ERROR: "
                f"{type(cleanup_exc).__name__}: {cleanup_exc}"
            )

            if cleanup_connection is not None:
                cleanup_connection.rollback()

        finally:

            if cleanup_connection is not None:
                cleanup_connection.close()

            if connection is not None:
                connection.close()

    #
    # ----------------------------------------------------------
    # Final result.
    # ----------------------------------------------------------
    #

    print()
    print("=" * 60)
    print(
        f"Mixed-avail unschedule regression tests: "
        f"{passed} passed, {failed} failed"
    )
    print("=" * 60)

    if failed == 0:
        print()
        print("ALL MIXED-AVAIL UNSCHEDULE REGRESSION TESTS PASSED")
        return 0

    print()
    print("MIXED-AVAIL UNSCHEDULE REGRESSION TESTS FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
