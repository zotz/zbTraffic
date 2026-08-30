# traffic/invoice_pdf.py

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from traffic.billing import (
    get_invoice,
    list_invoice_items,
    list_payments,
    get_invoice_paid_amount,
    get_invoice_balance,
    get_invoice_payment_status,
)
from traffic.customers import get_customer
from traffic.contracts import get_contract
from traffic.database import get_connection


def _get_invoice_station(contract_id):
    """
    Return station information for the invoice's contract.

    Returns:
        sqlite3.Row, or None.
    """

    if contract_id is None:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            stations.name,
            stations.call_letters,
            stations.frequency
        FROM contracts
        JOIN stations
            ON contracts.station_id = stations.id
        WHERE contracts.id = ?
        """,
        (contract_id,)
    )

    station = cursor.fetchone()

    connection.close()

    return station


def generate_invoice_pdf(invoice_id, output_directory="invoices"):
    """
    Generate a PDF for an invoice.

    Returns:
        Path to the generated PDF.
    """

    invoice = get_invoice(invoice_id)

    if invoice is None:
        raise ValueError("Invoice not found.")

    customer = get_customer(
        invoice["customer_id"]
    )

    if customer is None:
        raise ValueError("Invoice customer not found.")

    contract = None

    if invoice["contract_id"] is not None:
        contract = get_contract(
            invoice["contract_id"]
        )

    station = _get_invoice_station(
        invoice["contract_id"]
    )

    items = list_invoice_items(
        invoice_id
    )

    #
    # Determine the tax rate stored on the invoice items.
    #

    taxable_items = [
        item
        for item in items
        if item["taxable"]
    ]

    if taxable_items:

        tax_rate = taxable_items[0]["tax_rate"] or 0

    else:

        tax_rate = 0

    output_path = Path(
        output_directory
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    if invoice["invoice_number"]:

        invoice_number = invoice["invoice_number"]

        filename = (
            "Invoice-{}.pdf".format(
                invoice_number
            )
        )

    else:

        invoice_number = "DRAFT"

        filename = (
            "Draft-Invoice-{}.pdf".format(
                invoice_id
            )
        )

    pdf_path = output_path / filename

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=LETTER,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()

    normal = styles["Normal"]

    title = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=8,
    )

    small = ParagraphStyle(
        "Small",
        parent=normal,
        fontSize=9,
        leading=11,
    )

    story = []

    #
    # Station header
    #

    if station is not None:

        station_name = station["name"] or ""
        call_letters = station["call_letters"] or ""
        frequency = station["frequency"] or ""

        station_line = station_name

        if call_letters:
            station_line += " — {}".format(
                call_letters
            )

        if frequency:
            station_line += " {}".format(
                frequency
            )

        story.append(
            Paragraph(
                station_line,
                styles["Heading2"]
            )
        )

    if invoice["status"] == "Draft":

        invoice_title = "DRAFT INVOICE"

    else:

        invoice_title = "INVOICE"


    story.append(
        Paragraph(
            invoice_title,
            title
        )
    )

    #
    # Invoice information
    #

    invoice_info = [
        [
            Paragraph("<b>Invoice Number</b>", small),
            invoice_number,
        ],
        [
            Paragraph("<b>Invoice Date</b>", small),
            invoice["invoice_date"] or "",
        ],
        [
            Paragraph("<b>Due Date</b>", small),
            invoice["due_date"] or "",
        ],
    ]

    if contract is not None:

        contract_number = (
            contract["contract_number"]
            or ""
        )

        invoice_info.append(
            [
                Paragraph("<b>Contract</b>", small),
                contract_number,
            ]
        )

    info_table = Table(
        invoice_info,
        colWidths=[
            1.3 * inch,
            2.5 * inch,
        ]
    )

    info_table.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
        ])
    )

    story.append(info_table)

    story.append(
        Spacer(1, 0.2 * inch)
    )

    #
    # Bill To
    #

    bill_to = [
        Paragraph(
            "<b>Bill To</b>",
            normal
        )
    ]

    bill_to.append(
        Paragraph(
            customer["company_name"],
            normal
        )
    )

    for field in (
        "address_line1",
        "address_line2",
        "locality",
        "administrative_area",
        "postal_code",
    ):

        value = customer.get(field)

        if value:
            bill_to.append(
                Paragraph(
                    str(value),
                    normal
                )
            )

    if customer.get("country_code"):
        bill_to.append(
            Paragraph(
                customer["country_code"],
                normal
            )
        )

    story.extend(bill_to)

    story.append(
        Spacer(1, 0.25 * inch)
    )

    #
    # Invoice items
    #

    item_rows = [
        [
            Paragraph("<b>Description</b>", small),
            Paragraph("<b>Qty</b>", small),
            Paragraph("<b>Unit</b>", small),
            Paragraph("<b>Amount</b>", small),
        ]
    ]

    for item in items:

        quantity = item["quantity"]

        if quantity is None:
            quantity_text = ""
        elif float(quantity).is_integer():
            quantity_text = str(
                int(quantity)
            )
        else:
            quantity_text = "{:g}".format(
                quantity
            )

        unit_price = item["unit_price"]

        if unit_price is None:
            unit_text = ""
        else:
            unit_text = "${:,.2f}".format(
                unit_price / 100.0
            )

        amount_text = "${:,.2f}".format(
            item["amount"] / 100.0
        )

        item_rows.append(
            [
                Paragraph(
                    item["description"],
                    small
                ),
                quantity_text,
                unit_text,
                amount_text,
            ]
        )

    items_table = Table(
        item_rows,
        colWidths=[
            3.7 * inch,
            0.6 * inch,
            0.9 * inch,
            1.0 * inch,
        ],
        repeatRows=1,
    )

    items_table.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "RIGHT"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
        ])
    )

    story.append(items_table)

    story.append(
        Spacer(1, 0.15 * inch)
    )

    #
    # Totals
    #

    subtotal = invoice["subtotal"] or 0
    tax = invoice["tax"] or 0
    total = invoice["total"] or 0

    totals = [
        [
            "Subtotal",
            "${:,.2f}".format(
                subtotal / 100.0
            )
        ],
        [
            "Tax ({:.2f}%)".format(
                tax_rate / 100.0
            ),
            "${:,.2f}".format(
                tax / 100.0
            )
        ],
        [
            Paragraph("<b>Total</b>", normal),
            Paragraph(
                "<b>${:,.2f}</b>".format(
                    total / 100.0
                ),
                normal
            )
        ],
    ]

    totals_table = Table(
        totals,
        colWidths=[
            1.0 * inch,
            1.0 * inch,
        ],
        hAlign="RIGHT",
    )

    totals_table.setStyle(
        TableStyle([
            (
                "ALIGN",
                (1, 0),
                (1, -1),
                "RIGHT"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
        ])
    )

    story.append(
        totals_table
    )

    #
    # Payments
    #

    payments = list_payments(
        invoice_id=invoice_id
    )

    if payments:

        story.append(
            Spacer(1, 0.12 * inch)
        )

        story.append(
            Paragraph(
                "<b>Payments</b>",
                normal
            )
        )

        payment_rows = [
            [
                Paragraph("<b>Payment Date</b>", small),
                Paragraph("<b>Method</b>", small),
                Paragraph("<b>Reference</b>", small),
                Paragraph("<b>Amount</b>", small),
            ]
        ]

        for payment in payments:

            payment_date = (
                payment["payment_date"] or ""
            )

            payment_method = (
                payment["payment_method"] or ""
            )

            reference = (
                payment["reference"] or ""
            )

            amount = payment["amount"] or 0

            payment_rows.append(
                [
                    payment_date,
                    payment_method,
                    reference,
                    "${:,.2f}".format(
                        amount / 100.0
                    ),
                ]
            )

        payments_table = Table(
            payment_rows,
            colWidths=[
                1.1 * inch,
                1.0 * inch,
                1.8 * inch,
                1.0 * inch,
            ],
            repeatRows=1,
        )

        payments_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "ALIGN",
                    (-1, 1),
                    (-1, -1),
                    "RIGHT"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
            ])
        )

        story.append(
            payments_table
        )

        #
        # Payment Summary
        #

        paid_amount = get_invoice_paid_amount(
            invoice_id
        )

        balance = get_invoice_balance(
            invoice_id
        )

        payment_status = get_invoice_payment_status(
            invoice_id
        )

        payment_summary = [
            [
                "Paid",
                "${:,.2f}".format(
                    paid_amount / 100.0
                )
            ],
            [
                "Balance Due",
                "${:,.2f}".format(
                    balance / 100.0
                )
            ],
            [
                Paragraph("<b>Status</b>", normal),
                Paragraph(
                    "<b>{}</b>".format(
                        payment_status
                    ),
                    normal
                )
            ],
        ]

        payment_summary_table = Table(
            payment_summary,
            colWidths=[
                1.0 * inch,
                1.0 * inch,
            ],
            hAlign="RIGHT",
        )

        payment_summary_table.setStyle(
            TableStyle([
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
            ])
        )

        story.append(
            Spacer(1, 0.08 * inch)
        )

        story.append(
            payment_summary_table
        )

    #
    # Notes
    #

    if invoice["notes"]:

        story.append(
            Spacer(1, 0.2 * inch)
        )

        story.append(
            Paragraph(
                "<b>Notes</b>",
                normal
            )
        )

        story.append(
            Paragraph(
                invoice["notes"],
                normal
            )
        )

    document.build(
        story
    )

    return pdf_path
