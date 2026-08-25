#!/usr/bin/env python3

#
# File: tests/billing_regression_test.py
#
# Billing regression test.
#
# This test creates its own temporary billing data, exercises the
# billing module, and removes everything it created when finished.
#
# Run from the project root:
#
#     python3 tests/billing_regression_test.py
#

import os
import sys
import sqlite3


#
# Make the project root importable when this script is run as:
#
#     python3 tests/billing_regression_test.py
#

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from traffic.database import get_connection
from traffic.billing import (
    create_invoice,
    get_invoice,
    list_invoices,
    update_invoice,
    add_invoice_item,
    get_invoice_item,
    list_invoice_items,
    update_invoice_item,
    recalculate_invoice_totals,
    get_unbilled_completed_spots,
    attach_spot_to_invoice_item,
    attach_spots_to_invoice_item,
    list_invoice_item_spots,
    deactivate_invoice_item_spot,
    create_postpaid_invoice,
)


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

    #
    # IDs for everything created by this test.
    #
    # These are kept so the cleanup can be precise.
    #

    global passed
    global failed

    customer_id = None
    salesperson_id = None
    station_id = None
    contract_id = None
    contract_item_id = None
    postpaid_contract_item_id = None

    spot_ids = []

    invoice_ids = []
    invoice_item_ids = []
    invoice_item_spot_ids = []

    connection = None

    print()
    print("=" * 60)
    print("Billing Regression Test")
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
        # Create a test customer.
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
                "ZZTEST Billing Customer",
            )
        )

        customer_id = cursor.lastrowid

        #
        # Create a test salesperson.
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
                "Billing",
            )
        )

        salesperson_id = cursor.lastrowid

        #
        # Create a test station.
        #

        cursor.execute(
            """
            INSERT INTO stations (
                name,
                call_letters,
                active
            )
            VALUES (?, ?, 1)
            """,
            (
                "ZZTEST Billing Station",
                "ZZTB",
            )
        )

        station_id = cursor.lastrowid

        #
        # Create a test contract.
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
                customer_id,
                salesperson_id,
                station_id,
                "ZZTEST-BILLING-001",
                "Billing Regression Test Contract",
                "2026-08-01",
                "2026-08-31",
                "Active",
                "POSTPAID",
                30,
            )
        )

        contract_id = cursor.lastrowid

        #
        # Create the first contract item.
        #
        # This item is used for the individual billing function tests.
        #

        cursor.execute(
            """
            INSERT INTO contract_items (
                contract_id,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                contract_id,
                "ZZTEST Billing Commercial",
                "ZZTEST Billing Item",
                10,
                "PER_SPOT",
                2500,
                25000,
                30,
                "2026-08-01",
                "2026-08-31",
            )
        )

        contract_item_id = cursor.lastrowid

        #
        # Create a second contract item.
        #
        # This one is reserved for create_postpaid_invoice().
        #

        cursor.execute(
            """
            INSERT INTO contract_items (
                contract_id,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                contract_id,
                "ZZTEST Postpaid Commercial",
                "ZZTEST Postpaid Billing Item",
                5,
                "TOTAL",
                None,
                15000,
                30,
                "2026-08-01",
                "2026-08-31",
            )
        )

        postpaid_contract_item_id = cursor.lastrowid

        #
        # Create six Completed spots.
        #
        # Three belong to the first contract item.
        # Three belong to the postpaid contract item.
        #

        spot_data = [
            (
                contract_item_id,
                "2026-08-20",
                "10:00:00",
            ),
            (
                contract_item_id,
                "2026-08-21",
                "11:00:00",
            ),
            (
                contract_item_id,
                "2026-08-22",
                "12:00:00",
            ),
            (
                postpaid_contract_item_id,
                "2026-08-23",
                "13:00:00",
            ),
            (
                postpaid_contract_item_id,
                "2026-08-24",
                "14:00:00",
            ),
            (
                postpaid_contract_item_id,
                "2026-08-25",
                "15:00:00",
            ),
        ]

        for item_id, air_date, air_time in spot_data:

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
                VALUES (?, ?, NULL, NULL, ?, ?, 'Completed')
                """,
                (
                    station_id,
                    item_id,
                    air_date,
                    air_time,
                )
            )

            spot_ids.append(cursor.lastrowid)

        #
        # Also create one non-completed spot for the first contract item.
        #
        # It must NOT be returned by get_unbilled_completed_spots().
        #

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
            VALUES (?, ?, NULL, NULL, ?, ?, 'Scheduled')
            """,
            (
                station_id,
                contract_item_id,
                "2026-08-26",
                "16:00:00",
            )
        )

        scheduled_spot_id = cursor.lastrowid
        spot_ids.append(scheduled_spot_id)

        connection.commit()
        connection.close()
        connection = None

        print(
            f"Test customer: {customer_id}"
        )
        print(
            f"Test contract: {contract_id}"
        )
        print(
            f"Test contract item: {contract_item_id}"
        )
        print(
            f"Postpaid contract item: {postpaid_contract_item_id}"
        )
        print(
            f"Test spots created: {len(spot_ids)}"
        )
        print()


        #
        # ----------------------------------------------------------
        # Invoice header tests.
        # ----------------------------------------------------------
        #

        invoice_id = create_invoice(
            customer_id=customer_id,
            invoice_number="ZZTEST-INV-001",
            invoice_date="2026-08-25",
            due_date="2026-09-24",
            contract_id=contract_id,
            status="Draft",
            notes="Billing regression test",
        )

        invoice_ids.append(invoice_id)

        test(
            "create_invoice returns an id",
            invoice_id is not None,
            f"invoice_id={invoice_id}"
        )

        invoice = get_invoice(invoice_id)

        test(
            "get_invoice returns the invoice",
            invoice is not None,
        )

        test(
            "New invoice starts as Draft",
            invoice is not None
            and invoice["status"] == "Draft",
            f"status={invoice['status'] if invoice else None}"
        )

        test(
            "New invoice starts with zero subtotal",
            invoice is not None
            and invoice["subtotal"] == 0,
            f"subtotal={invoice['subtotal'] if invoice else None}"
        )

        test(
            "New invoice starts with zero tax",
            invoice is not None
            and invoice["tax"] == 0,
            f"tax={invoice['tax'] if invoice else None}"
        )

        test(
            "New invoice starts with zero total",
            invoice is not None
            and invoice["total"] == 0,
            f"total={invoice['total'] if invoice else None}"
        )


        #
        # list_invoices()
        #

        invoices = list_invoices(
            customer_id=customer_id
        )

        test(
            "list_invoices finds test invoice by customer",
            any(row["id"] == invoice_id for row in invoices),
            f"found={len(invoices)}"
        )

        invoices = list_invoices(
            contract_id=contract_id
        )

        test(
            "list_invoices finds test invoice by contract",
            any(row["id"] == invoice_id for row in invoices),
            f"found={len(invoices)}"
        )

        invoices = list_invoices(
            status="Draft"
        )

        test(
            "list_invoices supports status filter",
            any(row["id"] == invoice_id for row in invoices),
            f"found={len(invoices)}"
        )


        #
        # update_invoice()
        #

        changed = update_invoice(
            invoice_id,
            due_date="2026-10-01",
            status="Issued",
            notes="Updated billing regression test",
        )

        test(
            "update_invoice changes invoice",
            changed is True,
        )

        invoice = get_invoice(invoice_id)

        test(
            "Updated invoice has new due date",
            invoice is not None
            and invoice["due_date"] == "2026-10-01",
            f"due_date={invoice['due_date'] if invoice else None}"
        )

        test(
            "Updated invoice has new status",
            invoice is not None
            and invoice["status"] == "Issued",
            f"status={invoice['status'] if invoice else None}"
        )

        #
        # Put it back to Draft because subsequent tests expect a
        # normal working invoice.
        #

        update_invoice(
            invoice_id,
            status="Draft",
        )


        #
        # No-op update.
        #

        changed = update_invoice(
            invoice_id
        )

        test(
            "update_invoice with no fields returns False",
            changed is False,
        )


        #
        # ----------------------------------------------------------
        # Invoice item tests.
        # ----------------------------------------------------------
        #

        invoice_item_id = add_invoice_item(
            invoice_id=invoice_id,
            contract_item_id=contract_item_id,
            description="ZZTEST Item One",
            quantity=3,
            unit_price=2500,
        )

        invoice_item_ids.append(invoice_item_id)

        test(
            "add_invoice_item returns an id",
            invoice_item_id is not None,
            f"invoice_item_id={invoice_item_id}"
        )

        item = get_invoice_item(invoice_item_id)

        test(
            "get_invoice_item returns the item",
            item is not None,
        )

        test(
            "Invoice item quantity is correct",
            item is not None
            and item["quantity"] == 3,
            f"quantity={item['quantity'] if item else None}"
        )

        test(
            "Invoice item unit price is correct",
            item is not None
            and item["unit_price"] == 2500,
            f"unit_price={item['unit_price'] if item else None}"
        )

        test(
            "Invoice item amount is calculated",
            item is not None
            and item["amount"] == 7500,
            f"amount={item['amount'] if item else None}"
        )


        #
        # Second invoice item with an explicit amount.
        #

        invoice_item_2_id = add_invoice_item(
            invoice_id=invoice_id,
            contract_item_id=contract_item_id,
            description="ZZTEST Item Two",
            quantity=2,
            unit_price=4000,
            amount=10000,
        )

        invoice_item_ids.append(invoice_item_2_id)

        item_2 = get_invoice_item(invoice_item_2_id)

        test(
            "Explicit invoice item amount is preserved",
            item_2 is not None
            and item_2["amount"] == 10000,
            f"amount={item_2['amount'] if item_2 else None}"
        )


        #
        # list_invoice_items()
        #

        items = list_invoice_items(invoice_id)

        test(
            "list_invoice_items returns both items",
            len(items) == 2,
            f"count={len(items)}"
        )


        #
        # update_invoice_item()
        #

        changed = update_invoice_item(
            invoice_item_id,
            quantity=4,
            unit_price=3000,
        )

        test(
            "update_invoice_item changes item",
            changed is True,
        )

        item = get_invoice_item(invoice_item_id)

        test(
            "Updated item recalculates amount",
            item is not None
            and item["amount"] == 12000,
            f"amount={item['amount'] if item else None}"
        )


        #
        # Explicit amount override.
        #

        changed = update_invoice_item(
            invoice_item_id,
            amount=12500,
        )

        test(
            "update_invoice_item accepts explicit amount",
            changed is True,
        )

        item = get_invoice_item(invoice_item_id)

        test(
            "Explicit updated amount is preserved",
            item is not None
            and item["amount"] == 12500,
            f"amount={item['amount'] if item else None}"
        )


        #
        # No-op update.
        #

        changed = update_invoice_item(
            invoice_item_id
        )

        test(
            "update_invoice_item with no fields returns False",
            changed is False,
        )


        #
        # ----------------------------------------------------------
        # Invoice totals.
        # ----------------------------------------------------------
        #

        subtotal, tax, total = recalculate_invoice_totals(
            invoice_id,
            tax=1250,
        )

        test(
            "Invoice subtotal is calculated",
            subtotal == 22500,
            f"subtotal={subtotal}"
        )

        test(
            "Invoice tax is applied",
            tax == 1250,
            f"tax={tax}"
        )

        test(
            "Invoice total is subtotal plus tax",
            total == 23750,
            f"total={total}"
        )

        invoice = get_invoice(invoice_id)

        test(
            "Stored invoice subtotal is correct",
            invoice is not None
            and invoice["subtotal"] == 22500,
            f"subtotal={invoice['subtotal'] if invoice else None}"
        )

        test(
            "Stored invoice total is correct",
            invoice is not None
            and invoice["total"] == 23750,
            f"total={invoice['total'] if invoice else None}"
        )


        #
        # ----------------------------------------------------------
        # Completed spot discovery.
        # ----------------------------------------------------------
        #

        unbilled = get_unbilled_completed_spots(
            contract_item_id
        )

        test(
            "Completed unbilled spots are found",
            len(unbilled) == 3,
            f"count={len(unbilled)}"
        )

        unbilled_ids = [
            spot["id"]
            for spot in unbilled
        ]

        test(
            "All three completed spots are initially unbilled",
            set(unbilled_ids)
            == set(spot_ids[:3]),
            f"ids={unbilled_ids}"
        )

        #
        # The Scheduled spot must not appear.
        #

        test(
            "Scheduled spot is not billable",
            scheduled_spot_id not in unbilled_ids,
            f"scheduled_spot_id={scheduled_spot_id}"
        )


        #
        # ----------------------------------------------------------
        # Attach one spot.
        # ----------------------------------------------------------
        #

        association_id = attach_spot_to_invoice_item(
            invoice_item_id,
            spot_ids[0],
        )

        invoice_item_spot_ids.append(association_id)

        test(
            "attach_spot_to_invoice_item returns an id",
            association_id is not None,
            f"association_id={association_id}"
        )

        unbilled = get_unbilled_completed_spots(
            contract_item_id
        )

        test(
            "Attached spot is no longer unbilled",
            len(unbilled) == 2,
            f"count={len(unbilled)}"
        )


        #
        # ----------------------------------------------------------
        # Attach the remaining two spots in one operation.
        # ----------------------------------------------------------
        #

        count = attach_spots_to_invoice_item(
            invoice_item_id,
            [
                spot_ids[1],
                spot_ids[2],
            ],
        )

        test(
            "attach_spots_to_invoice_item attaches two spots",
            count == 2,
            f"count={count}"
        )

        #
        # Find their association IDs for later cleanup/testing.
        #

        associated = list_invoice_item_spots(
            invoice_item_id
        )

        for row in associated:
            if row["id"] not in invoice_item_spot_ids:
                invoice_item_spot_ids.append(row["id"])

        test(
            "Invoice item has three associated spots",
            len(associated) == 3,
            f"count={len(associated)}"
        )

        test(
            "All three associated spots are Completed",
            all(
                row["status"] == "Completed"
                for row in associated
            ),
        )


        #
        # No completed spots from the first contract item should
        # remain unbilled.
        #

        unbilled = get_unbilled_completed_spots(
            contract_item_id
        )

        test(
            "All first contract-item spots are now billed",
            len(unbilled) == 0,
            f"count={len(unbilled)}"
        )


        #
        # ----------------------------------------------------------
        # Deactivate one billing association.
        # ----------------------------------------------------------
        #

        changed = deactivate_invoice_item_spot(
            invoice_item_spot_ids[0]
        )

        test(
            "deactivate_invoice_item_spot succeeds",
            changed is True,
        )

        #
        # The spot itself must remain Completed.
        #

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                status
            FROM spots
            WHERE id = ?
            """,
            (
                spot_ids[0],
            )
        )

        spot = cursor.fetchone()

        connection.close()
        connection = None

        test(
            "Deactivating billing does not change spot status",
            spot is not None
            and spot["status"] == "Completed",
            f"status={spot['status'] if spot else None}"
        )

        #
        # It should become billable again.
        #

        unbilled = get_unbilled_completed_spots(
            contract_item_id
        )

        test(
            "Deactivated billing association makes spot billable again",
            len(unbilled) == 1
            and unbilled[0]["id"] == spot_ids[0],
            f"ids={[spot['id'] for spot in unbilled]}"
        )


        #
        # ----------------------------------------------------------
        # create_postpaid_invoice()
        # ----------------------------------------------------------
        #
        # First re-bill the previously deactivated spot so that the
        # first contract item is completely consumed.
        #

        replacement_invoice_item_id = add_invoice_item(
            invoice_id=invoice_id,
            contract_item_id=contract_item_id,
            description="ZZTEST Replacement Billing Item",
            quantity=1,
            amount=2500,
        )

        invoice_item_ids.append(
            replacement_invoice_item_id
        )

        replacement_association_id = attach_spot_to_invoice_item(
            replacement_invoice_item_id,
            spot_ids[0],
        )

        invoice_item_spot_ids.append(
            replacement_association_id
        )

        #
        # There should now be no unbilled spots on the first item.
        #

        unbilled = get_unbilled_completed_spots(
            contract_item_id
        )

        test(
            "First contract item has no remaining billable spots",
            len(unbilled) == 0,
            f"count={len(unbilled)}"
        )


        #
        # The second contract item has three completed spots and
        # none have been billed.
        #

        unbilled = get_unbilled_completed_spots(
            postpaid_contract_item_id
        )

        test(
            "Second contract item has three unbilled spots",
            len(unbilled) == 3,
            f"count={len(unbilled)}"
        )


        #
        # Create the postpaid invoice.
        #

        postpaid_invoice_id = create_postpaid_invoice(
            customer_id=customer_id,
            contract_id=contract_id,
            invoice_number="ZZTEST-POSTPAID-001",
            invoice_date="2026-08-25",
            due_date="2026-09-24",
            notes="ZZTEST postpaid invoice",
            tax=1500,
        )

        if postpaid_invoice_id is not None:
            invoice_ids.append(postpaid_invoice_id)

        test(
            "create_postpaid_invoice creates an invoice",
            postpaid_invoice_id is not None,
            f"invoice_id={postpaid_invoice_id}"
        )


        #
        # Inspect the generated invoice.
        #

        postpaid_invoice = None

        if postpaid_invoice_id is not None:
            postpaid_invoice = get_invoice(
                postpaid_invoice_id
            )

        test(
            "Postpaid invoice is Draft",
            postpaid_invoice is not None
            and postpaid_invoice["status"] == "Draft",
            (
                f"status="
                f"{postpaid_invoice['status'] if postpaid_invoice else None}"
            )
        )

        test(
            "Postpaid invoice has correct customer",
            postpaid_invoice is not None
            and postpaid_invoice["customer_id"] == customer_id,
            (
                f"customer_id="
                f"{postpaid_invoice['customer_id'] if postpaid_invoice else None}"
            )
        )

        test(
            "Postpaid invoice has correct contract",
            postpaid_invoice is not None
            and postpaid_invoice["contract_id"] == contract_id,
            (
                f"contract_id="
                f"{postpaid_invoice['contract_id'] if postpaid_invoice else None}"
            )
        )

        test(
            "Postpaid invoice tax is correct",
            postpaid_invoice is not None
            and postpaid_invoice["tax"] == 1500,
            (
                f"tax="
                f"{postpaid_invoice['tax'] if postpaid_invoice else None}"
            )
        )

        #
        # There should be exactly one generated invoice item:
        # the second contract item.
        #

        postpaid_items = []

        if postpaid_invoice_id is not None:
            postpaid_items = list_invoice_items(
                postpaid_invoice_id
            )

        test(
            "Postpaid invoice has one invoice item",
            len(postpaid_items) == 1,
            f"count={len(postpaid_items)}"
        )

        if postpaid_items:

            postpaid_item = postpaid_items[0]

            invoice_item_ids.append(
                postpaid_item["id"]
            )

            test(
                "Postpaid item belongs to second contract item",
                postpaid_item["contract_item_id"]
                == postpaid_contract_item_id,
                (
                    f"contract_item_id="
                    f"{postpaid_item['contract_item_id']}"
                )
            )

            test(
                "Postpaid item quantity is three",
                postpaid_item["quantity"] == 3,
                f"quantity={postpaid_item['quantity']}"
            )

            test(
                "Postpaid item amount is calculated",
                postpaid_item["amount"] == 9000,
                f"amount={postpaid_item['amount']}"
            )

            generated_spots = list_invoice_item_spots(
                postpaid_item["id"]
            )

            for row in generated_spots:
                if row["id"] not in invoice_item_spot_ids:
                    invoice_item_spot_ids.append(row["id"])

            test(
                "Postpaid item has three associated spots",
                len(generated_spots) == 3,
                f"count={len(generated_spots)}"
            )

            test(
                "All generated billing spots are Completed",
                all(
                    row["status"] == "Completed"
                    for row in generated_spots
                ),
            )


        #
        # The second contract item should now have no billable
        # completed spots remaining.
        #

        unbilled = get_unbilled_completed_spots(
            postpaid_contract_item_id
        )

        test(
            "Postpaid invoice consumes all three completed spots",
            len(unbilled) == 0,
            f"count={len(unbilled)}"
        )


        #
        # Calling create_postpaid_invoice() again should therefore
        # return None.
        #

        second_postpaid_invoice_id = create_postpaid_invoice(
            customer_id=customer_id,
            contract_id=contract_id,
            invoice_number="ZZTEST-POSTPAID-002",
            invoice_date="2026-08-25",
            due_date="2026-09-24",
            notes="Should not be created",
            tax=0,
        )

        test(
            "Second postpaid invoice has no billable spots",
            second_postpaid_invoice_id is None,
            f"invoice_id={second_postpaid_invoice_id}"
        )

        if second_postpaid_invoice_id is not None:
            invoice_ids.append(
                second_postpaid_invoice_id
            )


    except Exception as exc:

        print()
        print("ERROR: Billing regression test raised an exception.")
        print(f"       {type(exc).__name__}: {exc}")
        failed += 1

    finally:

        #
        # ----------------------------------------------------------
        # Cleanup.
        # ----------------------------------------------------------
        #

        print()
        print("Cleaning up billing regression test data...")

        try:

            if connection is None:
                connection = get_connection()

            cursor = connection.cursor()

            #
            # Delete billing associations first.
            #
            # Include all invoice-item/spot associations belonging to
            # our test invoices.  create_postpaid_invoice() creates some
            # of these internally, so they may not be in
            # invoice_item_spot_ids.
            #

            if invoice_ids:

                placeholders = ",".join(
                    ["?"] * len(invoice_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM invoice_item_spots
                    WHERE invoice_item_id IN (
                        SELECT id
                        FROM invoice_items
                        WHERE invoice_id IN ({placeholders})
                    )
                    """,
                    invoice_ids,
                )

            #
            # Also delete any individually tracked associations.
            #

            if invoice_item_spot_ids:

                placeholders = ",".join(
                    ["?"] * len(invoice_item_spot_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM invoice_item_spots
                    WHERE id IN ({placeholders})
                    """,
                    invoice_item_spot_ids,
                )

            #
            # Delete invoice items.
            #

            if invoice_item_ids:
                placeholders = ",".join(
                    ["?"] * len(invoice_item_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM invoice_items
                    WHERE id IN ({placeholders})
                    """,
                    invoice_item_ids,
                )

            #
            # Delete invoices.
            #

            if invoice_ids:
                placeholders = ",".join(
                    ["?"] * len(invoice_ids)
                )

                cursor.execute(
                    f"""
                    DELETE FROM invoices
                    WHERE id IN ({placeholders})
                    """,
                    invoice_ids,
                )

            #
            # Delete spots.
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
            # Delete contract items.
            #

            contract_item_ids = []

            if contract_item_id is not None:
                contract_item_ids.append(
                    contract_item_id
                )

            if postpaid_contract_item_id is not None:
                contract_item_ids.append(
                    postpaid_contract_item_id
                )

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
            # Delete contract.
            #

            if contract_id is not None:
                cursor.execute(
                    """
                    DELETE FROM contracts
                    WHERE id = ?
                    """,
                    (
                        contract_id,
                    )
                )

            #
            # Delete salesperson.
            #

            if salesperson_id is not None:
                cursor.execute(
                    """
                    DELETE FROM salespeople
                    WHERE id = ?
                    """,
                    (
                        salesperson_id,
                    )
                )

            #
            # Delete station.
            #

            if station_id is not None:
                cursor.execute(
                    """
                    DELETE FROM stations
                    WHERE id = ?
                    """,
                    (
                        station_id,
                    )
                )

            #
            # Delete customer.
            #

            if customer_id is not None:
                cursor.execute(
                    """
                    DELETE FROM customers
                    WHERE id = ?
                    """,
                    (
                        customer_id,
                    )
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
        f"Billing regression tests: "
        f"{passed} passed, {failed} failed"
    )
    print("=" * 60)
    print()

    if failed == 0:
        print("ALL BILLING REGRESSION TESTS PASSED")
        return 0

    print("BILLING REGRESSION TESTS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())