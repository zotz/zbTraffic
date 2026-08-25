#!/usr/bin/env python3

#
# traffic/billing.py
#
# Billing operations for zbTraffic.
#
# Billing is deliberately separate from the traffic lifecycle.
#
# Spot status remains:
#     Pending
#     Scheduled
#     Exported
#     Completed
#     Cancelled
#
# Invoice status remains:
#     Draft
#     Issued
#     Void
#
# Paid / partially paid / overdue are derived from payments,
# invoice total and due date and belong in traffic/ar.py.
#

from traffic.database import get_connection
from traffic.utilities import current_timestamp

#
# Invoice operations
#


def create_invoice(customer_id,
                   invoice_number,
                   invoice_date,
                   due_date=None,
                   contract_id=None,
                   status="Draft",
                   notes=None):
    """
    Create a new invoice.

    Returns:
        New invoice id.
    """

    conn = get_connection()
    cursor = conn.cursor()

    now = current_timestamp()

    cursor.execute(
        """
        INSERT INTO invoices (
            customer_id,
            contract_id,
            invoice_number,
            invoice_date,
            due_date,
            status,
            subtotal,
            tax,
            total,
            notes,
            created_date,
            modified_date
        )
        VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)
        """,
        (
            customer_id,
            contract_id,
            invoice_number,
            invoice_date,
            due_date,
            status,
            notes,
            now,
            now
        )
    )

    invoice_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return invoice_id


def get_invoice(invoice_id):
    """
    Return one invoice by id.

    Returns:
        sqlite3.Row, or None if not found.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            customer_id,
            contract_id,
            invoice_number,
            invoice_date,
            due_date,
            status,
            subtotal,
            tax,
            total,
            notes,
            created_date,
            modified_date
        FROM invoices
        WHERE id = ?
        """,
        (invoice_id,)
    )

    invoice = cursor.fetchone()

    conn.close()

    return invoice


def list_invoices(customer_id=None,
                  contract_id=None,
                  status=None):
    """
    Return invoices, optionally filtered by customer,
    contract and/or status.
    """

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            id,
            customer_id,
            contract_id,
            invoice_number,
            invoice_date,
            due_date,
            status,
            subtotal,
            tax,
            total,
            notes,
            created_date,
            modified_date
        FROM invoices
        WHERE 1 = 1
    """

    params = []

    if customer_id is not None:
        sql += " AND customer_id = ?"
        params.append(customer_id)

    if contract_id is not None:
        sql += " AND contract_id = ?"
        params.append(contract_id)

    if status is not None:
        sql += " AND status = ?"
        params.append(status)

    sql += """
        ORDER BY invoice_date DESC, id DESC
    """

    cursor.execute(sql, params)

    invoices = cursor.fetchall()

    conn.close()

    return invoices


def update_invoice(invoice_id,
                   invoice_date=None,
                   due_date=None,
                   status=None,
                   notes=None):
    """
    Update invoice header information.

    Invoice totals are maintained separately by
    recalculate_invoice_totals().
    """

    conn = get_connection()
    cursor = conn.cursor()

    fields = []
    params = []

    if invoice_date is not None:
        fields.append("invoice_date = ?")
        params.append(invoice_date)

    if due_date is not None:
        fields.append("due_date = ?")
        params.append(due_date)

    if status is not None:
        fields.append("status = ?")
        params.append(status)

    if notes is not None:
        fields.append("notes = ?")
        params.append(notes)

    if not fields:
        conn.close()
        return False

    fields.append("modified_date = ?")
    params.append(current_timestamp())

    params.append(invoice_id)

    sql = """
        UPDATE invoices
        SET
            {}
        WHERE id = ?
    """.format(", ".join(fields))

    cursor.execute(sql, params)

    changed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return changed


#
# Invoice item operations
#


def add_invoice_item(invoice_id,
                     description,
                     quantity=1,
                     unit_price=None,
                     amount=0,
                     contract_item_id=None):
    """
    Add an item to an invoice.

    If unit_price is supplied and amount is left at 0,
    amount is calculated as quantity * unit_price.

    Returns:
        New invoice item id.
    """

    if amount == 0 and unit_price is not None:
        amount = quantity * unit_price

    conn = get_connection()
    cursor = conn.cursor()

    now = current_timestamp()

    cursor.execute(
        """
        INSERT INTO invoice_items (
            invoice_id,
            contract_item_id,
            description,
            quantity,
            unit_price,
            amount,
            created_date,
            modified_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_id,
            contract_item_id,
            description,
            quantity,
            unit_price,
            amount,
            now,
            now
        )
    )

    invoice_item_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return invoice_item_id


def get_invoice_item(invoice_item_id):
    """
    Return one invoice item by id.

    Returns:
        sqlite3.Row, or None if not found.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            invoice_id,
            contract_item_id,
            description,
            quantity,
            unit_price,
            amount,
            created_date,
            modified_date
        FROM invoice_items
        WHERE id = ?
        """,
        (invoice_item_id,)
    )

    item = cursor.fetchone()

    conn.close()

    return item


def list_invoice_items(invoice_id):
    """
    Return all items belonging to an invoice.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            invoice_id,
            contract_item_id,
            description,
            quantity,
            unit_price,
            amount,
            created_date,
            modified_date
        FROM invoice_items
        WHERE invoice_id = ?
        ORDER BY id
        """,
        (invoice_id,)
    )

    items = cursor.fetchall()

    conn.close()

    return items


def update_invoice_item(invoice_item_id,
                        description=None,
                        quantity=None,
                        unit_price=None,
                        amount=None,
                        contract_item_id=None):
    """
    Update an invoice item.

    Amount may be supplied explicitly. If amount is not supplied,
    but quantity and/or unit_price are being changed, amount is
    recalculated when both values are available.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            quantity,
            unit_price
        FROM invoice_items
        WHERE id = ?
        """,
        (invoice_item_id,)
    )

    existing = cursor.fetchone()

    if existing is None:
        conn.close()
        return False

    new_quantity = existing["quantity"]
    new_unit_price = existing["unit_price"]

    if quantity is not None:
        new_quantity = quantity

    if unit_price is not None:
        new_unit_price = unit_price

    if amount is None and new_unit_price is not None:
        amount = new_quantity * new_unit_price

    fields = []
    params = []

    if description is not None:
        fields.append("description = ?")
        params.append(description)

    if quantity is not None:
        fields.append("quantity = ?")
        params.append(quantity)

    if unit_price is not None:
        fields.append("unit_price = ?")
        params.append(unit_price)

    if amount is not None:
        fields.append("amount = ?")
        params.append(amount)

    if contract_item_id is not None:
        fields.append("contract_item_id = ?")
        params.append(contract_item_id)

    if not fields:
        conn.close()
        return False

    fields.append("modified_date = ?")
    params.append(current_timestamp())

    params.append(invoice_item_id)

    sql = """
        UPDATE invoice_items
        SET
            {}
        WHERE id = ?
    """.format(", ".join(fields))

    cursor.execute(sql, params)

    changed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return changed


#
# Invoice totals
#


def recalculate_invoice_totals(invoice_id, tax=0):
    """
    Recalculate an invoice subtotal and total from its items.

    Tax is supplied by the caller because tax rules have not yet
    been implemented.

    Returns:
        (subtotal, tax, total)
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(amount), 0)
        FROM invoice_items
        WHERE invoice_id = ?
        """,
        (invoice_id,)
    )

    row = cursor.fetchone()

    subtotal = row[0]
    total = subtotal + tax

    cursor.execute(
        """
        UPDATE invoices
        SET
            subtotal = ?,
            tax = ?,
            total = ?,
            modified_date = ?
        WHERE id = ?
        """,
        (
            subtotal,
            tax,
            total,
            current_timestamp(),
            invoice_id
        )
    )

    conn.commit()
    conn.close()

    return subtotal, tax, total


#
# POSTPAID spot billing
#


def get_unbilled_completed_spots(contract_item_id):
    """
    Return completed spots for a contract item that have not
    already been actively associated with an invoice item.

    This is the primary source of billable spots for POSTPAID
    contracts.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            s.id,
            s.station_id,
            s.contract_item_id,
            s.commercial_id,
            s.avail_id,
            s.air_date,
            s.air_time,
            s.status
        FROM spots s
        LEFT JOIN invoice_item_spots iis
            ON iis.spot_id = s.id
           AND iis.active = 1
        WHERE s.contract_item_id = ?
          AND s.status = 'Completed'
          AND iis.id IS NULL
        ORDER BY s.air_date, s.air_time, s.id
        """,
        (contract_item_id,)
    )

    spots = cursor.fetchall()

    conn.close()

    return spots


def attach_spot_to_invoice_item(invoice_item_id, spot_id):
    """
    Associate a completed spot with an invoice item.

    The database unique index prevents a spot from having more
    than one active billing association.

    Returns:
        New invoice_item_spots id.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO invoice_item_spots (
            invoice_item_id,
            spot_id,
            active,
            created_date,
            modified_date
        )
        VALUES (?, ?, 1, ?, ?)
        """,
        (
            invoice_item_id,
            spot_id,
            current_timestamp(),
            current_timestamp()
        )
    )

    association_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return association_id


def attach_spots_to_invoice_item(invoice_item_id, spot_ids):
    """
    Associate multiple completed spots with an invoice item.

    Returns:
        Number of spots successfully attached.

    The entire operation is performed as one transaction.
    """

    if not spot_ids:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    now = current_timestamp()

    count = 0

    for spot_id in spot_ids:

        cursor.execute(
            """
            INSERT INTO invoice_item_spots (
                invoice_item_id,
                spot_id,
                active,
                created_date,
                modified_date
            )
            VALUES (?, ?, 1, ?, ?)
            """,
            (
                invoice_item_id,
                spot_id,
                now,
                now
            )
        )

        count += 1

    conn.commit()
    conn.close()

    return count


def list_invoice_item_spots(invoice_item_id):
    """
    Return the spots associated with an invoice item.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            s.id,
            s.station_id,
            s.contract_item_id,
            s.commercial_id,
            s.avail_id,
            s.air_date,
            s.air_time,
            s.status,
            iis.active
        FROM invoice_item_spots iis
        JOIN spots s
            ON s.id = iis.spot_id
        WHERE iis.invoice_item_id = ?
        ORDER BY s.air_date, s.air_time, s.id
        """,
        (invoice_item_id,)
    )

    spots = cursor.fetchall()

    conn.close()

    return spots


def deactivate_invoice_item_spot(invoice_item_spot_id):
    """
    Deactivate an invoice-item/spot association.

    The spot itself is NOT changed.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE invoice_item_spots
        SET
            active = 0,
            modified_date = ?
        WHERE id = ?
          AND active = 1
        """,
        (
            current_timestamp(),
            invoice_item_spot_id
        )
    )

    changed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return changed


#
# Convenience function for POSTPAID billing
#


def create_postpaid_invoice(customer_id,
                            contract_id,
                            invoice_number,
                            invoice_date,
                            due_date=None,
                            notes=None,
                            tax=0):
    """
    Create a draft POSTPAID invoice for completed, unbilled spots
    belonging to a contract.

    This function creates the invoice and one invoice item for
    each contract item that has completed spots.

    Returns:
        New invoice id, or None if there are no billable spots.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            description,
            commercial_title,
            spot_length_seconds
        FROM contract_items
        WHERE contract_id = ?
          AND active = 1
        ORDER BY id
        """,
        (contract_id,)
    )

    contract_items = cursor.fetchall()

    conn.close()

    billable_items = []

    for contract_item in contract_items:

        spots = get_unbilled_completed_spots(contract_item["id"])

        if spots:
            billable_items.append(
                (
                    contract_item,
                    spots
                )
            )

    if not billable_items:
        return None

    invoice_id = create_invoice(
        customer_id=customer_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        due_date=due_date,
        contract_id=contract_id,
        status="Draft",
        notes=notes
    )

    for contract_item, spots in billable_items:

        description = contract_item["description"]

        if not description:
            description = contract_item["commercial_title"]

        if not description:
            description = "Advertising spots"

        invoice_item_id = add_invoice_item(
            invoice_id=invoice_id,
            contract_item_id=contract_item["id"],
            description=description,
            quantity=len(spots),
            unit_price=None,
            amount=0
        )

        attach_spots_to_invoice_item(
            invoice_item_id,
            [spot["id"] for spot in spots]
        )

    recalculate_invoice_totals(
        invoice_id,
        tax=tax
    )

    return invoice_id