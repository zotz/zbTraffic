#!/usr/bin/env python3

#
# prototype/billing_board.py
#
# Billing / A/R prototype GUI.
#
# This is still a prototype, but it now exercises the complete
# operational billing workflow:
#
#     Customer
#         |
#       Contract
#         |
#    Contract Item
#         |
#       Spots
#         |
#     Completed
#         |
#   Postpaid Invoice
#
# The important distinction is that billing state is NOT stored
# in spots.status.  Spot status remains part of the traffic
# lifecycle:
#
#     Pending
#     Scheduled
#     Exported
#     Completed
#     Cancelled
#
# Billing associations are handled by the billing layer and
# invoice_item_spots.
#


import tkinter as tk
from tkinter import ttk, messagebox

from datetime import date
from decimal import Decimal, ROUND_HALF_UP


from traffic.database import get_connection

from traffic.billing import (
    create_invoice,
    get_invoice,
    list_invoices,
    add_invoice_item,
    get_invoice_item,
    list_invoice_items,
    update_invoice_item,
    recalculate_invoice_totals,
    get_unbilled_completed_spots,
    list_invoice_item_spots,
    create_postpaid_invoice,
)


# ----------------------------------------------------------------------
# Formatting helpers
# ----------------------------------------------------------------------


def money(cents):
    """
    Display integer cents as dollars.

    Example:

        1250 -> $12.50
    """

    if cents is None:
        return ""

    return f"${cents / 100:,.2f}"


def cents_from_text(value):
    """
    Convert a dollar entry such as:

        25
        25.00
        $25.00
        $1,250.50

    into integer cents.

    Also accepts:

        cents:1250

    for explicit cent entry.
    """

    value = value.strip()

    if not value:
        return None

    if value.lower().startswith("cents:"):

        return int(
            value[6:].strip()
        )

    value = (
        value
        .replace("$", "")
        .replace(",", "")
    )

    return int(
        (
            Decimal(value)
            * Decimal("100")
        ).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


# ----------------------------------------------------------------------
# Database reads
# ----------------------------------------------------------------------


def fetch_customers():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            company_name

        FROM customers

        WHERE active = 1

        ORDER BY company_name
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


def fetch_contracts(
    customer_id=None
):

    connection = get_connection()
    cursor = connection.cursor()

    sql = """
        SELECT
            c.id,
            c.customer_id,
            c.contract_number,
            c.description,
            c.status,
            c.start_date,
            c.end_date

        FROM contracts c

        WHERE c.active = 1
    """

    parameters = []

    if customer_id is not None:

        sql += """
            AND c.customer_id = ?
        """

        parameters.append(
            customer_id
        )

    sql += """
        ORDER BY
            c.contract_number,
            c.id
    """

    cursor.execute(
        sql,
        parameters
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


def fetch_contract_items(
    contract_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
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

        FROM contract_items

        WHERE contract_id = ?

        ORDER BY id
        """,
        (
            contract_id,
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


def fetch_contract(
    contract_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *

        FROM contracts

        WHERE id = ?
        """,
        (
            contract_id,
        )
    )

    row = cursor.fetchone()

    connection.close()

    return row


def fetch_customer_name(
    customer_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT company_name

        FROM customers

        WHERE id = ?
        """,
        (
            customer_id,
        )
    )

    row = cursor.fetchone()

    connection.close()

    if row:

        return row["company_name"]

    return ""


# ----------------------------------------------------------------------
# Spot reads
# ----------------------------------------------------------------------


def fetch_contract_item_spots(
    contract_item_id
):

    """
    Return all traffic spots belonging to the selected
    contract item.

    This is intentionally separate from the billing functions.

    A spot can be:

        Pending
        Scheduled
        Exported
        Completed
        Cancelled

    and can independently have a billing association.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            spots.id,
            spots.contract_item_id,
            spots.commercial_id,
            spots.avail_id,
            spots.air_date,
            spots.air_time,
            spots.status,
            spots.actual_air_time,

            commercials.cart_number,
            commercials.title

        FROM spots

        LEFT JOIN commercials
            ON spots.commercial_id = commercials.id

        WHERE
            spots.contract_item_id = ?

        ORDER BY
            spots.air_date,
            spots.air_time,
            spots.id
        """,
        (
            contract_item_id,
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


def fetch_spot_counts(
    contract_item_id
):

    """
    Return useful status counts for a contract item.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            status,
            COUNT(*) AS count

        FROM spots

        WHERE contract_item_id = ?

        GROUP BY status
        """,
        (
            contract_item_id,
        )
    )

    rows = cursor.fetchall()

    connection.close()

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

    return counts


def mark_spots_completed(
    spot_ids
):

    """
    Mark exported spots as Completed.

    We deliberately require the current status to be
    Exported.

    This is the same traffic lifecycle rule used by the
    reconciliation GUI.
    """

    if not spot_ids:

        return 0

    connection = get_connection()
    cursor = connection.cursor()

    changed = 0

    try:

        for spot_id in spot_ids:

            cursor.execute(
                """
                UPDATE spots

                SET
                    status = 'Completed'

                WHERE
                    id = ?

                    AND status = 'Exported'
                """,
                (
                    spot_id,
                )
            )

            changed += cursor.rowcount

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()

    return changed


# ----------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------


class BillingBoard(tk.Tk):

    def __init__(
        self
    ):

        super().__init__()

        self.title(
            "zbTraffic Billing Board - Prototype"
        )

        self.geometry(
            "1450x900"
        )

        self.minsize(
            1150,
            750
        )

        #
        # Current selections.
        #

        self.customers = []
        self.contracts = []
        self.contract_items = []

        self.selected_customer_id = None
        self.selected_contract_id = None
        self.selected_contract_item_id = None

        self.selected_spot_id = None

        self.selected_invoice_id = None
        self.selected_invoice_item_id = None

        #
        # Build and load.
        #

        self.build_ui()

        self.load_customers()


    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------


    def build_ui(self):

        #
        # Top selectors.
        #

        top = ttk.Frame(
            self,
            padding=8
        )

        top.pack(
            fill="x"
        )


        ttk.Label(
            top,
            text="Customer:"
        ).pack(
            side="left"
        )


        self.customer_var = tk.StringVar()

        self.customer_combo = ttk.Combobox(
            top,
            textvariable=self.customer_var,
            state="readonly",
            width=34,
        )

        self.customer_combo.pack(
            side="left",
            padx=(5, 15)
        )

        self.customer_combo.bind(
            "<<ComboboxSelected>>",
            self.customer_changed
        )


        ttk.Label(
            top,
            text="Contract:"
        ).pack(
            side="left"
        )


        self.contract_var = tk.StringVar()

        self.contract_combo = ttk.Combobox(
            top,
            textvariable=self.contract_var,
            state="readonly",
            width=42,
        )

        self.contract_combo.pack(
            side="left",
            padx=5
        )

        self.contract_combo.bind(
            "<<ComboboxSelected>>",
            self.contract_changed
        )


        ttk.Button(
            top,
            text="Refresh",
            command=self.refresh_all
        ).pack(
            side="right"
        )


        #
        # --------------------------------------------------------------
        # Contract information
        # --------------------------------------------------------------
        #

        contract_info = ttk.LabelFrame(
            self,
            text="Contract",
            padding=8
        )

        contract_info.pack(
            fill="x",
            padx=8,
            pady=(0, 6)
        )


        self.contract_info_var = tk.StringVar(
            value="Select a contract."
        )


        ttk.Label(
            contract_info,
            textvariable=self.contract_info_var,
            justify="left"
        ).pack(
            anchor="w"
        )


        #
        # --------------------------------------------------------------
        # Contract items
        # --------------------------------------------------------------
        #

        item_frame = ttk.LabelFrame(
            self,
            text="Contract Items",
            padding=6
        )

        item_frame.pack(
            fill="x",
            padx=8,
            pady=(0, 6)
        )


        item_columns = (
            "id",
            "title",
            "description",
            "quantity",
            "pricing",
            "unit",
            "total",
            "length",
            "scheduled",
            "exported",
            "completed",
            "unbilled",
        )


        self.item_tree = ttk.Treeview(
            item_frame,
            columns=item_columns,
            show="headings",
            height=6
        )


        item_headings = {

            "id": "ID",

            "title": "Commercial",

            "description": "Description",

            "quantity": "Qty",

            "pricing": "Pricing",

            "unit": "Unit",

            "total": "Total",

            "length": "Length",

            "scheduled": "Scheduled",

            "exported": "Exported",

            "completed": "Completed",

            "unbilled": "Unbilled",
        }


        item_widths = {

            "id": 45,

            "title": 180,

            "description": 210,

            "quantity": 55,

            "pricing": 80,

            "unit": 85,

            "total": 90,

            "length": 65,

            "scheduled": 75,

            "exported": 70,

            "completed": 75,

            "unbilled": 70,
        }


        for column in item_columns:

            self.item_tree.heading(
                column,
                text=item_headings[column]
            )

            self.item_tree.column(
                column,
                width=item_widths[column],
                anchor=(
                    "w"
                    if column in (
                        "title",
                        "description"
                    )
                    else "center"
                )
            )


        item_scroll = ttk.Scrollbar(
            item_frame,
            orient="vertical",
            command=self.item_tree.yview
        )


        self.item_tree.configure(
            yscrollcommand=item_scroll.set
        )


        self.item_tree.pack(
            side="left",
            fill="x",
            expand=True
        )


        item_scroll.pack(
            side="right",
            fill="y"
        )


        self.item_tree.bind(
            "<<TreeviewSelect>>",
            self.contract_item_selected
        )


        item_buttons = ttk.Frame(
            self
        )

        item_buttons.pack(
            fill="x",
            padx=8,
            pady=(0, 6)
        )


        ttk.Button(
            item_buttons,
            text="Refresh Contract Items",
            command=self.load_contract_items
        ).pack(
            side="left"
        )


        ttk.Button(
            item_buttons,
            text="Create Postpaid Invoice",
            command=self.create_postpaid
        ).pack(
            side="left",
            padx=6
        )


        ttk.Label(
            item_buttons,
            text=(
                "Select a contract item to see its spots below."
            )
        ).pack(
            side="left",
            padx=12
        )


        #
        # --------------------------------------------------------------
        # Main lower area.
        #
        # Left = spots
        # Right = invoices
        #
        # --------------------------------------------------------------
        #

        main = ttk.Panedwindow(
            self,
            orient="horizontal"
        )

        main.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=(0, 6)
        )


        #
        # ==============================================================
        # LEFT: SPOTS
        # ============================================================== 
        #

        spots_frame = ttk.LabelFrame(
            main,
            text="Spots for Selected Contract Item",
            padding=8
        )


        main.add(
            spots_frame,
            weight=1
        )


        self.spot_summary_var = tk.StringVar(
            value="Select a contract item."
        )


        ttk.Label(
            spots_frame,
            textvariable=self.spot_summary_var,
            justify="left"
        ).pack(
            anchor="w",
            pady=(0, 6)
        )


        spot_tree_frame = ttk.Frame(
            spots_frame
        )

        spot_tree_frame.pack(
            fill="both",
            expand=True
        )


        spot_columns = (
            "id",
            "date",
            "time",
            "cart",
            "title",
            "status",
            "actual",
            "billed",
        )


        self.spot_tree = ttk.Treeview(
            spot_tree_frame,
            columns=spot_columns,
            show="headings",
            selectmode="extended"
        )


        spot_headings = {

            "id": "ID",

            "date": "Air Date",

            "time": "Air Time",

            "cart": "Cart",

            "title": "Commercial",

            "status": "Status",

            "actual": "Actual",

            "billed": "Billed",
        }


        spot_widths = {

            "id": 45,

            "date": 90,

            "time": 75,

            "cart": 80,

            "title": 180,

            "status": 90,

            "actual": 75,

            "billed": 65,
        }


        for column in spot_columns:

            self.spot_tree.heading(
                column,
                text=spot_headings[column]
            )

            self.spot_tree.column(
                column,
                width=spot_widths[column],
                anchor=(
                    "w"
                    if column == "title"
                    else "center"
                )
            )


        spot_y = ttk.Scrollbar(
            spot_tree_frame,
            orient="vertical",
            command=self.spot_tree.yview
        )


        spot_x = ttk.Scrollbar(
            spot_tree_frame,
            orient="horizontal",
            command=self.spot_tree.xview
        )


        self.spot_tree.configure(
            yscrollcommand=spot_y.set,
            xscrollcommand=spot_x.set
        )


        self.spot_tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )


        spot_y.grid(
            row=0,
            column=1,
            sticky="ns"
        )


        spot_x.grid(
            row=1,
            column=0,
            sticky="ew"
        )


        spot_tree_frame.rowconfigure(
            0,
            weight=1
        )


        spot_tree_frame.columnconfigure(
            0,
            weight=1
        )


        self.spot_tree.bind(
            "<<TreeviewSelect>>",
            self.spot_selected
        )



        spot_buttons = ttk.Frame(
            spots_frame
        )

        spot_buttons.pack(
            fill="x",
            pady=(6, 0)
        )


        ttk.Button(
            spot_buttons,
            text="Refresh Spots",
            command=self.load_contract_item_spots
        ).pack(
            side="left"
        )




        #
        # ==============================================================
        # RIGHT: INVOICES
        # ============================================================== 
        #

        invoice_frame = ttk.LabelFrame(
            main,
            text="Invoices",
            padding=8
        )


        main.add(
            invoice_frame,
            weight=1
        )


        invoice_pane = ttk.Panedwindow(
            invoice_frame,
            orient="vertical"
        )


        invoice_pane.pack(
            fill="both",
            expand=True
        )


        #
        # --------------------------------------------------------------
        # Invoice list
        # --------------------------------------------------------------
        #

        invoice_list_frame = ttk.Frame(
            invoice_pane
        )


        invoice_pane.add(
            invoice_list_frame,
            weight=1
        )


        invoice_columns = (
            "id",
            "number",
            "date",
            "due",
            "status",
            "subtotal",
            "tax",
            "total",
        )


        self.invoice_tree = ttk.Treeview(
            invoice_list_frame,
            columns=invoice_columns,
            show="headings"
        )


        invoice_headings = {

            "id": "ID",

            "number": "Invoice",

            "date": "Date",

            "due": "Due",

            "status": "Status",

            "subtotal": "Subtotal",

            "tax": "Tax",

            "total": "Total",
        }


        invoice_widths = {

            "id": 45,

            "number": 120,

            "date": 90,

            "due": 90,

            "status": 75,

            "subtotal": 90,

            "tax": 75,

            "total": 90,
        }


        for column in invoice_columns:

            self.invoice_tree.heading(
                column,
                text=invoice_headings[column]
            )

            self.invoice_tree.column(
                column,
                width=invoice_widths[column],
                anchor="center"
            )


        invoice_y = ttk.Scrollbar(
            invoice_list_frame,
            orient="vertical",
            command=self.invoice_tree.yview
        )


        self.invoice_tree.configure(
            yscrollcommand=invoice_y.set
        )


        self.invoice_tree.pack(
            side="left",
            fill="both",
            expand=True
        )


        invoice_y.pack(
            side="right",
            fill="y"
        )


        self.invoice_tree.bind(
            "<<TreeviewSelect>>",
            self.invoice_selected
        )


        invoice_buttons = ttk.Frame(
            invoice_frame
        )

        invoice_buttons.pack(
            fill="x",
            pady=(6, 0)
        )


        ttk.Button(
            invoice_buttons,
            text="New Draft Invoice",
            command=self.new_invoice
        ).pack(
            side="left"
        )


        ttk.Button(
            invoice_buttons,
            text="Refresh Invoices",
            command=self.load_invoices
        ).pack(
            side="left",
            padx=6
        )


        #
        # --------------------------------------------------------------
        # Invoice detail
        # --------------------------------------------------------------
        #

        detail_frame = ttk.LabelFrame(
            invoice_pane,
            text="Invoice Detail",
            padding=8
        )


        invoice_pane.add(
            detail_frame,
            weight=1
        )


        self.invoice_info = tk.StringVar(
            value="Select an invoice."
        )


        ttk.Label(
            detail_frame,
            textvariable=self.invoice_info,
            justify="left"
        ).pack(
            anchor="w"
        )


        self.invoice_item_tree = ttk.Treeview(
            detail_frame,
            columns=(
                "id",
                "description",
                "quantity",
                "unit",
                "amount",
                "spots",
            ),
            show="headings",
            height=7
        )


        detail_headings = {

            "id": "ID",

            "description": "Description",

            "quantity": "Qty",

            "unit": "Unit",

            "amount": "Amount",

            "spots": "Spots",
        }


        detail_widths = {

            "id": 45,

            "description": 200,

            "quantity": 60,

            "unit": 85,

            "amount": 90,

            "spots": 60,
        }


        for column in detail_headings:

            self.invoice_item_tree.heading(
                column,
                text=detail_headings[column]
            )

            self.invoice_item_tree.column(
                column,
                width=detail_widths[column],
                anchor=(
                    "w"
                    if column == "description"
                    else "center"
                )
            )


        self.invoice_item_tree.pack(
            fill="x",
            expand=False,
            pady=(8, 6)
        )


        self.invoice_item_tree.bind(
            "<<TreeviewSelect>>",
            self.invoice_item_selected
        )


        detail_buttons = ttk.Frame(
            detail_frame
        )

        detail_buttons.pack(
            fill="x"
        )


        ttk.Button(
            detail_buttons,
            text="Add Manual Item",
            command=self.add_manual_item
        ).pack(
            side="left"
        )


        ttk.Button(
            detail_buttons,
            text="Edit Selected Item",
            command=self.edit_invoice_item
        ).pack(
            side="left",
            padx=6
        )


        ttk.Button(
            detail_buttons,
            text="Recalculate",
            command=self.recalculate_selected_invoice
        ).pack(
            side="left"
        )


        ttk.Button(
            detail_buttons,
            text="Show Item Spots",
            command=self.show_item_spots
        ).pack(
            side="left",
            padx=6
        )


        #
        # Status bar.
        #

        self.status_var = tk.StringVar(
            value="Ready."
        )


        ttk.Label(
            self,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding=4
        ).pack(
            fill="x",
            side="bottom"
        )


    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------


    def load_customers(self):

        self.customers = fetch_customers()

        values = [

            f"{row['id']} - {row['company_name']}"

            for row in self.customers
        ]


        self.customer_combo["values"] = values


        if values:

            self.customer_combo.current(0)

            self.customer_changed()

        else:

            self.customer_var.set("")

            self.contract_combo["values"] = ()

            self.clear_contract_area()


    def customer_changed(
        self,
        event=None
    ):

        index = self.customer_combo.current()

        if index < 0:

            return


        self.selected_customer_id = (
            self.customers[index]["id"]
        )


        self.contracts = fetch_contracts(
            self.selected_customer_id
        )


        values = []


        for row in self.contracts:

            number = (
                row["contract_number"]
                or "(no number)"
            )

            description = (
                row["description"]
                or ""
            )


            values.append(
                f"{row['id']} - {number} - {description}"
            )


        self.contract_combo["values"] = values


        if values:

            self.contract_combo.current(0)

            self.contract_changed()

        else:

            self.contract_var.set("")

            self.clear_contract_area()


        self.load_invoices()


    def contract_changed(
        self,
        event=None
    ):

        index = self.contract_combo.current()

        if index < 0:

            return


        self.selected_contract_id = (
            self.contracts[index]["id"]
        )


        self.load_contract_information()

        self.load_contract_items()

        self.load_invoices()


    def load_contract_information(self):

        if self.selected_contract_id is None:

            self.contract_info_var.set(
                "Select a contract."
            )

            return


        contract = fetch_contract(
            self.selected_contract_id
        )


        if contract is None:

            self.contract_info_var.set(
                "Contract not found."
            )

            return


        customer_name = fetch_customer_name(
            contract["customer_id"]
        )


        self.contract_info_var.set(
            f"Customer: {customer_name}\n"
            f"Contract: "
            f"{contract['contract_number'] or '(no number)'}\n"
            f"Description: "
            f"{contract['description'] or ''}\n"
            f"Status: {contract['status']}    "
            f"Flight: "
            f"{contract['start_date'] or '-'} "
            f"through "
            f"{contract['end_date'] or '-'}"
        )


    def load_contract_items(self):

        self.item_tree.delete(
            *self.item_tree.get_children()
        )


        self.selected_contract_item_id = None


        self.clear_spots()


        if self.selected_contract_id is None:

            return


        self.contract_items = fetch_contract_items(
            self.selected_contract_id
        )
        
        #
        # Automatically select the first contract item.
        #
        if self.contract_items:

            self.selected_contract_item_id = (
                self.contract_items[0]["id"]
            )


        for row in self.contract_items:

            counts = fetch_spot_counts(
                row["id"]
            )


            unbilled = len(
                get_unbilled_completed_spots(
                    row["id"]
                )
            )


            self.item_tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(

                    row["id"],

                    row["commercial_title"],

                    row["description"],

                    row["quantity"],

                    row["pricing_type"],

                    money(row["unit_price"]),

                    money(row["total_price"]),

                    row["spot_length_seconds"],

                    counts["Scheduled"],

                    counts["Exported"],

                    counts["Completed"],

                    unbilled,
                )
            )

        if self.contract_items:

            first_item_id = str(
                self.contract_items[0]["id"]
            )

            self.item_tree.selection_set(
                first_item_id
            )

            self.item_tree.focus(
                first_item_id
            )

            self.item_tree.see(
                first_item_id
            )

            self.load_contract_item_spots()


        self.status_var.set(
            f"{len(self.contract_items)} "
            f"contract item(s) loaded."
        )


    def load_invoices(self):

        self.invoice_tree.delete(
            *self.invoice_tree.get_children()
        )


        self.invoice_item_tree.delete(
            *self.invoice_item_tree.get_children()
        )


        self.selected_invoice_id = None
        self.selected_invoice_item_id = None


        self.invoice_info.set(
            "Select an invoice."
        )


        if self.selected_customer_id is None:

            return


        rows = list_invoices(
            customer_id=self.selected_customer_id,
            contract_id=self.selected_contract_id,
        )


        for row in rows:

            self.invoice_tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(

                    row["id"],

                    row["invoice_number"],

                    row["invoice_date"],

                    row["due_date"] or "",

                    row["status"],

                    money(row["subtotal"]),

                    money(row["tax"]),

                    money(row["total"]),
                )
            )


        self.status_var.set(
            f"{len(rows)} invoice(s) loaded."
        )


    def clear_contract_area(self):

        self.item_tree.delete(
            *self.item_tree.get_children()
        )

        self.invoice_tree.delete(
            *self.invoice_tree.get_children()
        )

        self.invoice_item_tree.delete(
            *self.invoice_item_tree.get_children()
        )


        self.clear_spots()


        self.selected_contract_id = None
        self.selected_contract_item_id = None
        self.selected_invoice_id = None
        self.selected_invoice_item_id = None


        self.contract_info_var.set(
            "Select a contract."
        )


        self.invoice_info.set(
            "Select an invoice."
        )


    def refresh_all(self):

        customer_id = self.selected_customer_id
        contract_id = self.selected_contract_id
        item_id = self.selected_contract_item_id
        invoice_id = self.selected_invoice_id


        self.load_customers()


        #
        # Try to restore the previous customer.
        #

        if customer_id is not None:

            for index, row in enumerate(
                self.customers
            ):

                if row["id"] == customer_id:

                    self.customer_combo.current(
                        index
                    )

                    self.customer_changed()

                    break


        #
        # Try to restore the previous contract.
        #

        if contract_id is not None:

            for index, row in enumerate(
                self.contracts
            ):

                if row["id"] == contract_id:

                    self.contract_combo.current(
                        index
                    )

                    self.contract_changed()

                    break


        #
        # Try to restore the previous item.
        #

        if item_id is not None:

            iid = str(item_id)

            if iid in self.item_tree.get_children():

                self.item_tree.selection_set(
                    iid
                )

                self.item_tree.focus(
                    iid
                )

                self.item_tree.see(
                    iid
                )

                self.selected_contract_item_id = (
                    item_id
                )

                self.load_contract_item_spots()


        #
        # Try to restore invoice selection.
        #

        if invoice_id is not None:

            self.select_invoice(
                invoice_id
            )


    # ------------------------------------------------------------------
    # Contract item selection
    # ------------------------------------------------------------------


    def contract_item_selected(
        self,
        event=None
    ):

        selected = (
            self.item_tree.selection()
        )


        if not selected:

            self.selected_contract_item_id = None

            self.clear_spots()

            return


        self.selected_contract_item_id = int(
            selected[0]
        )


        self.load_contract_item_spots()


    # ------------------------------------------------------------------
    # Spot area
    # ------------------------------------------------------------------


    def clear_spots(self):

        self.spot_tree.delete(
            *self.spot_tree.get_children()
        )


        self.selected_spot_id = None


        self.spot_summary_var.set(
            "Select a contract item."
        )


    def load_contract_item_spots(self):

        self.spot_tree.delete(
            *self.spot_tree.get_children()
        )


        self.selected_spot_id = None


        if self.selected_contract_item_id is None:

            self.spot_summary_var.set(
                "Select a contract item."
            )

            return


        counts = fetch_spot_counts(
            self.selected_contract_item_id
        )


        unbilled = len(
            get_unbilled_completed_spots(
                self.selected_contract_item_id
            )
        )


        self.spot_summary_var.set(
            f"Pending: {counts['Pending']}    "
            f"Scheduled: {counts['Scheduled']}    "
            f"Exported: {counts['Exported']}    "
            f"Completed: {counts['Completed']}    "
            f"Cancelled: {counts['Cancelled']}    "
            f"Unbilled Completed: {unbilled}"
        )


        spots = fetch_contract_item_spots(
            self.selected_contract_item_id
        )


        #
        # Determine which spots are already billed.
        #
        # We do this using the invoice_item_spots table rather
        # than introducing billing state into spots.
        #

        billed_ids = set()


        connection = get_connection()
        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                iis.spot_id

            FROM invoice_item_spots iis

            INNER JOIN invoice_items ii
                ON iis.invoice_item_id = ii.id

            INNER JOIN invoices i
                ON ii.invoice_id = i.id

            WHERE
                iis.active = 1

                AND iis.spot_id IN (
                    SELECT id
                    FROM spots
                    WHERE contract_item_id = ?
                )

                AND i.status != 'Void'
            """,
            (
                self.selected_contract_item_id,
            )
        )


        billed_rows = cursor.fetchall()

        connection.close()


        for row in billed_rows:

            billed_ids.add(
                row["spot_id"]
            )


        for spot in spots:

            billed = (
                "Yes"
                if spot["id"] in billed_ids
                else ""
            )


            self.spot_tree.insert(
                "",
                "end",
                iid=str(spot["id"]),
                values=(

                    spot["id"],

                    spot["air_date"] or "",

                    spot["air_time"] or "",

                    spot["cart_number"] or "",

                    spot["title"] or "",

                    spot["status"] or "",

                    spot["actual_air_time"] or "",

                    billed,
                )
            )


        self.status_var.set(
            f"{len(spots)} spot(s) loaded "
            f"for contract item "
            f"{self.selected_contract_item_id}."
        )


    def spot_selected(
        self,
        event=None
    ):

        selected = (
            self.spot_tree.selection()
        )


        if not selected:

            self.selected_spot_id = None

            return


        #
        # The GUI allows multiple selection.
        #
        # Keep the first selected ID as the convenience
        # single-selection value.
        #

        self.selected_spot_id = int(
            selected[0]
        )



    # ------------------------------------------------------------------
    # Invoice operations
    # ------------------------------------------------------------------


    def new_invoice(self):

        if self.selected_customer_id is None:

            messagebox.showerror(
                "Invoice",
                "Select a customer first."
            )

            return


        contract_id = (
            self.selected_contract_id
        )


        dialog = SimpleDialog(
            self,
            "New Draft Invoice",
            [
                (
                    "Due date",
                    ""
                ),

                (
                    "Notes",
                    ""
                ),
            ]
        )


        if dialog.result is None:

            return



        try:

            invoice_id = create_invoice(
                customer_id=(
                    self.selected_customer_id
                ),

                invoice_number=None,

                invoice_date=None,

                due_date=(
                    dialog.result[0].strip()
                    or None
                ),

                contract_id=(
                    contract_id
                ),

                status="Draft",

                notes=(
                    dialog.result[1].strip()
                    or None
                ),
            )


        except Exception as exc:

            messagebox.showerror(
                "Create Invoice",
                str(exc)
            )

            return


        self.load_invoices()

        self.select_invoice(
            invoice_id
        )


        self.status_var.set(
            f"Draft invoice {invoice_id} created."
        )


    def invoice_selected(
        self,
        event=None
    ):

        selected = (
            self.invoice_tree.selection()
        )


        if not selected:

            return


        self.selected_invoice_id = int(
            selected[0]
        )


        self.load_invoice_detail()


    def select_invoice(
        self,
        invoice_id
    ):

        iid = str(
            invoice_id
        )


        if iid not in (
            self.invoice_tree.get_children()
        ):

            return


        self.invoice_tree.selection_set(
            iid
        )

        self.invoice_tree.focus(
            iid
        )

        self.invoice_tree.see(
            iid
        )


        self.selected_invoice_id = (
            invoice_id
        )


        self.load_invoice_detail()


    def load_invoice_detail(self):

        self.invoice_item_tree.delete(
            *self.invoice_item_tree.get_children()
        )


        self.selected_invoice_item_id = None


        if self.selected_invoice_id is None:

            self.invoice_info.set(
                "Select an invoice."
            )

            return


        invoice = get_invoice(
            self.selected_invoice_id
        )


        if invoice is None:

            self.invoice_info.set(
                "Invoice not found."
            )

            return


        self.invoice_info.set(
            f"Invoice {invoice['invoice_number'] or '(Draft)'}    "
            f"Status: {invoice['status']}    "
            f"Date: {invoice['invoice_date'] or '-'}    "
            f"Due: {invoice['due_date'] or '-'}    "
            f"Subtotal: {money(invoice['subtotal'])}    "
            f"Tax: {money(invoice['tax'])}    "
            f"Total: {money(invoice['total'])}"
        )


        items = list_invoice_items(
            self.selected_invoice_id
        )


        for item in items:

            spots = list_invoice_item_spots(
                item["id"]
            )


            self.invoice_item_tree.insert(
                "",
                "end",
                iid=str(item["id"]),
                values=(

                    item["id"],

                    item["description"],

                    item["quantity"],

                    money(item["unit_price"]),

                    money(item["amount"]),

                    len(spots),
                )
            )


    def recalculate_selected_invoice(self):

        if self.selected_invoice_id is None:

            messagebox.showinfo(
                "Recalculate",
                "Select an invoice first."
            )

            return


        invoice = get_invoice(
            self.selected_invoice_id
        )


        if invoice is None:

            return


        dialog = SimpleDialog(
            self,
            "Invoice Tax",
            [
                (
                    "Tax in dollars",
                    (
                        f"{invoice['tax'] / 100:.2f}"
                        if invoice["tax"] is not None
                        else "0.00"
                    )
                ),
            ]
        )


        if dialog.result is None:

            return


        try:

            tax = cents_from_text(
                dialog.result[0]
            )


            if tax is None:

                tax = 0


            recalculate_invoice_totals(
                self.selected_invoice_id,
                tax=tax
            )


        except Exception as exc:

            messagebox.showerror(
                "Recalculate",
                str(exc)
            )

            return


        invoice_id = self.selected_invoice_id

        self.load_invoices()

        self.select_invoice(
            invoice_id
        )


        self.status_var.set(
            "Invoice totals recalculated."
        )


    # ------------------------------------------------------------------
    # Invoice item operations
    # ------------------------------------------------------------------


    def invoice_item_selected(
        self,
        event=None
    ):

        selected = (
            self.invoice_item_tree.selection()
        )


        if not selected:

            self.selected_invoice_item_id = None

            return


        self.selected_invoice_item_id = int(
            selected[0]
        )


    def add_manual_item(self):

        if self.selected_invoice_id is None:

            messagebox.showerror(
                "Invoice Item",
                "Select an invoice first."
            )

            return

        invoice_id = self.selected_invoice_id

        selected_contract_item = None


        if self.selected_contract_item_id is not None:

            for row in self.contract_items:

                if (
                    row["id"]
                    == self.selected_contract_item_id
                ):

                    selected_contract_item = row

                    break


        defaults = [

            (
                "Description",

                (
                    selected_contract_item["description"]

                    if selected_contract_item

                    else ""
                )
            ),

            (
                "Quantity",
                "1"
            ),

            (
                "Unit price in dollars",

                (
                    f"{selected_contract_item['unit_price'] / 100:.2f}"

                    if (
                        selected_contract_item

                        and
                        selected_contract_item["unit_price"]
                        is not None
                    )

                    else ""
                )
            ),
        ]


        dialog = SimpleDialog(
            self,
            "Add Invoice Item",
            defaults
        )


        if dialog.result is None:

            return


        try:

            description = (
                dialog.result[0].strip()
            )


            quantity = float(
                dialog.result[1].strip()
            )


            unit_price = cents_from_text(
                dialog.result[2]
            )


            if not description:

                raise ValueError(
                    "Description is required."
                )


            if quantity <= 0:

                raise ValueError(
                    "Quantity must be greater than zero."
                )


            if unit_price is None:

                raise ValueError(
                    "Unit price is required."
                )


            item_id = add_invoice_item(
                invoice_id=(
                    self.selected_invoice_id
                ),

                contract_item_id=(

                    self.selected_contract_item_id

                    if selected_contract_item

                    else None
                ),

                description=(
                    description
                ),

                quantity=(
                    quantity
                ),

                unit_price=(
                    unit_price
                ),
            )


            invoice = get_invoice(
                self.selected_invoice_id
            )


            recalculate_invoice_totals(
                self.selected_invoice_id,
                tax=invoice["tax"]
            )


        except Exception as exc:

            messagebox.showerror(
                "Add Invoice Item",
                str(exc)
            )

            return


        self.load_invoices()

        self.select_invoice(
            invoice_id
        )


        self.status_var.set(
            f"Invoice item {item_id} created."
        )


    def edit_invoice_item(self):

        if self.selected_invoice_item_id is None:

            messagebox.showinfo(
                "Invoice Item",
                "Select an invoice item first."
            )

            return

        invoice_id = self.selected_invoice_id

        item = get_invoice_item(
            self.selected_invoice_item_id
        )


        if item is None:

            return


        dialog = SimpleDialog(
            self,
            "Edit Invoice Item",
            [
                (
                    "Description",
                    item["description"]
                ),

                (
                    "Quantity",
                    str(item["quantity"])
                ),

                (
                    "Unit price in dollars",

                    (
                        f"{item['unit_price'] / 100:.2f}"

                        if item["unit_price"]
                        is not None

                        else ""
                    )
                ),
            ]
        )


        if dialog.result is None:

            return


        try:

            description = (
                dialog.result[0].strip()
            )


            quantity = float(
                dialog.result[1].strip()
            )


            unit_price = cents_from_text(
                dialog.result[2]
            )


            if not description:

                raise ValueError(
                    "Description is required."
                )


            if quantity <= 0:

                raise ValueError(
                    "Quantity must be greater than zero."
                )


            if unit_price is None:

                raise ValueError(
                    "Unit price is required."
                )


            update_invoice_item(
                self.selected_invoice_item_id,

                description=(
                    description
                ),

                quantity=(
                    quantity
                ),

                unit_price=(
                    unit_price
                ),
            )


            invoice = get_invoice(
                self.selected_invoice_id
            )


            recalculate_invoice_totals(
                self.selected_invoice_id,
                tax=invoice["tax"]
            )


        except Exception as exc:

            messagebox.showerror(
                "Edit Invoice Item",
                str(exc)
            )

            return


        self.load_invoices()

        self.select_invoice(
            invoice_id
        )


        self.status_var.set(
            "Invoice item updated."
        )


    def show_item_spots(self):

        if self.selected_invoice_item_id is None:

            messagebox.showinfo(
                "Invoice Item Spots",
                "Select an invoice item first."
            )

            return


        spots = list_invoice_item_spots(
            self.selected_invoice_item_id
        )


        win = tk.Toplevel(
            self
        )


        win.title(
            (
                f"Invoice Item "
                f"{self.selected_invoice_item_id} Spots"
            )
        )


        win.geometry(
            "850x450"
        )


        columns = (
            "id",
            "date",
            "time",
            "status",
            "active",
        )


        tree = ttk.Treeview(
            win,
            columns=columns,
            show="headings"
        )


        for column, heading, width in (

            (
                "id",
                "Spot ID",
                80
            ),

            (
                "date",
                "Air Date",
                120
            ),

            (
                "time",
                "Air Time",
                100
            ),

            (
                "status",
                "Status",
                100
            ),

            (
                "active",
                "Billing Active",
                120
            ),
        ):

            tree.heading(
                column,
                text=heading
            )

            tree.column(
                column,
                width=width
            )


        tree.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )


        for spot in spots:

            tree.insert(
                "",
                "end",
                values=(

                    spot["id"],

                    spot["air_date"],

                    spot["air_time"],

                    spot["status"],

                    (
                        "Yes"
                        if spot["active"]
                        else "No"
                    ),
                )
            )


    # ------------------------------------------------------------------
    # Postpaid billing
    # ------------------------------------------------------------------


    def create_postpaid(self):

        if self.selected_customer_id is None:

            messagebox.showerror(
                "Postpaid Invoice",
                "Select a customer first."
            )

            return


        if self.selected_contract_id is None:

            messagebox.showerror(
                "Postpaid Invoice",
                "Select a contract first."
            )

            return


        #
        # Show the user what is about to be billed.
        #

        billable = []


        for item in self.contract_items:

            spots = get_unbilled_completed_spots(
                item["id"]
            )


            if spots:

                billable.append(
                    (
                        item,
                        spots
                    )
                )


        if not billable:

            messagebox.showinfo(
                "Postpaid Invoice",
                (
                    "There are no completed, "
                    "unbilled spots for this contract."
                )
            )

            return


        total_spots = sum(
            len(spots)
            for item, spots in billable
        )


        preview_lines = []


        for item, spots in billable:

            preview_lines.append(
                (
                    f"{item['commercial_title'] or item['description']}"
                    f": {len(spots)} spot(s)"
                )
            )


        preview = (
            "The invoice will include:\n\n"
            + "\n".join(preview_lines)
            + "\n\n"
            f"Total billable spots: {total_spots}"
        )


        confirmed = messagebox.askyesno(
            "Create Postpaid Invoice",
            preview
            + "\n\nContinue?"
        )


        if not confirmed:

            return


        dialog = SimpleDialog(
            self,
            "Create Postpaid Invoice",
            [
                (
                    "Invoice number",
                    ""
                ),

                (
                    "Invoice date",
                    str(date.today())
                ),

                (
                    "Due date",
                    ""
                ),

                (
                    "Tax in dollars",
                    "0.00"
                ),

                (
                    "Notes",
                    ""
                ),
            ]
        )


        if dialog.result is None:

            return


        invoice_number = (
            dialog.result[0].strip()
        )


        if not invoice_number:

            messagebox.showerror(
                "Postpaid Invoice",
                "Invoice number is required."
            )

            return


        try:

            tax = cents_from_text(
                dialog.result[3]
            )


            if tax is None:

                tax = 0


            invoice_id = create_postpaid_invoice(

                customer_id=(
                    self.selected_customer_id
                ),

                contract_id=(
                    self.selected_contract_id
                ),

                invoice_number=(
                    invoice_number
                ),

                invoice_date=(
                    dialog.result[1].strip()
                ),

                due_date=(
                    dialog.result[2].strip()
                    or None
                ),

                notes=(
                    dialog.result[4].strip()
                    or None
                ),

                tax=tax,
            )


            if invoice_id is None:

                messagebox.showinfo(
                    "Postpaid Invoice",
                    (
                        "There are no completed, "
                        "unbilled spots for this contract."
                    )
                )

                return


        except Exception as exc:

            messagebox.showerror(
                "Postpaid Invoice",
                str(exc)
            )

            return


        self.load_contract_items()

        self.load_invoices()

        self.select_invoice(
            invoice_id
        )


        self.status_var.set(
            (
                f"Postpaid invoice "
                f"{invoice_id} created from "
                f"{total_spots} completed spot(s)."
            )
        )


# ----------------------------------------------------------------------
# Simple modal dialog
# ----------------------------------------------------------------------


class SimpleDialog(
    tk.Toplevel
):

    def __init__(
        self,
        parent,
        title,
        fields
    ):

        super().__init__(
            parent
        )


        self.title(
            title
        )


        self.result = None


        self.transient(
            parent
        )


        self.grab_set()


        frame = ttk.Frame(
            self,
            padding=12
        )


        frame.pack(
            fill="both",
            expand=True
        )


        self.entries = []


        for row, (
            label,
            value
        ) in enumerate(
            fields
        ):

            ttk.Label(
                frame,
                text=label + ":"
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 10),
                pady=4
            )


            entry = ttk.Entry(
                frame,
                width=42
            )


            entry.insert(
                0,
                value
            )


            entry.grid(
                row=row,
                column=1,
                sticky="ew",
                pady=4
            )


            self.entries.append(
                entry
            )


        frame.columnconfigure(
            1,
            weight=1
        )


        buttons = ttk.Frame(
            frame
        )


        buttons.grid(
            row=len(fields),
            column=0,
            columnspan=2,
            sticky="e",
            pady=(10, 0)
        )


        ttk.Button(
            buttons,
            text="Cancel",
            command=self.cancel
        ).pack(
            side="right",
            padx=(6, 0)
        )


        ttk.Button(
            buttons,
            text="OK",
            command=self.ok
        ).pack(
            side="right"
        )


        self.protocol(
            "WM_DELETE_WINDOW",
            self.cancel
        )


        self.bind(
            "<Return>",
            lambda event: self.ok()
        )


        self.bind(
            "<Escape>",
            lambda event: self.cancel()
        )


        if self.entries:

            self.entries[0].focus_set()


        self.wait_window()


    def ok(self):

        self.result = [

            entry.get()

            for entry in self.entries
        ]


        self.destroy()


    def cancel(self):

        self.result = None

        self.destroy()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


if __name__ == "__main__":

    app = BillingBoard()

    app.mainloop()