#!/usr/bin/env python3

#
# prototype/billing_board.py
#
# Throwaway GUI for exercising the billing layer.
#
# This is intentionally a prototype.  It does not try to replace
# the eventual billing/AR GUI.
#
# It is designed to let us exercise the billing workflow that exists
# today, including the contract-item quantity/pricing fields that the
# normal contract GUI does not yet expose.
#

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


import os
import sys

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
    list_invoice_item_spots,
    create_postpaid_invoice,
)


# ----------------------------------------------------------------------
# Formatting helpers
# ----------------------------------------------------------------------


def money(cents):
    """Display integer cents as dollars."""
    if cents is None:
        return ""
    return f"${cents / 100:,.2f}"


def cents_from_text(value):
    """
    Convert a dollar entry such as 25 or 25.00 into integer cents.

    Also accepts an integer-looking cents value when the caller
    explicitly prefixes it with 'cents:'.
    """
    value = value.strip()

    if not value:
        return None

    if value.lower().startswith("cents:"):
        return int(value[6:].strip())

    value = value.replace("$", "").replace(",", "")

    # Avoid floating point for money.
    from decimal import Decimal, ROUND_HALF_UP

    return int(
        (Decimal(value) * Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


# ----------------------------------------------------------------------
# Database reads used by this prototype
# ----------------------------------------------------------------------


def fetch_customers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, company_name
        FROM customers
        WHERE active = 1
        ORDER BY company_name
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_contracts(customer_id=None):
    conn = get_connection()
    cur = conn.cursor()

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
    params = []

    if customer_id is not None:
        sql += " AND c.customer_id = ?"
        params.append(customer_id)

    sql += " ORDER BY c.contract_number, c.id"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_contract_items(contract_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
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
        FROM contract_items
        WHERE contract_id = ?
        ORDER BY id
        """,
        (contract_id,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_customer_name(customer_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT company_name FROM customers WHERE id = ?",
        (customer_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row["company_name"] if row else ""


def fetch_contract(contract_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM contracts
        WHERE id = ?
        """,
        (contract_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


# ----------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------


class BillingBoard(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("zbTraffic Billing Board - Prototype")
        self.geometry("1250x820")
        self.minsize(1050, 700)

        self.customers = []
        self.contracts = []
        self.contract_items = []

        self.selected_customer_id = None
        self.selected_contract_id = None
        self.selected_contract_item_id = None
        self.selected_invoice_id = None
        self.selected_invoice_item_id = None

        self.build_ui()
        self.load_customers()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def build_ui(self):

        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(
            top,
            text="Customer:"
        ).pack(side="left")

        self.customer_var = tk.StringVar()
        self.customer_combo = ttk.Combobox(
            top,
            textvariable=self.customer_var,
            state="readonly",
            width=32,
        )
        self.customer_combo.pack(side="left", padx=(5, 15))
        self.customer_combo.bind(
            "<<ComboboxSelected>>",
            self.customer_changed,
        )

        ttk.Label(
            top,
            text="Contract:"
        ).pack(side="left")

        self.contract_var = tk.StringVar()
        self.contract_combo = ttk.Combobox(
            top,
            textvariable=self.contract_var,
            state="readonly",
            width=35,
        )
        self.contract_combo.pack(side="left", padx=5)
        self.contract_combo.bind(
            "<<ComboboxSelected>>",
            self.contract_changed,
        )

        ttk.Button(
            top,
            text="Refresh",
            command=self.refresh_all,
        ).pack(side="right")

        # --------------------------------------------------------------
        # Contract / contract item area
        # --------------------------------------------------------------

        contract_frame = ttk.LabelFrame(
            self,
            text="Contract Items",
            padding=6,
        )
        contract_frame.pack(
            fill="both",
            expand=False,
            padx=8,
            pady=(0, 6),
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
            "billable",
        )

        self.item_tree = ttk.Treeview(
            contract_frame,
            columns=item_columns,
            show="headings",
            height=7,
        )

        headings = {
            "id": "ID",
            "title": "Commercial",
            "description": "Description",
            "quantity": "Qty",
            "pricing": "Pricing",
            "unit": "Unit Price",
            "total": "Total Price",
            "length": "Length",
            "billable": "Unbilled",
        }

        widths = {
            "id": 50,
            "title": 180,
            "description": 220,
            "quantity": 60,
            "pricing": 85,
            "unit": 90,
            "total": 90,
            "length": 65,
            "billable": 75,
        }

        for col in item_columns:
            self.item_tree.heading(col, text=headings[col])
            self.item_tree.column(
                col,
                width=widths[col],
                anchor="center" if col not in ("title", "description") else "w",
            )

        self.item_tree.pack(fill="x", expand=True)
        self.item_tree.bind(
            "<<TreeviewSelect>>",
            self.contract_item_selected,
        )

        item_buttons = ttk.Frame(contract_frame)
        item_buttons.pack(fill="x", pady=(5, 0))

        ttk.Button(
            item_buttons,
            text="Refresh Contract Items",
            command=self.load_contract_items,
        ).pack(side="left")

        ttk.Button(
            item_buttons,
            text="Create Postpaid Invoice",
            command=self.create_postpaid,
        ).pack(side="left", padx=8)

        ttk.Label(
            item_buttons,
            text=(
                "Contract-item pricing is shown here because the "
                "current contract GUI does not edit these fields."
            ),
        ).pack(side="left", padx=10)

        # --------------------------------------------------------------
        # Main invoice area
        # --------------------------------------------------------------

        invoice_frame = ttk.Frame(self, padding=8)
        invoice_frame.pack(fill="both", expand=True)

        left = ttk.LabelFrame(
            invoice_frame,
            text="Invoices",
            padding=6,
        )
        left.pack(side="left", fill="both", expand=True)

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
            left,
            columns=invoice_columns,
            show="headings",
            height=14,
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

        for col in invoice_columns:
            self.invoice_tree.heading(
                col,
                text=invoice_headings[col],
            )
            self.invoice_tree.column(
                col,
                width=invoice_widths[col],
                anchor="center",
            )

        self.invoice_tree.pack(fill="both", expand=True)
        self.invoice_tree.bind(
            "<<TreeviewSelect>>",
            self.invoice_selected,
        )

        invoice_buttons = ttk.Frame(left)
        invoice_buttons.pack(fill="x", pady=(6, 0))

        ttk.Button(
            invoice_buttons,
            text="New Draft Invoice",
            command=self.new_invoice,
        ).pack(side="left")

        ttk.Button(
            invoice_buttons,
            text="Refresh Invoices",
            command=self.load_invoices,
        ).pack(side="left", padx=6)

        # --------------------------------------------------------------
        # Invoice detail area
        # --------------------------------------------------------------

        right = ttk.LabelFrame(
            invoice_frame,
            text="Invoice Detail",
            padding=8,
        )
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        header = ttk.Frame(right)
        header.pack(fill="x")

        self.invoice_info = tk.StringVar(
            value="Select an invoice."
        )

        ttk.Label(
            header,
            textvariable=self.invoice_info,
            justify="left",
        ).pack(anchor="w")

        self.invoice_item_tree = ttk.Treeview(
            right,
            columns=(
                "id",
                "description",
                "quantity",
                "unit",
                "amount",
                "spots",
            ),
            show="headings",
            height=10,
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
            "unit": 80,
            "amount": 90,
            "spots": 60,
        }

        for col in detail_headings:
            self.invoice_item_tree.heading(
                col,
                text=detail_headings[col],
            )
            self.invoice_item_tree.column(
                col,
                width=detail_widths[col],
                anchor="center" if col != "description" else "w",
            )

        self.invoice_item_tree.pack(
            fill="both",
            expand=True,
            pady=(8, 6),
        )

        self.invoice_item_tree.bind(
            "<<TreeviewSelect>>",
            self.invoice_item_selected,
        )

        detail_buttons = ttk.Frame(right)
        detail_buttons.pack(fill="x")

        ttk.Button(
            detail_buttons,
            text="Add Manual Item",
            command=self.add_manual_item,
        ).pack(side="left")

        ttk.Button(
            detail_buttons,
            text="Edit Selected Item",
            command=self.edit_invoice_item,
        ).pack(side="left", padx=6)

        ttk.Button(
            detail_buttons,
            text="Recalculate",
            command=self.recalculate_selected_invoice,
        ).pack(side="left")

        ttk.Button(
            detail_buttons,
            text="Show Item Spots",
            command=self.show_item_spots,
        ).pack(side="left", padx=6)

        self.status_var = tk.StringVar(value="Ready.")

        ttk.Label(
            self,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding=4,
        ).pack(fill="x", side="bottom")

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

    def customer_changed(self, event=None):

        index = self.customer_combo.current()

        if index < 0:
            return

        self.selected_customer_id = self.customers[index]["id"]

        self.contracts = fetch_contracts(
            self.selected_customer_id
        )

        values = []

        for row in self.contracts:
            number = row["contract_number"] or "(no number)"
            description = row["description"] or ""
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

    def contract_changed(self, event=None):

        index = self.contract_combo.current()

        if index < 0:
            return

        self.selected_contract_id = self.contracts[index]["id"]

        self.load_contract_items()
        self.load_invoices()

    def load_contract_items(self):

        self.item_tree.delete(*self.item_tree.get_children())

        if self.selected_contract_id is None:
            return

        self.contract_items = fetch_contract_items(
            self.selected_contract_id
        )

        for row in self.contract_items:

            billable = len(
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
                    billable,
                ),
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
                ),
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

        self.selected_contract_id = None
        self.selected_invoice_id = None

    def refresh_all(self):

        self.load_customers()

    # ------------------------------------------------------------------
    # Contract item selection
    # ------------------------------------------------------------------

    def contract_item_selected(self, event=None):

        selected = self.item_tree.selection()

        if not selected:
            self.selected_contract_item_id = None
            return

        self.selected_contract_item_id = int(selected[0])

    # ------------------------------------------------------------------
    # Invoice operations
    # ------------------------------------------------------------------

    def new_invoice(self):

        if self.selected_customer_id is None:
            messagebox.showerror(
                "Invoice",
                "Select a customer first.",
            )
            return

        contract_id = self.selected_contract_id

        dialog = SimpleDialog(
            self,
            "New Draft Invoice",
            [
                ("Invoice number", ""),
                ("Invoice date", str(date.today())),
                ("Due date", ""),
                ("Notes", ""),
            ],
        )

        if dialog.result is None:
            return

        invoice_number = dialog.result[0].strip()

        if not invoice_number:
            messagebox.showerror(
                "Invoice",
                "Invoice number is required.",
            )
            return

        try:
            invoice_id = create_invoice(
                customer_id=self.selected_customer_id,
                invoice_number=invoice_number,
                invoice_date=dialog.result[1].strip(),
                due_date=dialog.result[2].strip() or None,
                contract_id=contract_id,
                status="Draft",
                notes=dialog.result[3].strip() or None,
            )

        except Exception as exc:
            messagebox.showerror(
                "Create Invoice",
                str(exc),
            )
            return

        self.load_invoices()
        self.select_invoice(invoice_id)

    def invoice_selected(self, event=None):

        selected = self.invoice_tree.selection()

        if not selected:
            return

        self.selected_invoice_id = int(selected[0])
        self.load_invoice_detail()

    def select_invoice(self, invoice_id):

        iid = str(invoice_id)

        if iid in self.invoice_tree.get_children():
            self.invoice_tree.selection_set(iid)
            self.invoice_tree.focus(iid)
            self.invoice_tree.see(iid)
            self.selected_invoice_id = invoice_id
            self.load_invoice_detail()

    def load_invoice_detail(self):

        self.invoice_item_tree.delete(
            *self.invoice_item_tree.get_children()
        )

        if self.selected_invoice_id is None:
            self.invoice_info.set("Select an invoice.")
            return

        invoice = get_invoice(
            self.selected_invoice_id
        )

        if invoice is None:
            self.invoice_info.set("Invoice not found.")
            return

        self.invoice_info.set(
            f"Invoice {invoice['invoice_number']}   "
            f"Status: {invoice['status']}\n"
            f"Date: {invoice['invoice_date']}   "
            f"Due: {invoice['due_date'] or '-'}\n"
            f"Subtotal: {money(invoice['subtotal'])}   "
            f"Tax: {money(invoice['tax'])}   "
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
                ),
            )

    def recalculate_selected_invoice(self):

        if self.selected_invoice_id is None:
            messagebox.showinfo(
                "Recalculate",
                "Select an invoice first.",
            )
            return

        dialog = SimpleDialog(
            self,
            "Invoice Tax",
            [
                (
                    "Tax in dollars",
                    "0.00",
                ),
            ],
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
                tax=tax,
            )

        except Exception as exc:
            messagebox.showerror(
                "Recalculate",
                str(exc),
            )
            return

        self.load_invoices()
        self.select_invoice(
            self.selected_invoice_id
        )

    # ------------------------------------------------------------------
    # Invoice item operations
    # ------------------------------------------------------------------

    def invoice_item_selected(self, event=None):

        selected = self.invoice_item_tree.selection()

        if not selected:
            self.selected_invoice_item_id = None
            return

        self.selected_invoice_item_id = int(selected[0])

    def add_manual_item(self):

        if self.selected_invoice_id is None:
            messagebox.showerror(
                "Invoice Item",
                "Select an invoice first.",
            )
            return

        selected_contract_item = None

        if self.selected_contract_item_id is not None:
            for row in self.contract_items:
                if row["id"] == self.selected_contract_item_id:
                    selected_contract_item = row
                    break

        defaults = [
            (
                "Description",
                (
                    selected_contract_item["description"]
                    if selected_contract_item
                    else ""
                ),
            ),
            ("Quantity", "1"),
            (
                "Unit price in dollars",
                (
                    f"{selected_contract_item['unit_price'] / 100:.2f}"
                    if selected_contract_item
                    and selected_contract_item["unit_price"] is not None
                    else ""
                ),
            ),
        ]

        dialog = SimpleDialog(
            self,
            "Add Invoice Item",
            defaults,
        )

        if dialog.result is None:
            return

        try:
            description = dialog.result[0].strip()
            quantity = float(dialog.result[1].strip())
            unit_price = cents_from_text(dialog.result[2])

            if not description:
                raise ValueError(
                    "Description is required."
                )

            if unit_price is None:
                raise ValueError(
                    "Unit price is required."
                )

            item_id = add_invoice_item(
                invoice_id=self.selected_invoice_id,
                contract_item_id=(
                    self.selected_contract_item_id
                    if selected_contract_item
                    else None
                ),
                description=description,
                quantity=quantity,
                unit_price=unit_price,
            )

            recalculate_invoice_totals(
                self.selected_invoice_id,
                tax=(
                    get_invoice(
                        self.selected_invoice_id
                    )["tax"]
                ),
            )

        except Exception as exc:
            messagebox.showerror(
                "Add Invoice Item",
                str(exc),
            )
            return

        self.load_invoices()
        self.select_invoice(
            self.selected_invoice_id
        )

        self.status_var.set(
            f"Invoice item {item_id} created."
        )

    def edit_invoice_item(self):

        if self.selected_invoice_item_id is None:
            messagebox.showinfo(
                "Invoice Item",
                "Select an invoice item first.",
            )
            return

        item = get_invoice_item(
            self.selected_invoice_item_id
        )

        if item is None:
            return

        dialog = SimpleDialog(
            self,
            "Edit Invoice Item",
            [
                ("Description", item["description"]),
                ("Quantity", str(item["quantity"])),
                (
                    "Unit price in dollars",
                    (
                        f"{item['unit_price'] / 100:.2f}"
                        if item["unit_price"] is not None
                        else ""
                    ),
                ),
            ],
        )

        if dialog.result is None:
            return

        try:
            description = dialog.result[0].strip()
            quantity = float(dialog.result[1].strip())
            unit_price = cents_from_text(
                dialog.result[2]
            )

            if unit_price is None:
                raise ValueError(
                    "Unit price is required."
                )

            update_invoice_item(
                self.selected_invoice_item_id,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
            )

            invoice = get_invoice(
                self.selected_invoice_id
            )

            recalculate_invoice_totals(
                self.selected_invoice_id,
                tax=invoice["tax"],
            )

        except Exception as exc:
            messagebox.showerror(
                "Edit Invoice Item",
                str(exc),
            )
            return

        self.load_invoices()
        self.select_invoice(
            self.selected_invoice_id
        )

    def show_item_spots(self):

        if self.selected_invoice_item_id is None:
            messagebox.showinfo(
                "Invoice Item Spots",
                "Select an invoice item first.",
            )
            return

        spots = list_invoice_item_spots(
            self.selected_invoice_item_id
        )

        win = tk.Toplevel(self)
        win.title(
            f"Invoice Item {self.selected_invoice_item_id} Spots"
        )
        win.geometry("850x400")

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
            show="headings",
        )

        for col, heading, width in (
            ("id", "Spot ID", 80),
            ("date", "Air Date", 120),
            ("time", "Air Time", 100),
            ("status", "Status", 100),
            ("active", "Billing Active", 120),
        ):
            tree.heading(col, text=heading)
            tree.column(col, width=width)

        tree.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8,
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
                    "Yes" if spot["active"] else "No",
                ),
            )

    # ------------------------------------------------------------------
    # POSTPAID
    # ------------------------------------------------------------------

    def create_postpaid(self):

        if self.selected_customer_id is None:
            messagebox.showerror(
                "Postpaid Invoice",
                "Select a customer first.",
            )
            return

        if self.selected_contract_id is None:
            messagebox.showerror(
                "Postpaid Invoice",
                "Select a contract first.",
            )
            return

        dialog = SimpleDialog(
            self,
            "Create Postpaid Invoice",
            [
                (
                    "Invoice number",
                    "",
                ),
                (
                    "Invoice date",
                    str(date.today()),
                ),
                (
                    "Due date",
                    "",
                ),
                (
                    "Tax in dollars",
                    "0.00",
                ),
                (
                    "Notes",
                    "",
                ),
            ],
        )

        if dialog.result is None:
            return

        invoice_number = dialog.result[0].strip()

        if not invoice_number:
            messagebox.showerror(
                "Postpaid Invoice",
                "Invoice number is required.",
            )
            return

        try:
            tax = cents_from_text(
                dialog.result[3]
            )
            if tax is None:
                tax = 0

            invoice_id = create_postpaid_invoice(
                customer_id=self.selected_customer_id,
                contract_id=self.selected_contract_id,
                invoice_number=invoice_number,
                invoice_date=dialog.result[1].strip(),
                due_date=dialog.result[2].strip() or None,
                notes=dialog.result[4].strip() or None,
                tax=tax,
            )

            if invoice_id is None:
                messagebox.showinfo(
                    "Postpaid Invoice",
                    "There are no completed, unbilled spots "
                    "for this contract.",
                )
                return

        except Exception as exc:
            messagebox.showerror(
                "Postpaid Invoice",
                str(exc),
            )
            return

        self.load_contract_items()
        self.load_invoices()
        self.select_invoice(invoice_id)

        self.status_var.set(
            f"Postpaid invoice {invoice_id} created."
        )


# ----------------------------------------------------------------------
# Simple modal dialog
# ----------------------------------------------------------------------


class SimpleDialog(tk.Toplevel):

    def __init__(self, parent, title, fields):

        super().__init__(parent)

        self.title(title)
        self.result = None

        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        self.entries = []

        for row, (label, value) in enumerate(fields):

            ttk.Label(
                frame,
                text=label + ":",
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 10),
                pady=4,
            )

            entry = ttk.Entry(
                frame,
                width=42,
            )
            entry.insert(0, value)

            entry.grid(
                row=row,
                column=1,
                sticky="ew",
                pady=4,
            )

            self.entries.append(entry)

        frame.columnconfigure(1, weight=1)

        buttons = ttk.Frame(frame)
        buttons.grid(
            row=len(fields),
            column=0,
            columnspan=2,
            sticky="e",
            pady=(10, 0),
        )

        ttk.Button(
            buttons,
            text="Cancel",
            command=self.cancel,
        ).pack(side="right", padx=(6, 0))

        ttk.Button(
            buttons,
            text="OK",
            command=self.ok,
        ).pack(side="right")

        self.protocol(
            "WM_DELETE_WINDOW",
            self.cancel,
        )

        self.bind(
            "<Return>",
            lambda event: self.ok(),
        )

        self.bind(
            "<Escape>",
            lambda event: self.cancel(),
        )

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
