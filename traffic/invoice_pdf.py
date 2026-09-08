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
    Image,
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
from traffic.station_invoice_settings import (
    get_station_invoice_settings,
)
from traffic.country_codes import get_country_name


#
# Invoice asset directory.
#
# Logo filenames stored in the database are resolved relative
# to this directory.
#

INVOICE_ASSETS_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "invoice_assets"
)


#
# Fixed logo display sizes.
#

CORPORATE_LOGO_WIDTH = 2.0 * inch
CORPORATE_LOGO_HEIGHT = 0.5 * inch

STATION_LOGO_WIDTH = 1.5 * inch
STATION_LOGO_HEIGHT = 1.5 * inch


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
            stations.id,
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


def _get_invoice_logo(filename):
    """
    Resolve an invoice logo.

    The database normally stores only the filename, for example:

        zbT_corporate_logo.png

    For compatibility, this also accepts paths such as:

        data/invoice_assets/zbT_corporate_logo.png

    and absolute filesystem paths.

    Returns:
        Path | None
    """

    if not filename:
        return None

    value = Path(str(filename).strip())

    project_root = (
        Path(__file__).resolve().parent.parent
    )

    #
    # 1. Absolute filesystem path.
    #

    if value.is_absolute():

        if value.is_file():
            return value

        return None

    #
    # 2. Filename / path relative to invoice_assets.
    #

    candidate = (
        INVOICE_ASSETS_DIRECTORY / value
    )

    if candidate.is_file():
        return candidate

    #
    # 3. Project-relative path.
    #

    candidate = (
        project_root / value
    )

    if candidate.is_file():
        return candidate

    #
    # 4. If a path was supplied, try just its filename.
    #
    # This makes the system tolerant of an old/incorrect
    # directory prefix, provided the filename itself exists
    # in invoice_assets.
    #

    candidate = (
        INVOICE_ASSETS_DIRECTORY
        / value.name
    )

    if candidate.is_file():
        return candidate

    #
    # Nothing found.
    #

    return None


def _make_logo(filename, width, height):
    """
    Create a ReportLab Image for an invoice logo.

    Returns:
        Image | None
    """

    logo_path = _get_invoice_logo(filename)

    if logo_path is None:
        return None

    return Image(
        str(logo_path),
        width=width,
        height=height,
    )


def _make_invoice_header(
    station,
    invoice_settings,
    invoice_title,
    styles,
):
    """
    Build the invoice header.

    Layout:

        Corporate logo                 Station logo
        Biller block

        Station name / call letters / frequency

        INVOICE or DRAFT INVOICE
    """

    normal = styles["Normal"]

    small = ParagraphStyle(
        "InvoiceHeaderSmall",
        parent=normal,
        fontSize=9,
        leading=11,
    )

    title = ParagraphStyle(
        "InvoiceHeaderTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=4,
    )

    #
    # Corporate logo.
    #

    corporate_logo = None

    if invoice_settings is not None:

        corporate_logo = _make_logo(
            invoice_settings["corporate_logo"],
            CORPORATE_LOGO_WIDTH,
            CORPORATE_LOGO_HEIGHT,
        )

    #
    # Station logo.
    #

    station_logo = None

    if invoice_settings is not None:

        station_logo = _make_logo(
            invoice_settings["station_logo"],
            STATION_LOGO_WIDTH,
            STATION_LOGO_HEIGHT,
        )

    #
    # Left side of the logo/header area.
    #

    left_content = []

    if corporate_logo is not None:

        left_content.append(
            corporate_logo
        )

        left_content.append(
            Spacer(
                1,
                0.08 * inch
            )
        )

    #
    # Biller block.
    #
    # The biller block is stored as multiline text.
    #

    if invoice_settings is not None:

        biller_block = (
            invoice_settings["biller_block"]
            or ""
        )

        for line in biller_block.splitlines():

            line = line.strip()

            if line:

                left_content.append(
                    Paragraph(
                        line,
                        small
                    )
                )

    #
    # If the left side is completely empty, provide a
    # small spacer so the header remains stable.
    #

    if not left_content:

        left_content.append(
            Spacer(
                CORPORATE_LOGO_WIDTH,
                0.5 * inch
            )
        )

    #
    # Right side of the header.
    #

    right_content = []

    if station_logo is not None:

        right_content.append(
            station_logo
        )

    else:

        right_content.append(
            Spacer(
                STATION_LOGO_WIDTH,
                STATION_LOGO_HEIGHT
            )
        )

    #
    # Logo/biller area.
    #
    # Available invoice width is 6.5".
    #

    logo_table = Table(
        [
            [
                left_content,
                right_content,
            ]
        ],
        colWidths=[
            5.0 * inch,
            1.5 * inch,
        ],
        rowHeights=[
            1.55 * inch,
        ],
    )

    logo_table.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "ALIGN",
                (1, 0),
                (1, 0),
                "RIGHT",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    #
    # Station information.
    #

    station_line = ""

    if station is not None:

        station_name = (
            station["name"]
            or ""
        )

        call_letters = (
            station["call_letters"]
            or ""
        )

        frequency = (
            station["frequency"]
            or ""
        )

        station_line = station_name

        if call_letters:

            if station_line:
                station_line += " — "

            station_line += call_letters

        if frequency:

            if station_line:
                station_line += " "

            station_line += frequency

    #
    # Build the lower portion of the header.
    #

    lower_header = []

    if station_line:

        lower_header.append(
            Paragraph(
                station_line,
                styles["Heading2"]
            )
        )

    lower_header.append(
        Paragraph(
            invoice_title,
            title
        )
    )

    #
    # Combine logo area and lower header.
    #

    header_table = Table(
        [
            [
                logo_table
            ],
            [
                lower_header
            ],
        ],
        colWidths=[
            6.5 * inch,
        ],
    )

    header_table.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    return header_table


def generate_invoice_pdf(
    invoice_id,
    output_directory="invoices"
):
    """
    Generate a PDF for an invoice.

    Returns:
        Path to the generated PDF.
    """

    invoice = get_invoice(
        invoice_id
    )

    if invoice is None:
        raise ValueError(
            "Invoice not found."
        )

    customer = get_customer(
        invoice["customer_id"]
    )

    if customer is None:
        raise ValueError(
            "Invoice customer not found."
        )

    contract = None

    if invoice["contract_id"] is not None:

        contract = get_contract(
            invoice["contract_id"]
        )

    station = _get_invoice_station(
        invoice["contract_id"]
    )

    #
    # Get station-specific invoice settings.
    #

    invoice_settings = None

    if station is not None:

        invoice_settings = (
            get_station_invoice_settings(
                station["id"]
            )
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

        tax_rate = (
            taxable_items[0]["tax_rate"]
            or 0
        )

    else:

        tax_rate = 0

    #
    # Output path.
    #

    output_path = Path(
        output_directory
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    if invoice["invoice_number"]:

        invoice_number = (
            invoice["invoice_number"]
        )

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

    pdf_path = (
        output_path
        / filename
    )

    #
    # PDF document.
    #

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
    # Invoice title.
    #

    if invoice["status"] == "Draft":

        invoice_title = "DRAFT INVOICE"

    else:

        invoice_title = "INVOICE"

    #
    # Station / logo header.
    #

    story.append(
        _make_invoice_header(
            station,
            invoice_settings,
            invoice_title,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            0.12 * inch
        )
    )

    #
    # Bill To / Invoice information.
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
    ):

        value = customer.get(field)

        if value:

            bill_to.append(
                Paragraph(
                    str(value),
                    normal
                )
            )

    address_parts = []

    locality = customer.get("locality")
    administrative_area = customer.get("administrative_area")
    country_code = customer.get("country_code")

    if locality:
        address_parts.append(
            str(locality)
        )

    if administrative_area:
        address_parts.append(
            str(administrative_area)
        )

    if country_code:

        country_name = get_country_name(
            country_code
        )

        if country_name:
            address_parts.append(
                str(country_name)
            )
        else:
            address_parts.append(
                str(country_code)
            )

    if address_parts:

        bill_to.append(
            Paragraph(
                ", ".join(address_parts),
                normal
            )
        )

    postal_code = customer.get("postal_code")

    if postal_code:

        bill_to.append(
            Paragraph(
                str(postal_code),
                normal
            )
        )

    #
    # Invoice information.
    #

    invoice_info = [
        [
            Paragraph(
                "<b>Invoice Number</b>",
                small
            ),
            invoice_number or "",
        ],
        [
            Paragraph(
                "<b>Invoice Date</b>",
                small
            ),
            invoice["invoice_date"] or "",
        ],
        [
            Paragraph(
                "<b>Due Date</b>",
                small
            ),
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
                Paragraph(
                    "<b>Contract</b>",
                    small
                ),
                contract_number,
            ]
        )

    invoice_info_table = Table(
        invoice_info,
        colWidths=[
            1.25 * inch,
            1.75 * inch,
        ]
    )

    invoice_info_table.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
        ])
    )

    #
    # Put Bill To and invoice information side by side.
    #

    details_table = Table(
        [
            [
                bill_to,
                invoice_info_table,
            ]
        ],
        colWidths=[
            3.75 * inch,
            2.75 * inch,
        ]
    )

    details_table.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    story.append(
        details_table
    )

    story.append(
        Spacer(
            1,
            0.25 * inch
        )
    )

    story.append(
        Spacer(
            1,
            0.2 * inch
        )
    )

    #
    # Bill To.
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
    ):

        value = customer.get(field)

        if value:

            bill_to.append(
                Paragraph(
                    str(value),
                    normal
                )
            )

    address_parts = []

    locality = customer.get("locality")
    administrative_area = customer.get("administrative_area")
    country_code = customer.get("country_code")

    if locality:
        address_parts.append(
            str(locality)
        )

    if administrative_area:
        address_parts.append(
            str(administrative_area)
        )

    if country_code:

        country_name = get_country_name(
            country_code
        )

        if country_name:
            address_parts.append(
                str(country_name)
            )
        else:
            address_parts.append(
                str(country_code)
            )

    if address_parts:

        bill_to.append(
            Paragraph(
                ", ".join(address_parts),
                normal
            )
        )

    postal_code = customer.get("postal_code")

    if postal_code:

        bill_to.append(
            Paragraph(
                str(postal_code),
                normal
            )
        )

    story.extend(
        bill_to
    )

    story.append(
        Spacer(
            1,
            0.25 * inch
        )
    )
    #
    # Invoice items.
    #

    item_rows = [
        [
            Paragraph(
                "<b>Description</b>",
                small
            ),
            Paragraph(
                "<b>Qty</b>",
                small
            ),
            Paragraph(
                "<b>Unit</b>",
                small
            ),
            Paragraph(
                "<b>Amount</b>",
                small
            ),
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

        unit_price = (
            item["unit_price"]
        )

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
                colors.grey,
            ),
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey,
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "RIGHT",
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
        ])
    )

    story.append(
        items_table
    )

    story.append(
        Spacer(
            1,
            0.15 * inch
        )
    )

    #
    # Totals.
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
            Paragraph(
                "<b>Total</b>",
                normal
            ),
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
                "RIGHT",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
        ])
    )

    story.append(
        totals_table
    )

    #
    # Payments.
    #

    payments = list_payments(
        invoice_id=invoice_id
    )

    if payments:

        story.append(
            Spacer(
                1,
                0.12 * inch
            )
        )

        story.append(
            Paragraph(
                "<b>Payments</b>",
                normal
            )
        )

        payment_rows = [
            [
                Paragraph(
                    "<b>Payment Date</b>",
                    small
                ),
                Paragraph(
                    "<b>Method</b>",
                    small
                ),
                Paragraph(
                    "<b>Reference</b>",
                    small
                ),
                Paragraph(
                    "<b>Amount</b>",
                    small
                ),
            ]
        ]

        for payment in payments:

            payment_date = (
                payment["payment_date"]
                or ""
            )

            payment_method = (
                payment["payment_method"]
                or ""
            )

            reference = (
                payment["reference"]
                or ""
            )

            amount = (
                payment["amount"]
                or 0
            )

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
                    colors.grey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "ALIGN",
                    (-1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ])
        )

        story.append(
            payments_table
        )

        #
        # Payment summary.
        #

        paid_amount = (
            get_invoice_paid_amount(
                invoice_id
            )
        )

        balance = (
            get_invoice_balance(
                invoice_id
            )
        )

        payment_status = (
            get_invoice_payment_status(
                invoice_id
            )
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
                Paragraph(
                    "<b>Status</b>",
                    normal
                ),
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
                    "RIGHT",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ])
        )

        story.append(
            Spacer(
                1,
                0.08 * inch
            )
        )

        story.append(
            payment_summary_table
        )

    #
    # Payment instructions.
    #

    if (
        invoice_settings is not None
        and invoice_settings[
            "payment_instructions"
        ]
    ):

        story.append(
            Spacer(
                1,
                0.2 * inch
            )
        )

        story.append(
            Paragraph(
                "<b>Payment Instructions</b>",
                normal
            )
        )

        story.append(
            Paragraph(
                invoice_settings[
                    "payment_instructions"
                ],
                normal
            )
        )

    #
    # Invoice notes.
    #

    if invoice["notes"]:

        story.append(
            Spacer(
                1,
                0.2 * inch
            )
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

    #
    # Invoice footer.
    #

    if (
        invoice_settings is not None
        and invoice_settings[
            "invoice_footer"
        ]
    ):

        story.append(
            Spacer(
                1,
                0.2 * inch
            )
        )

        story.append(
            Paragraph(
                invoice_settings[
                    "invoice_footer"
                ],
                small
            )
        )

    #
    # Build PDF.
    #

    document.build(
        story
    )

    return pdf_path
