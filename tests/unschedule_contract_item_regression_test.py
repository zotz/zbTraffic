#!/usr/bin/env python3

#
# File: tests/unschedule_contract_item_regression_test.py
#
# Contract-item deschedule regression test.
#
# This test creates two isolated customer/commercial/contract/
# contract-item/rule sets, creates avails and scheduled spots,
# exercises unschedule_contract_item(), and removes everything
# it created when finished.
#
# Run from the project root:
#
#     python3 tests/unschedule_contract_item_regression_test.py
#

import os
import sys


#
# Make the project root importable when this script is run as:
#
#     python3 tests/unschedule_contract_item_regression_test.py
#

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from traffic.database import get_connection
from traffic.spots import unschedule_contract_item


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

    global passed
    global failed

    #
    # IDs for everything created by this test.
    #
    # These are kept so cleanup can be precise.
    #

    customer_a_id = None
    customer_b_id = None

    salesperson_a_id = None
    salesperson_b_id = None

    station_id = None

    contract_a_id = None
    contract_b_id = None

    contract_item_a_id = None
    contract_item_b_id = None

    commercial_a_id = None
    commercial_b_id = None

    rule_a_id = None
    rule_b_id = None

    avail_ids = []
    spot_ids = []

    connection = None

    print()
    print("=" * 60)
    print("Contract Item Unschedule Regression Test")
    print("=" * 60)
    print()

    try:

        #
        # ----------------------------------------------------------
        # Create isolated test data.
        # ----------------------------------------------------------
        #

        connection = get_connection()
        cursor = connection.cursor()

        #
        # Find the default station.
        #
        # We deliberately use an existing station rather than
        # creating a test station.
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
            raise RuntimeError(
                "No active station exists for the regression test."
            )

        station_id = station["id"]

        #
        # ----------------------------------------------------------
        # Customer A.
        # ----------------------------------------------------------
        #

        cursor.execute(
            """
            INSERT INTO customers (
                company_name,
                active
            )
            VALUES (?, 1)
            """,
            (
                "ZZTEST Unschedule Customer A",
            )
        )

        customer_a_id = cursor.lastrowid

        #
        # Customer B.
        #

        cursor.execute(
            """
            INSERT INTO customers (
                company_name,
                active
            )
            VALUES (?, 1)
            """,
            (
                "ZZTEST Unschedule Customer B",
            )
        )

        customer_b_id = cursor.lastrowid

        #
        # ----------------------------------------------------------
        # Salespeople.
        #
        # Contracts require a salesperson, so create isolated test
        # salespeople rather than using real data.
        # ----------------------------------------------------------
        #

        cursor.execute(
            """
            INSERT INTO salespeople (
                first_name,
                last_name,
                active
            )
            VALUES (?, ?, 1)
            """,
            (
                "ZZTEST",
                "Unschedule A",
            )
        )

        salesperson_a_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO salespeople (
                first_name,
                last_name,
                active
            )
            VALUES (?, ?, 1)
            """,
            (
                "ZZTEST",
                "Unschedule B",
            )
        )

        salesperson_b_id = cursor.lastrowid

        #
        # ----------------------------------------------------------
        # Commercial A.
        # ----------------------------------------------------------
        #

        cursor.execute(
            """
            INSERT INTO commercials (
                customer_id,
                title,
                length_seconds,
                active
            )
            VALUES (?, ?, ?, 1)
            """,
            (
                customer_a_id,
                "ZZTEST Unschedule Commercial A",
                30,
            )
        )

        commercial_a_id = cursor.lastrowid

        #
        # Commercial B.
        #

        cursor.execute(
            """
            INSERT INTO commercials (
                customer_id,
                title,
                length_seconds,
                active
            )
            VALUES (?, ?, ?, 1)
            """,
            (
                customer_b_id,
                "ZZTEST Unschedule Commercial B",
                30,
            )
        )

        commercial_b_id = cursor.lastrowid

        #
        # ----------------------------------------------------------
        # Contract A.
        # ----------------------------------------------------------
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
                payment_terms_days
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                customer_a_id,
                salesperson_a_id,
                station_id,
                "ZZTEST-UNSCHEDULE-A",
                "Unschedule Regression Test Contract A",
                "2026-10-05",
                "2026-10-07",
                "Active",
                "POSTPAID",
                30,
            )
        )

        contract_a_id = cursor.lastrowid

        #
        # Contract B.
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
                payment_terms_days
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                customer_b_id,
                salesperson_b_id,
                station_id,
                "ZZTEST-UNSCHEDULE-B",
                "Unschedule Regression Test Contract B",
                "2026-10-05",
                "2026-10-07",
                "Active",
                "POSTPAID",
                30,
            )
        )

        contract_b_id = cursor.lastrowid

        #
        # ----------------------------------------------------------
        # Contract Item A.
        # ----------------------------------------------------------
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
                total_price,
                spot_length_seconds,
                start_date,
                end_date,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                contract_a_id,
                commercial_a_id,
                "ZZTEST Unschedule Commercial A",
                "ZZTEST Unschedule Item A",
                6,
                "PER_SPOT",
                30000,
                180000,
                30,
                "2026-10-05",
                "2026-10-07",
            )
        )

        contract_item_a_id = cursor.lastrowid

        #
        # Contract Item B.
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
                total_price,
                spot_length_seconds,
                start_date,
                end_date,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                contract_b_id,
                commercial_b_id,
                "ZZTEST Unschedule Commercial B",
                "ZZTEST Unschedule Item B",
                6,
                "PER_SPOT",
                30000,
                180000,
                30,
                "2026-10-05",
                "2026-10-07",
            )
        )

        contract_item_b_id = cursor.lastrowid

        #
        # ----------------------------------------------------------
        # Contract Item Rules.
        #
        # Both rules have the same eligible days and time window.
        #

        cursor.execute(
            """
            INSERT INTO contract_item_rules (
                contract_item_id,
                days_of_week,
                start_time,
                end_time,
                max_spots_per_day,
                max_spots_per_week,
                allow_news,
                allow_special_events,
                active,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, 1, 1, ?)
            """,
            (
                contract_item_a_id,
                "Mon,Tue,Wed",
                "01:00:00",
                "04:00:00",
                6,
                6,
                "ZZTEST Unschedule Rule A",
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
                max_spots_per_day,
                max_spots_per_week,
                allow_news,
                allow_special_events,
                active,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, 1, 1, ?)
            """,
            (
                contract_item_b_id,
                "Mon,Tue,Wed",
                "01:00:00",
                "04:00:00",
                6,
                6,
                "ZZTEST Unschedule Rule B",
            )
        )

        rule_b_id = cursor.lastrowid

        #
        # ----------------------------------------------------------
        # Create test avails.
        #
        # We deliberately create three different types:
        #
        #   A-only
        #   B-only
        #   A+B shared
        #
        # All are 60-second avails, while each commercial is 30
        # seconds. Therefore:
        #
        #   one spot  = Partial
        #   two spots = Filled
        #
        # This makes the state changes easy to verify.
        # ----------------------------------------------------------

        avail_data = [
            # id label, date, time
            ("A-only-1", "2026-10-05", "01:00:00"),
            ("A-only-2", "2026-10-05", "02:00:00"),

            ("B-only-1", "2026-10-05", "01:30:00"),
            ("B-only-2", "2026-10-05", "02:30:00"),

            ("Shared-1", "2026-10-06", "01:00:00"),
            ("Shared-2", "2026-10-06", "02:00:00"),
        ]

        avail_by_label = {}

        for label, air_date, start_time in avail_data:

            cursor.execute(
                """
                INSERT INTO avails (
                    station_id,
                    air_date,
                    start_time,
                    length_seconds,
                    status
                )
                VALUES (?, ?, ?, ?, 'Open')
                """,
                (
                    station_id,
                    air_date,
                    start_time,
                    60,
                )
            )

            avail_id = cursor.lastrowid

            avail_ids.append(avail_id)
            avail_by_label[label] = avail_id

        #
        # ----------------------------------------------------------
        # Create scheduled spots.
        #
        # A:
        #   A-only-1
        #   A-only-2
        #   Shared-1
        #   Shared-2
        #   plus two additional A-only spots
        #
        # B:
        #   B-only-1
        #   B-only-2
        #   Shared-1
        #   Shared-2
        #   plus two additional B-only spots
        #
        # This gives each CI exactly six spots.
        # ----------------------------------------------------------
        #

        spot_data = [
            #
            # A spots
            #
            (
                contract_item_a_id,
                commercial_a_id,
                avail_by_label["A-only-1"],
                "2026-10-05",
                "01:00:00",
            ),
            (
                contract_item_a_id,
                commercial_a_id,
                avail_by_label["A-only-2"],
                "2026-10-05",
                "02:00:00",
            ),
            (
                contract_item_a_id,
                commercial_a_id,
                avail_by_label["Shared-1"],
                "2026-10-06",
                "01:00:00",
            ),
            (
                contract_item_a_id,
                commercial_a_id,
                avail_by_label["Shared-2"],
                "2026-10-06",
                "02:00:00",
            ),
            (
                contract_item_a_id,
                commercial_a_id,
                avail_by_label["A-only-1"],
                "2026-10-05",
                "01:00:00",
            ),
            (
                contract_item_a_id,
                commercial_a_id,
                avail_by_label["A-only-2"],
                "2026-10-05",
                "02:00:00",
            ),

            #
            # B spots
            #
            (
                contract_item_b_id,
                commercial_b_id,
                avail_by_label["B-only-1"],
                "2026-10-05",
                "01:30:00",
            ),
            (
                contract_item_b_id,
                commercial_b_id,
                avail_by_label["B-only-2"],
                "2026-10-05",
                "02:30:00",
            ),
            (
                contract_item_b_id,
                commercial_b_id,
                avail_by_label["Shared-1"],
                "2026-10-06",
                "01:00:00",
            ),
            (
                contract_item_b_id,
                commercial_b_id,
                avail_by_label["Shared-2"],
                "2026-10-06",
                "02:00:00",
            ),
            (
                contract_item_b_id,
                commercial_b_id,
                avail_by_label["B-only-1"],
                "2026-10-05",
                "01:30:00",
            ),
            (
                contract_item_b_id,
                commercial_b_id,
                avail_by_label["B-only-2"],
                "2026-10-05",
                "02:30:00",
            ),
        ]

        for (
            item_id,
            commercial_id,
            avail_id,
            air_date,
            air_time,
        ) in spot_data:

            cursor.execute(
                """
                INSERT INTO spots (
                    station_id,
                    contract_item_id,
                    commercial_id,
                    avail_id,
                    air_date,
                    air_time,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'Scheduled')
                """,
                (
                    station_id,
                    item_id,
                    commercial_id,
                    avail_id,
                    air_date,
                    air_time,
                )
            )

            spot_ids.append(cursor.lastrowid)

        #
        # Recalculate all test avail statuses using the same
        # application logic used by scheduling/unscheduling.
        #

        from traffic.avails import update_avail_status

        for avail_id in avail_ids:
            update_avail_status(
                avail_id,
                connection=connection
            )

        connection.commit()
        connection.close()
        connection = None

        #
        # ----------------------------------------------------------
        # Initial state checks.
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
            "CI A has exactly six spots before deschedule",
            a_count == 6,
            f"found {a_count}"
        )

        test(
            "CI B has exactly six spots before deschedule",
            b_count == 6,
            f"found {b_count}"
        )

        #
        # Check the initial avail states.
        #

        expected_initial = {
            "A-only-1": "Filled",
            "A-only-2": "Filled",
            "B-only-1": "Filled",
            "B-only-2": "Filled",
            "Shared-1": "Filled",
            "Shared-2": "Filled",
        }

        #
        # Because we deliberately put two A spots in each A-only
        # avail and two B spots in each B-only avail, those avails
        # are Filled. Shared avails also contain two 30-second spots.
        #

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
            "CI B still has six spots after A deschedule",
            b_remaining == 6,
            f"found {b_remaining}"
        )

        # A-only avails should now be Open because all A spots
        # occupying them were removed.
        #
        # Shared avails should be Partial because their A spot
        # was removed but B remains.
        #
        # B-only avails should remain Filled.

        expected_after_a = {
            "A-only-1": "Open",
            "A-only-2": "Open",
            "B-only-1": "Filled",
            "B-only-2": "Filled",
            "Shared-1": "Partial",
            "Shared-2": "Partial",
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
        # Verify B's spots are still correctly assigned.
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

        b_scheduled = cursor.fetchone()[0]

        test(
            "All B spots remain Scheduled and assigned",
            b_scheduled == 6,
            f"found {b_scheduled}"
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
        # Final verification.
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
        # Every test avail should now be Open.
        #

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM avails
            WHERE id IN ({})
            AND status != 'Open'
            """.format(
                ",".join(["?"] * len(avail_ids))
            ),
            avail_ids,
        )

        non_open_count = cursor.fetchone()[0]

        test(
            "All test avails are Open after both deschedules",
            non_open_count == 0,
            f"found {non_open_count} non-open avails"
        )

        #
        # Verify no test spots remain assigned to the test avails.
        #

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM spots
            WHERE avail_id IN ({})
            """.format(
                ",".join(["?"] * len(avail_ids))
            ),
            avail_ids,
        )

        remaining_avail_spots = cursor.fetchone()[0]

        test(
            "No spots remain on test avails",
            remaining_avail_spots == 0,
            f"found {remaining_avail_spots}"
        )

        connection.close()
        connection = None

    except Exception as exc:

        print()
        print(
            "ERROR: Unschedule regression test raised an exception."
        )
        print(
            f"       {type(exc).__name__}: {exc}"
        )

        failed += 1

    finally:

        #
        # ----------------------------------------------------------
        # Cleanup.
        # ----------------------------------------------------------
        #

        print()
        print(
            "Cleaning up unschedule regression test data..."
        )

        try:

            if connection is None:
                connection = get_connection()

            cursor = connection.cursor()

            #
            # Delete spots first.
            #

            if spot_ids:

                placeholders = ",".join(
                    ["?"] * len(spot_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM spots
                    WHERE id IN ({placeholders})
                    """,
                    spot_ids,
                )

            #
            # Delete any remaining spots belonging to the test
            # contract items as an additional safety measure.
            #

            contract_item_ids = []

            if contract_item_a_id is not None:
                contract_item_ids.append(
                    contract_item_a_id
                )

            if contract_item_b_id is not None:
                contract_item_ids.append(
                    contract_item_b_id
                )

            if contract_item_ids:

                placeholders = ",".join(
                    ["?"] * len(contract_item_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM spots
                    WHERE contract_item_id IN ({placeholders})
                    """,
                    contract_item_ids,
                )

            #
            # Delete contract item rules.
            #

            rule_ids = []

            if rule_a_id is not None:
                rule_ids.append(rule_a_id)

            if rule_b_id is not None:
                rule_ids.append(rule_b_id)

            if rule_ids:

                placeholders = ",".join(
                    ["?"] * len(rule_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM contract_item_rules
                    WHERE id IN ({placeholders})
                    """,
                    rule_ids,
                )

            #
            # Delete contract items.
            #

            if contract_item_ids:

                placeholders = ",".join(
                    ["?"] * len(contract_item_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM contract_items
                    WHERE id IN ({placeholders})
                    """,
                    contract_item_ids,
                )

            #
            # Delete contracts.
            #

            contract_ids = []

            if contract_a_id is not None:
                contract_ids.append(contract_a_id)

            if contract_b_id is not None:
                contract_ids.append(contract_b_id)

            if contract_ids:

                placeholders = ",".join(
                    ["?"] * len(contract_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM contracts
                    WHERE id IN ({placeholders})
                    """,
                    contract_ids,
                )

            #
            # Delete commercials.
            #

            commercial_ids = []

            if commercial_a_id is not None:
                commercial_ids.append(commercial_a_id)

            if commercial_b_id is not None:
                commercial_ids.append(commercial_b_id)

            if commercial_ids:

                placeholders = ",".join(
                    ["?"] * len(commercial_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM commercials
                    WHERE id IN ({placeholders})
                    """,
                    commercial_ids,
                )

            #
            # Delete test avails.
            #

            if avail_ids:

                placeholders = ",".join(
                    ["?"] * len(avail_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM avails
                    WHERE id IN ({placeholders})
                    """,
                    avail_ids,
                )

            #
            # Delete salespeople.
            #

            salesperson_ids = []

            if salesperson_a_id is not None:
                salesperson_ids.append(salesperson_a_id)

            if salesperson_b_id is not None:
                salesperson_ids.append(salesperson_b_id)

            if salesperson_ids:

                placeholders = ",".join(
                    ["?"] * len(salesperson_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM salespeople
                    WHERE id IN ({placeholders})
                    """,
                    salesperson_ids,
                )

            #
            # Delete customers.
            #

            customer_ids = []

            if customer_a_id is not None:
                customer_ids.append(customer_a_id)

            if customer_b_id is not None:
                customer_ids.append(customer_b_id)

            if customer_ids:

                placeholders = ",".join(
                    ["?"] * len(customer_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM customers
                    WHERE id IN ({placeholders})
                    """,
                    customer_ids,
                )

            connection.commit()

            print("Cleanup complete.")

        except Exception as exc:

            print(
                "WARNING: Cleanup failed:"
            )
            print(
                f"         {type(exc).__name__}: {exc}"
            )

            failed += 1

        finally:

            if connection is not None:
                connection.close()


    #
    # --------------------------------------------------------------
    # Final result.
    # --------------------------------------------------------------
    #

    print()
    print("=" * 60)
    print(
        f"Unschedule regression tests: "
        f"{passed} passed, {failed} failed"
    )
    print("=" * 60)
    print()

    if failed == 0:
        print(
            "ALL UNSCHEDULE REGRESSION TESTS PASSED"
        )
        return 0

    print(
        "UNSCHEDULE REGRESSION TESTS FAILED"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
