# File: prototype/met/contract_master_detail_gui_new.py - v5 updated for pricing_type + full field coverage
# - Supports contract_items: quantity, pricing_type (PER_SPOT/TOTAL), unit_price, total_price as cents <-> dollars
# - Full edit coverage for contracts and contract_items tables per create_database.py
# - Keeps 3-pane design, LIKE search for stopsets, Mon/Tue checkboxes
# - Pricing logic from traffic/billing.py

import sys
import pathlib
_HERE = pathlib.Path(__file__).resolve()
for _p in [_HERE.parent, *_HERE.parents]:
    if (_p / "traffic").is_dir():
        if str(_p) not in sys.path: sys.path.insert(0, str(_p))
        break

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from traffic.database import get_connection
from traffic.scheduler import schedule_contract_item_quantity

def now_str(): return datetime.now().isoformat(sep=' ', timespec='seconds')

# ---------- Billing helpers (from traffic/billing.py) ----------
def calculate_amount(quantity, unit_price_cents):
    """Calculate invoice amount in integer cents. quantity may be fractional, unit_price is integer cents."""
    if quantity is None or unit_price_cents is None:
        return 0
    return int(
        (Decimal(str(quantity)) * Decimal(unit_price_cents)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

def dollars_to_cents(s):
    if s is None: return None
    s = str(s).strip()
    if s == "" or s.lower() == "none": return None
    # allow $ sign
    s = s.replace("$","").replace(",","").strip()
    try:
        d = Decimal(s) * Decimal("100")
        return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except:
        return None

def cents_to_dollars(cents, allow_empty=True):
    if cents is None:
        return "" if allow_empty else "0.00"
    try:
        # For PER_SPOT total calc we want 2 decimals, for TOTAL unit calc we may want more
        return f"{(Decimal(cents) / Decimal('100')):.2f}"
    except:
        return ""

def cents_to_dollars_precise(cents, decimals=4):
    if cents is None:
        return ""
    try:
        fmt = f"{{:.{decimals}f}}"
        return fmt.format(float(Decimal(cents) / Decimal("100")))
    except:
        return ""

# ---------- Days helpers ----------
DAY_ORDER = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
DAY_TO_NUM = {name: i+1 for i, name in enumerate(DAY_ORDER)}
NUM_TO_DAY = {v:k for k,v in DAY_TO_NUM.items()}

def normalize_days_to_names(days_str):
    if not days_str: return ""
    parts = [p.strip() for p in days_str.replace(";",",").split(",") if p.strip()]
    result = []
    for p in parts:
        if p in DAY_ORDER: result.append(p)
        elif p.isdigit():
            n = int(p)
            if n == 0: n = 7
            if n in NUM_TO_DAY: result.append(NUM_TO_DAY[n])
        else:
            cap = p[:3].title()
            if cap in DAY_ORDER: result.append(cap)
    ordered = [d for d in DAY_ORDER if d in result]
    return ",".join(ordered)

# ---------- LIKE Searchable Combobox ----------
class DBSearchableCombobox(ttk.Frame):
    def __init__(self, parent, placeholder="-- Any / No Preference --", width=30, search_func=None):
        super().__init__(parent)
        self.placeholder = placeholder
        self.search_func = search_func
        self.id_to_label = {None: placeholder}
        self.var_text = tk.StringVar()
        self.var_id = None
        self.filtered = [(None, placeholder)]
        self.entry = ttk.Entry(self, textvariable=self.var_text, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn = ttk.Button(self, text="▼", width=3, command=self.toggle_list)
        self.btn.pack(side=tk.LEFT)
        self.listbox_frame = None
        self.listbox = None
        self._after_id = None
        self.entry.bind("<KeyRelease>", self.on_keyrelease)
        self.entry.bind("<FocusIn>", lambda e: self.show_list(initial=True))
        self.entry.bind("<FocusOut>", lambda e: self.after(150, self.hide_if_not_focused))

    def hide_if_not_focused(self):
        if self.listbox_frame:
            foc = self.focus_get()
            if foc not in (self.entry, self.listbox, self.btn): self.hide_list()

    def toggle_list(self):
        if self.listbox_frame and self.listbox_frame.winfo_ismapped(): self.hide_list()
        else: self.show_list(initial=True)

    def show_list(self, initial=False):
        if self.listbox_frame: self.listbox_frame.destroy()
        self.listbox_frame = tk.Toplevel(self)
        self.listbox_frame.wm_overrideredirect(True)
        self.listbox_frame.wm_attributes("-topmost", True)
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = self.entry.winfo_width() + self.btn.winfo_width()
        self.listbox_frame.geometry(f"{w}x200+{x}+{y}")
        self.listbox = tk.Listbox(self.listbox_frame, height=10)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        if initial and not self.var_text.get().strip():
            self.filtered = [(None, self.placeholder), (None, "Type 2+ letters to search...")]
        self.refresh()
        self.listbox.bind("<Double-Button-1>", self.on_select)
        self.listbox.bind("<Return>", self.on_select)

    def hide_list(self):
        if self.listbox_frame: self.listbox_frame.destroy(); self.listbox_frame = None; self.listbox = None

    def refresh(self):
        if not self.listbox: return
        self.listbox.delete(0, tk.END)
        for oid, label in self.filtered:
            disp = label if (oid is None and "Type" in label) else (f"{label}" if oid is None else f"{label} [{oid}]")
            self.listbox.insert(tk.END, disp)

    def on_keyrelease(self, e):
        if e.keysym in ("Up","Down","Return","Escape"):
            if e.keysym == "Escape": self.hide_list()
            return
        text = self.var_text.get().strip()
        if self._after_id: self.after_cancel(self._after_id)
        self._after_id = self.after(300, lambda: self.do_search(text))

    def do_search(self, text):
        if len(text) < 2:
            self.filtered = [(None, self.placeholder), (None, "Type 2+ letters to search...")]
            self.show_list(); self.refresh(); return
        try:
            results = self.search_func(text) if self.search_func else []
            self.filtered = [(None, self.placeholder)] + results[:100]
            self.id_to_label.update({oid: label for oid, label in results})
            self.show_list(); self.refresh()
        except Exception as ex:
            print(f"DBSearch error: {ex}")
            self.filtered = [(None, self.placeholder), (None, f"Error: {ex}")]
            self.show_list(); self.refresh()

    def on_select(self, e):
        if not self.listbox or not self.listbox.curselection(): return
        idx = self.listbox.curselection()[0]
        if idx >= len(self.filtered): return
        oid, label = self.filtered[idx]
        if label.startswith("Type"): return
        self.set_id(oid, label); self.hide_list(); self.entry.focus_set(); self.event_generate("<<DBSearchSelected>>")

    def get_id(self): return self.var_id
    def set_id(self, oid, label=None):
        self.var_id = oid
        if oid is None:
            self.var_text.set(self.placeholder if label is None else label)
        else:
            resolved = label or self.id_to_label.get(oid, str(oid))
            self.var_text.set(resolved)
        if oid is not None and label: self.id_to_label[oid] = label

    def set_resolved(self, oid, label):
        if oid is None: self.set_id(None)
        else:
            self.id_to_label[oid] = label
            self.set_id(oid, label)

class ScrolledTreeview(ttk.Frame):
    def __init__(self, parent, columns, height=5, **kwargs):
        super().__init__(parent)
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=height, **kwargs)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        for c in columns:
            self.tree.heading(c, text=c.replace("_"," ").title())
            w=90
            if c in ("description","company_name","commercial_title","contract_number","notes","customer","commercial","title"): w=160
            if c in ("id","active","quantity","priority","max_spots_per_day","max_spots_per_week","spot_length"): w=65
            if c in ("start_date","end_date","status","days_of_week","pricing_type","unit_price","total_price"): w=95
            if c in ("pref_program","pref_stopset"): w=120
            self.tree.column(c, width=w, minwidth=40, stretch=True)

class ContractMasterDetailGUI:
    def __init__(self, root):
        self.root = root
        root.title("zbTraffic - Contracts -> Items -> Rules (v5 pricing)")
        root.geometry("1450x960")
        self.customers = {}; self.salespeople = {}; self.stations = {}; self.commercials = {}
        self.programs = {}; self.programs_by_id = {}; self.stopsets_by_id = {}
        self.contract_cache = {}; self.item_cache = {}; self.rule_cache = {}
        self.selected_contract_id = None; self.selected_item_id = None
        self._pricing_recalc_lock = False
        self.build(); self.load_lookups(); self.load_contracts(); self.update_button_states()

    def build(self):
        ctrl = ttk.Frame(self.root); ctrl.pack(fill="x", padx=5, pady=2)
        ttk.Label(ctrl, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        entry = ttk.Entry(ctrl, textvariable=self.filter_var, width=22)
        entry.pack(side="left", padx=5); entry.bind("<Return>", lambda e: self.load_contracts())
        ttk.Button(ctrl, text="Search", command=self.load_contracts).pack(side="left", padx=2)
        ttk.Button(ctrl, text="Clear", command=lambda: [self.filter_var.set(""), self.load_contracts()]).pack(side="left", padx=2)
        ttk.Separator(ctrl, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(ctrl, text="Refresh All", command=self.refresh_all).pack(side="left", padx=2)
        self.status_var = tk.StringVar(value="Select a contract...")
        ttk.Label(self.root, textvariable=self.status_var, foreground="#0a58ca").pack(anchor="w", padx=5)

        paned_main = ttk.PanedWindow(self.root, orient="vertical")
        paned_main.pack(fill="both", expand=True, padx=5, pady=3)

        top_h_paned = ttk.PanedWindow(paned_main, orient="horizontal")
        paned_main.add(top_h_paned, weight=3)

        contract_frame = ttk.LabelFrame(top_h_paned, text="1. Contracts")
        top_h_paned.add(contract_frame, weight=2)
        items_frame = ttk.LabelFrame(top_h_paned, text="2. Items")
        top_h_paned.add(items_frame, weight=3)

        # Contracts tree
        contract_cols = ("id", "contract_number", "customer", "station", "salesperson", "status", "payment_timing", "start_date", "end_date", "active")
        self.contract_tree_wrap = ScrolledTreeview(contract_frame, contract_cols, height=7)
        self.contract_tree_wrap.pack(fill="both", expand=True, padx=2, pady=2)
        self.contract_tree = self.contract_tree_wrap.tree
        self.contract_tree.bind("<<TreeviewSelect>>", self.on_contract_select)

        # Contract form - full fields
        cf = ttk.Frame(contract_frame); cf.pack(fill="x", padx=2, pady=2)
        ttk.Label(cf, text="Cust:").grid(row=0, column=0, sticky="w")
        self.cust_cb = ttk.Combobox(cf, state="readonly", width=18); self.cust_cb.grid(row=0, column=1, padx=1)
        ttk.Label(cf, text="Sales:").grid(row=0, column=2, sticky="w")
        self.sales_cb = ttk.Combobox(cf, state="readonly", width=14); self.sales_cb.grid(row=0, column=3, padx=1)
        ttk.Label(cf, text="Sta:").grid(row=0, column=4, sticky="w")
        self.stat_cb = ttk.Combobox(cf, state="readonly", width=12); self.stat_cb.grid(row=0, column=5, padx=1)
        self.active_var = tk.IntVar(value=1)
        ttk.Checkbutton(cf, text="Act", variable=self.active_var).grid(row=0, column=6, padx=2)

        ttk.Label(cf, text="#:").grid(row=1, column=0, sticky="w")
        self.num_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.num_var, width=12).grid(row=1, column=1, padx=1, sticky="w")
        ttk.Label(cf, text="Sts:").grid(row=1, column=2, sticky="w")
        self.status_cb = ttk.Combobox(cf, values=["Draft","Active","Completed","Cancelled"], width=10)
        self.status_cb.grid(row=1, column=3, padx=1, sticky="w"); self.status_cb.set("Draft")
        ttk.Label(cf, text="Start:").grid(row=1, column=4, sticky="w")
        self.start_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.start_var, width=10).grid(row=1, column=5, padx=1, sticky="w")
        ttk.Label(cf, text="End:").grid(row=1, column=6, sticky="w")
        self.end_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.end_var, width=10).grid(row=1, column=7, padx=1, sticky="w")

        # NEW row: payment_timing, payment_terms, description
        ttk.Label(cf, text="Pay:").grid(row=2, column=0, sticky="w")
        self.payment_timing_cb = ttk.Combobox(cf, values=["POSTPAID","PREPAID"], width=10, state="readonly")
        self.payment_timing_cb.grid(row=2, column=1, padx=1, sticky="w"); self.payment_timing_cb.set("POSTPAID")
        ttk.Label(cf, text="Terms days:").grid(row=2, column=2, sticky="w")
        self.payment_terms_var = tk.StringVar(value="30")
        ttk.Entry(cf, textvariable=self.payment_terms_var, width=6).grid(row=2, column=3, padx=1, sticky="w")
        ttk.Label(cf, text="Desc:").grid(row=2, column=4, sticky="w")
        self.contract_desc_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.contract_desc_var, width=26).grid(row=2, column=5, columnspan=3, padx=1, sticky="we")

        ttk.Label(cf, text="Notes:").grid(row=3, column=0, sticky="w")
        self.contract_notes_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.contract_notes_var, width=58).grid(row=3, column=1, columnspan=7, padx=1, sticky="we", pady=1)

        btn_cf = ttk.Frame(contract_frame); btn_cf.pack(fill="x", padx=2, pady=1)
        ttk.Button(btn_cf, text="New", command=self.clear_contract_form).pack(side="left", padx=1)
        ttk.Button(btn_cf, text="Add", command=self.add_contract).pack(side="left", padx=2)
        ttk.Button(btn_cf, text="Update", command=self.update_contract).pack(side="left", padx=1)
        ttk.Button(btn_cf, text="Toggle Act", command=self.toggle_contract_active).pack(side="left", padx=8)

        # Items tree - show pricing
        items_cols = ("id", "commercial", "quantity", "pricing_type", "unit_price", "total_price", "spot_length", "priority", "active")
        self.items_tree_wrap = ScrolledTreeview(items_frame, items_cols, height=7)
        self.items_tree_wrap.pack(fill="both", expand=True, padx=2, pady=2)
        self.items_tree = self.items_tree_wrap.tree
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_select)

        # Items form - FULL COVERAGE
        itf = ttk.Frame(items_frame); itf.pack(fill="x", padx=2, pady=1)
        # Row 0: commercial
        ttk.Label(itf, text="Com:").grid(row=0, column=0, sticky="w")
        self.com_cb = ttk.Combobox(itf, state="readonly", width=22); self.com_cb.grid(row=0, column=1, padx=1)
        ttk.Label(itf, text="Com Title:").grid(row=0, column=2, sticky="w")
        self.commercial_title_var = tk.StringVar()
        ttk.Entry(itf, textvariable=self.commercial_title_var, width=20).grid(row=0, column=3, columnspan=3, padx=1, sticky="we")
        # Row1: qty, pricing_type, unit, total
        ttk.Label(itf, text="Qty:").grid(row=1, column=0, sticky="w")
        self.qty_var = tk.StringVar(value="0")
        qty_entry = ttk.Entry(itf, textvariable=self.qty_var, width=6); qty_entry.grid(row=1, column=1, padx=1)
        qty_entry.bind("<FocusOut>", lambda e: self.on_quantity_changed())
        qty_entry.bind("<KeyRelease>", lambda e: self.root.after(400, self.on_quantity_changed))

        ttk.Label(itf, text="Pricing:").grid(row=1, column=2, sticky="w")
        self.pricing_type_cb = ttk.Combobox(itf, values=["PER_SPOT","TOTAL"], width=10, state="readonly")
        self.pricing_type_cb.grid(row=1, column=3, padx=1, sticky="w"); self.pricing_type_cb.set("PER_SPOT")
        self.pricing_type_cb.bind("<<ComboboxSelected>>", lambda e: self.on_pricing_type_changed())

        ttk.Label(itf, text="Unit $:").grid(row=1, column=4, sticky="w")
        self.unit_price_var = tk.StringVar()
        self.unit_entry = ttk.Entry(itf, textvariable=self.unit_price_var, width=10)
        self.unit_entry.grid(row=1, column=5, padx=1, sticky="w")
        self.unit_entry.bind("<FocusOut>", lambda e: self.on_unit_price_changed())
        self.unit_entry.bind("<KeyRelease>", lambda e: self.root.after(500, self.on_unit_price_changed))

        ttk.Label(itf, text="Total $:").grid(row=1, column=6, sticky="w")
        self.total_price_var = tk.StringVar()
        self.total_entry = ttk.Entry(itf, textvariable=self.total_price_var, width=12)
        self.total_entry.grid(row=1, column=7, padx=1, sticky="w")
        self.total_entry.bind("<FocusOut>", lambda e: self.on_total_price_changed())
        self.total_entry.bind("<KeyRelease>", lambda e: self.root.after(500, self.on_total_price_changed))

        # Row2: spot length, priority, rotation_group, dates
        ttk.Label(itf, text="Len:").grid(row=2, column=0, sticky="w")
        self.len_var = tk.StringVar(value="30")
        ttk.Entry(itf, textvariable=self.len_var, width=6).grid(row=2, column=1, padx=1, sticky="w")
        ttk.Label(itf, text="Pri:").grid(row=2, column=2, sticky="w")
        self.priority_var = tk.StringVar(value="1")
        ttk.Entry(itf, textvariable=self.priority_var, width=4).grid(row=2, column=3, padx=1, sticky="w")
        ttk.Label(itf, text="Rot Grp:").grid(row=2, column=4, sticky="w")
        self.rotation_group_var = tk.StringVar()
        ttk.Entry(itf, textvariable=self.rotation_group_var, width=10).grid(row=2, column=5, padx=1, sticky="w")
        self.item_active = tk.IntVar(value=1)
        ttk.Checkbutton(itf, text="Act", variable=self.item_active).grid(row=2, column=6, padx=2)

        ttk.Label(itf, text="Start:").grid(row=3, column=0, sticky="w")
        self.item_start_var = tk.StringVar()
        ttk.Entry(itf, textvariable=self.item_start_var, width=12).grid(row=3, column=1, padx=1, sticky="w")
        ttk.Label(itf, text="End:").grid(row=3, column=2, sticky="w")
        self.item_end_var = tk.StringVar()
        ttk.Entry(itf, textvariable=self.item_end_var, width=12).grid(row=3, column=3, padx=1, sticky="w")
        ttk.Label(itf, text="Desc:").grid(row=3, column=4, sticky="w")
        self.item_desc_var = tk.StringVar()
        ttk.Entry(itf, textvariable=self.item_desc_var, width=22).grid(row=3, column=5, columnspan=3, padx=1, sticky="we")

        ttk.Label(itf, text="Notes:").grid(row=4, column=0, sticky="w")
        self.item_notes_var = tk.StringVar()
        ttk.Entry(itf, textvariable=self.item_notes_var, width=58).grid(row=4, column=1, columnspan=7, padx=1, sticky="we", pady=1)

        # pricing info label
        self.pricing_info_var = tk.StringVar(value="PER_SPOT: enter unit price → total calculated. TOTAL: enter total → unit calculated.")
        ttk.Label(itf, textvariable=self.pricing_info_var, foreground="#6c757d").grid(row=5, column=0, columnspan=8, sticky="w", pady=1)

        btn_it = ttk.Frame(items_frame); btn_it.pack(fill="x", padx=2, pady=1)
        self.add_item_btn = ttk.Button(btn_it, text="Add Item", command=self.add_item); self.add_item_btn.pack(side="left", padx=1)
        self.update_item_btn = ttk.Button(btn_it, text="Upd Item", command=self.update_item); self.update_item_btn.pack(side="left", padx=1)
        self.item_status_lbl = ttk.Label(btn_it, text=" (select contract)", foreground="gray"); self.item_status_lbl.pack(side="left", padx=5)

        # ---- RULES ----
        rules_frame = ttk.LabelFrame(paned_main, text="3. Contract Item Rules")
        paned_main.add(rules_frame, weight=2)
        rules_cols = ("id", "days_of_week", "start_time", "end_time", "max_spots_per_day", "max_spots_per_week", "allow_news", "allow_special", "active", "pref_program", "pref_stopset", "notes")
        self.rules_tree_wrap = ScrolledTreeview(rules_frame, rules_cols, height=5)
        self.rules_tree_wrap.pack(fill="both", expand=True, padx=2, pady=2)
        self.rules_tree = self.rules_tree_wrap.tree
        self.rules_tree.bind("<<TreeviewSelect>>", self.on_rule_select)

        rf_days = ttk.Frame(rules_frame); rf_days.pack(fill="x", padx=3, pady=1)
        ttk.Label(rf_days, text="Days:").pack(side="left")
        self.day_vars = {}
        for d in DAY_ORDER:
            var = tk.BooleanVar(value=(d in ["Mon","Tue","Wed","Thu","Fri"]))
            self.day_vars[d] = var
            ttk.Checkbutton(rf_days, text=d, variable=var, command=self.sync_days_from_checkboxes).pack(side="left", padx=2)
        self.days_var = tk.StringVar(value="Mon,Tue,Wed,Thu,Fri")
        ttk.Label(rf_days, textvariable=self.days_var, foreground="gray").pack(side="left", padx=10)

        rf = ttk.Frame(rules_frame); rf.pack(fill="x", padx=3, pady=1)
        ttk.Label(rf, text="Start:").grid(row=0, column=0, sticky="w")
        self.rule_start = tk.StringVar(value="06:00")
        ttk.Entry(rf, textvariable=self.rule_start, width=7).grid(row=0, column=1, padx=2)
        ttk.Label(rf, text="End:").grid(row=0, column=2, sticky="w")
        self.rule_end = tk.StringVar(value="23:00")
        ttk.Entry(rf, textvariable=self.rule_end, width=7).grid(row=0, column=3, padx=2)
        ttk.Label(rf, text="/Day:").grid(row=0, column=4, sticky="w")
        self.per_day = tk.IntVar(value=1)
        ttk.Entry(rf, textvariable=self.per_day, width=4).grid(row=0, column=5, padx=2)
        ttk.Label(rf, text="/Wk:").grid(row=0, column=6, sticky="w")
        self.per_week = tk.IntVar(value=5)
        ttk.Entry(rf, textvariable=self.per_week, width=4).grid(row=0, column=7, padx=2)
        self.allow_news = tk.IntVar(value=1)
        ttk.Checkbutton(rf, text="News", variable=self.allow_news).grid(row=0, column=8, padx=4)
        self.allow_spec = tk.IntVar(value=1)
        ttk.Checkbutton(rf, text="Special", variable=self.allow_spec).grid(row=0, column=9, padx=4)
        self.rule_active = tk.IntVar(value=1)
        ttk.Checkbutton(rf, text="Act", variable=self.rule_active).grid(row=0, column=10, padx=4)

        rf_pref = ttk.Frame(rules_frame); rf_pref.pack(fill="x", padx=3, pady=1)
        ttk.Label(rf_pref, text="Pref Prog:").grid(row=0, column=0, sticky="w")
        self.pref_program_cb = ttk.Combobox(rf_pref, state="readonly", width=22)
        self.pref_program_cb.grid(row=0, column=1, padx=3, sticky="w")
        ttk.Label(rf_pref, text="Pref Stopset (LIKE search):").grid(row=0, column=2, sticky="w", padx=(10,2))
        self.pref_stopset_cb = DBSearchableCombobox(rf_pref, width=28, search_func=self.search_stopsets_like)
        self.pref_stopset_cb.grid(row=0, column=3, padx=3, sticky="w")
        ttk.Label(rf_pref, text="Type 2+ chars", foreground="gray").grid(row=0, column=4, sticky="w")

        rf2 = ttk.Frame(rules_frame); rf2.pack(fill="x", padx=3, pady=1)
        ttk.Label(rf2, text="Notes:").pack(side="left", padx=2)
        self.notes_var = tk.StringVar()
        ttk.Entry(rf2, textvariable=self.notes_var, width=30).pack(side="left", padx=2)
        self.add_rule_btn = ttk.Button(rf2, text="Add Rule", command=self.add_rule); self.add_rule_btn.pack(side="left", padx=8)
        self.update_rule_btn = ttk.Button(rf2, text="Update Rule", command=self.update_rule); self.update_rule_btn.pack(side="left", padx=2)
        self.rule_status_lbl = ttk.Label(rf2, text=" (select item)", foreground="gray"); self.rule_status_lbl.pack(side="left", padx=8)

        sched_row = ttk.Frame(rules_frame); sched_row.pack(fill="x", padx=3, pady=4)
        self.schedule_info_var = tk.StringVar(value="Select an Item")
        ttk.Label(sched_row, textvariable=self.schedule_info_var, foreground="gray").pack(side="left", padx=5)
        self.schedule_run_btn = ttk.Button(sched_row, text="Run Schedule", command=self.run_schedule, state="disabled")
        self.schedule_run_btn.pack(side="right", padx=5)

        self.on_pricing_type_changed()

    # ---------- Pricing logic ----------
    def get_quantity_int(self):
        try: return int(Decimal(str(self.qty_var.get() or "0")))
        except: return 0

    def on_pricing_type_changed(self):
        pt = self.pricing_type_cb.get() or "PER_SPOT"
        if pt == "PER_SPOT":
            self.pricing_info_var.set("PER_SPOT: Unit $ editable, Total $ read-only = qty × unit.")
            self.unit_entry.config(state="normal")
            self.total_entry.config(state="readonly")
        else:
            self.pricing_info_var.set("TOTAL: Total $ editable, Unit $ read-only = total ÷ qty.")
            self.unit_entry.config(state="readonly")
            self.total_entry.config(state="normal")
        # trigger recalc
        self.recalc_pricing(source="type")

    def on_quantity_changed(self):
        self.recalc_pricing(source="qty")

    def on_unit_price_changed(self):
        if self.pricing_type_cb.get() == "PER_SPOT":
            self.recalc_pricing(source="unit")

    def on_total_price_changed(self):
        if self.pricing_type_cb.get() == "TOTAL":
            self.recalc_pricing(source="total")

    def recalc_pricing(self, source="unit"):
        if self._pricing_recalc_lock: return
        self._pricing_recalc_lock = True
        try:
            pt = self.pricing_type_cb.get() or "PER_SPOT"
            qty = self.get_quantity_int()
            unit_cents = dollars_to_cents(self.unit_price_var.get())
            total_cents = dollars_to_cents(self.total_price_var.get())

            if pt == "PER_SPOT":
                # unit authoritative, total readonly
                if qty < 0:
                    self.pricing_info_var.set("Quantity cannot be negative.")
                    return
                if unit_cents is not None:
                    calc_total = calculate_amount(qty, unit_cents)
                    # Temporarily make total writable to update
                    was_state = self.total_entry.cget("state")
                    self.total_entry.config(state="normal")
                    self.total_price_var.set(cents_to_dollars(calc_total))
                    self.total_entry.config(state=was_state)
                    self.pricing_info_var.set(f"PER_SPOT: {qty} × ${cents_to_dollars(unit_cents)} = ${cents_to_dollars(calc_total)}")
            else: # TOTAL
                # total authoritative, unit readonly
                if qty <= 0:
                    # validation for qty=0 in TOTAL mode
                    was_state = self.unit_entry.cget("state")
                    self.unit_entry.config(state="normal")
                    self.unit_price_var.set("0.00")
                    self.unit_entry.config(state=was_state)
                    if qty == 0:
                        self.pricing_info_var.set("⚠ TOTAL mode requires qty > 0 to calculate unit price. Enter qty first.")
                    else:
                        self.pricing_info_var.set("⚠ Quantity cannot be negative.")
                    return
                if total_cents is not None:
                    unit_calc = (Decimal(total_cents) / Decimal(qty)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                    calc_unit_cents = int(unit_calc)
                    was_state = self.unit_entry.cget("state")
                    self.unit_entry.config(state="normal")
                    self.unit_price_var.set(cents_to_dollars(calc_unit_cents))
                    self.unit_entry.config(state=was_state)
                    precise = (Decimal(total_cents) / Decimal(qty) / Decimal("100"))
                    if total_cents % qty != 0:
                        self.pricing_info_var.set(f"TOTAL: ${cents_to_dollars(total_cents)} ÷ {qty} = ${precise:.4f} (stored ${cents_to_dollars(calc_unit_cents)} rounded)")
                    else:
                        self.pricing_info_var.set(f"TOTAL: ${cents_to_dollars(total_cents)} ÷ {qty} = ${cents_to_dollars(calc_unit_cents)}")
        finally:
            self._pricing_recalc_lock = False

    def sync_days_from_checkboxes(self):
        selected = [d for d, v in self.day_vars.items() if v.get()]
        self.days_var.set(",".join(selected))

    def sync_checkboxes_from_days(self, days_str):
        normalized = normalize_days_to_names(days_str)
        selected_set = set(normalized.split(",")) if normalized else set()
        for d, var in self.day_vars.items(): var.set(d in selected_set)
        self.days_var.set(normalized)

    def search_stopsets_like(self, text):
        con = get_connection(); cur = con.cursor()
        try:
            fallback = [
                ("SELECT id, COALESCE(name, code, 'Stopset ' || id) as label FROM stopsets WHERE name LIKE ? OR code LIKE ? ORDER BY label LIMIT 100", 2),
                ("SELECT id, name as label FROM stopsets WHERE name LIKE ? ORDER BY name LIMIT 100", 1),
            ]
            pattern = f"%{text}%"
            for sql, param_count in fallback:
                try:
                    if param_count == 2: cur.execute(sql, (pattern, pattern))
                    else: cur.execute(sql, (pattern,))
                    rows = cur.fetchall()
                    return [(r["id"], r["label"]) for r in rows]
                except: continue
            return []
        finally: con.close()

    def update_button_states(self):
        has_contract = self.selected_contract_id is not None
        has_item = self.selected_item_id is not None
        state_c = "normal" if has_contract else "disabled"
        state_i = "normal" if has_item else "disabled"
        if hasattr(self, 'add_item_btn'): self.add_item_btn.config(state=state_c)
        self.update_item_btn.config(state=state_i)
        self.item_status_lbl.config(text=f"→ Contract {self.selected_contract_id}" if has_contract else " (select contract)")
        if hasattr(self, 'add_rule_btn'): self.add_rule_btn.config(state=state_i)
        self.update_rule_btn.config(state="disabled" if not has_item or not self.rules_tree.selection() else "normal")
        self.rule_status_lbl.config(text=f"→ Item {self.selected_item_id}" if has_item else " (select item)")
        if hasattr(self, 'schedule_run_btn'): self.schedule_run_btn.config(state=state_i)
        self.schedule_info_var.set(f"Ready to schedule Item {self.selected_item_id}" if has_item else "Select an Item")

    def load_lookups(self):
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute("SELECT id, company_name FROM customers WHERE active=1 ORDER BY company_name")
            self.customers = {r["company_name"]: r["id"] for r in cur.fetchall()}
            self.cust_cb["values"] = list(self.customers.keys())
            cur.execute("SELECT id, first_name, last_name FROM salespeople WHERE active=1 ORDER BY last_name")
            self.salespeople = {f"{r['first_name']} {r['last_name']}": r["id"] for r in cur.fetchall()}
            self.sales_cb["values"] = list(self.salespeople.keys())
            cur.execute("SELECT id, name FROM stations WHERE active=1 ORDER BY name")
            self.stations = {r["name"]: r["id"] for r in cur.fetchall()}
            self.stat_cb["values"] = list(self.stations.keys())
            cur.execute("SELECT id, title FROM commercials WHERE active=1 ORDER BY title")
            self.commercials = {r["title"]: r["id"] for r in cur.fetchall()}
            self.com_cb["values"] = list(self.commercials.keys())
            try:
                cur.execute("SELECT id, name FROM programs ORDER BY name")
                rows = cur.fetchall()
                self.programs = {r["name"]: r["id"] for r in rows}
                self.programs_by_id = {r["id"]: r["name"] for r in rows}
                self.pref_program_cb["values"] = ["-- Any --"] + list(self.programs.keys())
                self.pref_program_cb.set("-- Any --")
            except Exception as e:
                print(f"programs lookup failed: {e}")
                self.pref_program_cb["values"] = ["-- Any --"]; self.pref_program_cb.set("-- Any --")
        finally: con.close()

    def load_contracts(self):
        filter_text = self.filter_var.get().strip()
        con = get_connection(); cur = con.cursor()
        try:
            base = """ SELECT co.id, co.contract_number, c.company_name, s.name as sname,
             sp.first_name || ' ' || sp.last_name as sales_name,
             co.status, co.active, co.start_date, co.end_date, co.description, co.notes,
             co.customer_id, co.salesperson_id, co.station_id, co.payment_timing, co.payment_terms_days
            FROM contracts co
             JOIN customers c ON co.customer_id=c.id
             JOIN stations s ON co.station_id=s.id
             JOIN salespeople sp ON co.salesperson_id=sp.id """
            if filter_text:
                cur.execute(base + " WHERE co.contract_number LIKE ? OR c.company_name LIKE ? ORDER BY co.id DESC", (f"%{filter_text}%", f"%{filter_text}%"))
            else:
                cur.execute(base + " ORDER BY co.id DESC")
            rows = cur.fetchall()
            self.contract_tree.delete(*self.contract_tree.get_children())
            self.contract_cache = {r["id"]: r for r in rows}
            for r in rows:
                self.contract_tree.insert("", "end", values=(r["id"], r["contract_number"], r["company_name"], r["sname"], r["sales_name"], r["status"], r["payment_timing"], r["start_date"], r["end_date"], r["active"]))
            self.status_var.set(f"Loaded {len(rows)} contracts")
        finally: con.close()

    def on_contract_select(self, event):
        sel = self.contract_tree.selection()
        if not sel: return
        vals = self.contract_tree.item(sel[0], "values")
        cid = int(vals[0])
        self.selected_contract_id = cid; self.selected_item_id = None
        r = self.contract_cache.get(cid)
        if r:
            for name, i in self.customers.items():
                if i == r["customer_id"]: self.cust_cb.set(name); break
            for name, i in self.salespeople.items():
                if i == r["salesperson_id"]: self.sales_cb.set(name); break
            for name, i in self.stations.items():
                if i == r["station_id"]: self.stat_cb.set(name); break
            self.num_var.set(r["contract_number"] or ""); self.status_cb.set(r["status"] or "Draft")
            self.start_var.set(r["start_date"] or ""); self.end_var.set(r["end_date"] or "")
            self.active_var.set(r["active"])
            self.contract_desc_var.set(r["description"] or "")
            self.contract_notes_var.set(r["notes"] or "")
            self.payment_timing_cb.set(r["payment_timing"] or "POSTPAID")
            self.payment_terms_var.set(str(r["payment_terms_days"] if r["payment_terms_days"] is not None else "30"))
            self.load_items_for_contract(cid); self.update_button_states()

    def load_items_for_contract(self, contract_id):
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" SELECT ci.id, com.title as title, ci.commercial_title, ci.quantity, ci.spot_length_seconds,
             ci.priority, ci.active, ci.description, ci.commercial_id, ci.contract_id,
             ci.pricing_type, ci.unit_price, ci.total_price, ci.start_date, ci.end_date, ci.rotation_group, ci.notes
            FROM contract_items ci LEFT JOIN commercials com ON ci.commercial_id=com.id
             WHERE ci.contract_id=? ORDER BY ci.id """, (contract_id,))
            rows = cur.fetchall()
            self.items_tree.delete(*self.items_tree.get_children())
            self.item_cache = {r["id"]: r for r in rows}
            for r in rows:
                disp_title = r["title"] or r["commercial_title"] or "(no title)"
                pt = r["pricing_type"] or "PER_SPOT"
                up = cents_to_dollars(r["unit_price"]) if r["unit_price"] is not None else ""
                tp = cents_to_dollars(r["total_price"]) if r["total_price"] is not None else ""
                self.items_tree.insert("", "end", values=(r["id"], disp_title, r["quantity"], pt, f"${up}" if up else "", f"${tp}" if tp else "", r["spot_length_seconds"], r["priority"], r["active"]))
            self.rules_tree.delete(*self.rules_tree.get_children())
            self.status_var.set(f"Contract {contract_id}: {len(rows)} items")
            if rows:
                first = self.items_tree.get_children()[0]
                self.items_tree.selection_set(first); self.items_tree.focus(first); self.items_tree.see(first)
                self.root.after(10, lambda: self.on_item_select(None))
        finally: con.close()

    def on_item_select(self, event):
        sel = self.items_tree.selection()
        if not sel: return
        vals = self.items_tree.item(sel[0], "values")
        item_id = int(vals[0]); self.selected_item_id = item_id
        r = self.item_cache.get(item_id)
        if r:
            for name, i in self.commercials.items():
                if i == r["commercial_id"]: self.com_cb.set(name); break
            else: self.com_cb.set(r["commercial_title"] or "")
            self.commercial_title_var.set(r["commercial_title"] or "")
            self.qty_var.set(str(r["quantity"] or 0))
            self.len_var.set(str(r["spot_length_seconds"] or 30))
            self.item_active.set(r["active"])
            self.priority_var.set(str(r["priority"] or 1))
            self.rotation_group_var.set(r["rotation_group"] or "")
            self.item_start_var.set(r["start_date"] or "")
            self.item_end_var.set(r["end_date"] or "")
            self.item_desc_var.set(r["description"] or "")
            self.item_notes_var.set(r["notes"] or "")
            # pricing - set both fields temporarily writable to load
            self.pricing_type_cb.set(r["pricing_type"] or "PER_SPOT")
            self.unit_entry.config(state="normal"); self.total_entry.config(state="normal")
            self.unit_price_var.set(cents_to_dollars(r["unit_price"]) if r["unit_price"] is not None else "")
            self.total_price_var.set(cents_to_dollars(r["total_price"]) if r["total_price"] is not None else "")
            self.on_pricing_type_changed()
            self.load_rules_for_item(item_id); self.update_button_states()

    def load_rules_for_item(self, item_id):
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" SELECT id, contract_item_id, days_of_week, start_time, end_time,
             max_spots_per_day, max_spots_per_week, allow_news, allow_special_events, active, notes,
             preferred_program_id, preferred_stopset_id
             FROM contract_item_rules WHERE contract_item_id=? ORDER BY id """, (item_id,))
            rows = cur.fetchall()
            self.rules_tree.delete(*self.rules_tree.get_children())
            self.rule_cache = {r["id"]: r for r in rows}
            for r in rows:
                prog_label = self.programs_by_id.get(r["preferred_program_id"], "") if r["preferred_program_id"] else ""
                pref_prog_disp = f"{prog_label} [{r['preferred_program_id']}]" if r["preferred_program_id"] else ""
                stop_id = r["preferred_stopset_id"]
                pref_stop_disp = f"[{stop_id}]" if stop_id else ""
                if stop_id and stop_id in self.stopsets_by_id: pref_stop_disp = f"{self.stopsets_by_id[stop_id]} [{stop_id}]"
                days_norm = normalize_days_to_names(r["days_of_week"])
                self.rules_tree.insert("", "end", values=(r["id"], days_norm, r["start_time"], r["end_time"], r["max_spots_per_day"], r["max_spots_per_week"], r["allow_news"], r["allow_special_events"], r["active"], pref_prog_disp, pref_stop_disp, r["notes"]))
            self.status_var.set(f"Item {item_id}: {len(rows)} rules")
        finally: con.close()

    def on_rule_select(self, event):
        sel = self.rules_tree.selection()
        if not sel: return
        rid = int(self.rules_tree.item(sel[0], "values")[0])
        r = self.rule_cache.get(rid)
        if not r: return
        self.sync_checkboxes_from_days(r["days_of_week"] or "")
        self.rule_start.set(r["start_time"] or ""); self.rule_end.set(r["end_time"] or "")
        self.per_day.set(r["max_spots_per_day"] or 0); self.per_week.set(r["max_spots_per_week"] or 0)
        self.allow_news.set(r["allow_news"]); self.allow_spec.set(r["allow_special_events"])
        self.rule_active.set(r["active"]); self.notes_var.set(r["notes"] or "")
        prog_id = r["preferred_program_id"]; stop_id = r["preferred_stopset_id"]
        if prog_id and prog_id in self.programs_by_id: self.pref_program_cb.set(self.programs_by_id[prog_id])
        else: self.pref_program_cb.set("-- Any --")
        if stop_id:
            con = get_connection(); cur = con.cursor()
            try:
                cur.execute("SELECT COALESCE(name, code, 'Stopset ' || id) as label FROM stopsets WHERE id=?", (stop_id,))
                row = cur.fetchone(); label = row["label"] if row else f"Stopset {stop_id}"
                self.stopsets_by_id[stop_id] = label; self.pref_stopset_cb.set_resolved(stop_id, label)
            except: self.pref_stopset_cb.set_resolved(stop_id, f"Stopset {stop_id}")
            finally: con.close()
        else: self.pref_stopset_cb.set_id(None)
        self.update_rule_btn.config(state="normal")

    def refresh_all(self):
        self.load_lookups(); self.load_contracts()
        self.items_tree.delete(*self.items_tree.get_children()); self.rules_tree.delete(*self.rules_tree.get_children())
        self.selected_contract_id = None; self.selected_item_id = None; self.update_button_states()

    def clear_contract_form(self):
        self.selected_contract_id = None; self.selected_item_id = None
        self.contract_tree.selection_remove(self.contract_tree.selection())
        self.items_tree.delete(*self.items_tree.get_children()); self.rules_tree.delete(*self.rules_tree.get_children())
        self.cust_cb.set(""); self.sales_cb.set(""); self.stat_cb.set("")
        self.num_var.set(""); self.status_cb.set("Draft"); self.start_var.set(""); self.end_var.set("")
        self.active_var.set(1); self.contract_desc_var.set(""); self.contract_notes_var.set("")
        self.payment_timing_cb.set("POSTPAID"); self.payment_terms_var.set("30")
        self.update_button_states(); self.status_var.set("New contract")

    def _get_contract_form_values(self):
        cust_id = self.customers.get(self.cust_cb.get())
        sales_id = self.salespeople.get(self.sales_cb.get())
        stat_id = self.stations.get(self.stat_cb.get())
        try: terms = int(self.payment_terms_var.get() or "30")
        except: terms = 30
        return cust_id, sales_id, stat_id, terms

    def add_contract(self):
        cust_id, sales_id, stat_id, terms = self._get_contract_form_values()
        if not cust_id or not sales_id or not stat_id:
            messagebox.showwarning("Validation", "Select customer, salesperson, and station"); return
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" INSERT INTO contracts (customer_id, salesperson_id, station_id, contract_number, description, status, start_date, end_date, notes, active, payment_timing, payment_terms_days, created_date, modified_date)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) """,
            (cust_id, sales_id, stat_id, self.num_var.get().strip(), self.contract_desc_var.get().strip(), self.status_cb.get(), self.start_var.get().strip() or None, self.end_var.get().strip() or None, self.contract_notes_var.get().strip(), self.active_var.get(), self.payment_timing_cb.get(), terms, now_str(), now_str()))
            con.commit(); self.load_contracts()
        except Exception as e: messagebox.showerror("Error", str(e))
        finally: con.close()

    def update_contract(self):
        if not self.selected_contract_id: messagebox.showwarning("Select", "Select a contract"); return
        cust_id, sales_id, stat_id, terms = self._get_contract_form_values()
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" UPDATE contracts SET customer_id=?, salesperson_id=?, station_id=?, contract_number=?, description=?, status=?, start_date=?, end_date=?, notes=?, active=?, payment_timing=?, payment_terms_days=?, modified_date=? WHERE id=? """,
            (cust_id, sales_id, stat_id, self.num_var.get().strip(), self.contract_desc_var.get().strip(), self.status_cb.get(), self.start_var.get().strip() or None, self.end_var.get().strip() or None, self.contract_notes_var.get().strip(), self.active_var.get(), self.payment_timing_cb.get(), terms, now_str(), self.selected_contract_id))
            con.commit(); self.load_contracts()
        finally: con.close()

    def toggle_contract_active(self):
        if not self.selected_contract_id: return
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute("SELECT active FROM contracts WHERE id=?", (self.selected_contract_id,)); row = cur.fetchone()
            if not row: return
            new_active = 0 if row["active"] else 1
            cur.execute("UPDATE contracts SET active=?, modified_date=? WHERE id=?", (new_active, now_str(), self.selected_contract_id))
            con.commit(); self.load_contracts()
        finally: con.close()

    # ---------- Item add/update with pricing ----------
    def _get_item_pricing_cents(self):
        pt = self.pricing_type_cb.get() or "PER_SPOT"
        qty = self.get_quantity_int()
        if qty < 0:
            raise ValueError("Quantity cannot be negative")
        if pt == "TOTAL" and qty == 0:
            raise ValueError("TOTAL pricing requires quantity > 0 to calculate unit price")
        unit_cents = dollars_to_cents(self.unit_price_var.get())
        total_cents = dollars_to_cents(self.total_price_var.get())
        # Enforce authoritative logic
        if pt == "PER_SPOT":
            if unit_cents is None: unit_cents = 0
            total_cents = calculate_amount(qty, unit_cents)
        else: # TOTAL
            if total_cents is None: total_cents = 0
            unit_cents = int((Decimal(total_cents) / Decimal(qty)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return pt, qty, unit_cents, total_cents

    def add_item(self):
        if not self.selected_contract_id: messagebox.showwarning("Select", "Select a contract first"); return
        com_id = self.commercials.get(self.com_cb.get())
        pt, qty, unit_cents, total_cents = self._get_item_pricing_cents()
        try: spot_len = int(self.len_var.get() or "0")
        except: spot_len = 0
        try: pri = int(self.priority_var.get() or "1")
        except: pri = 1
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" INSERT INTO contract_items
             (contract_id, commercial_id, commercial_title, description, quantity, pricing_type, unit_price, total_price, spot_length_seconds, start_date, end_date, priority, rotation_group, notes, active, created_date, modified_date)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) """,
            (self.selected_contract_id, com_id, self.commercial_title_var.get().strip() or self.com_cb.get().strip(), self.item_desc_var.get().strip(), qty, pt, unit_cents, total_cents, spot_len, self.item_start_var.get().strip() or None, self.item_end_var.get().strip() or None, pri, self.rotation_group_var.get().strip(), self.item_notes_var.get().strip(), self.item_active.get(), now_str(), now_str()))
            con.commit(); self.load_items_for_contract(self.selected_contract_id)
        except Exception as e: messagebox.showerror("Error", str(e))
        finally: con.close()

    def update_item(self):
        if not self.selected_item_id: return
        com_id = self.commercials.get(self.com_cb.get())
        pt, qty, unit_cents, total_cents = self._get_item_pricing_cents()
        try: spot_len = int(self.len_var.get() or "0")
        except: spot_len = 0
        try: pri = int(self.priority_var.get() or "1")
        except: pri = 1
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" UPDATE contract_items SET commercial_id=?, commercial_title=?, description=?, quantity=?, pricing_type=?, unit_price=?, total_price=?, spot_length_seconds=?, start_date=?, end_date=?, priority=?, rotation_group=?, notes=?, active=?, modified_date=? WHERE id=? """,
            (com_id, self.commercial_title_var.get().strip() or self.com_cb.get().strip(), self.item_desc_var.get().strip(), qty, pt, unit_cents, total_cents, spot_len, self.item_start_var.get().strip() or None, self.item_end_var.get().strip() or None, pri, self.rotation_group_var.get().strip(), self.item_notes_var.get().strip(), self.item_active.get(), now_str(), self.selected_item_id))
            con.commit(); self.load_items_for_contract(self.selected_contract_id)
        finally: con.close()

    def _get_pref_ids(self):
        prog_name = self.pref_program_cb.get()
        prog_id = None if not prog_name or prog_name == "-- Any --" else self.programs.get(prog_name)
        stop_id = self.pref_stopset_cb.get_id()
        return prog_id, stop_id

    def add_rule(self):
        if not self.selected_item_id: messagebox.showwarning("Select", "Select item first"); return
        prog_id, stop_id = self._get_pref_ids()
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" INSERT INTO contract_item_rules (contract_item_id, days_of_week, start_time, end_time, max_spots_per_day, max_spots_per_week, allow_news, allow_special_events, active, notes, preferred_program_id, preferred_stopset_id, created_date, modified_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) """,
            (self.selected_item_id, self.days_var.get().strip(), self.rule_start.get().strip(), self.rule_end.get().strip(), self.per_day.get() or 0, self.per_week.get() or 0, self.allow_news.get(), self.allow_spec.get(), self.rule_active.get(), self.notes_var.get().strip(), prog_id, stop_id, now_str(), now_str()))
            con.commit(); self.load_rules_for_item(self.selected_item_id)
        except Exception as e: messagebox.showerror("Error", str(e))
        finally: con.close()

    def update_rule(self):
        sel = self.rules_tree.selection()
        if not sel: messagebox.showwarning("Select", "Select rule"); return
        rid = int(self.rules_tree.item(sel[0], "values")[0])
        prog_id, stop_id = self._get_pref_ids()
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" UPDATE contract_item_rules SET days_of_week=?, start_time=?, end_time=?, max_spots_per_day=?, max_spots_per_week=?, allow_news=?, allow_special_events=?, active=?, notes=?, preferred_program_id=?, preferred_stopset_id=?, modified_date=? WHERE id=? """,
            (self.days_var.get().strip(), self.rule_start.get().strip(), self.rule_end.get().strip(), self.per_day.get() or 0, self.per_week.get() or 0, self.allow_news.get(), self.allow_spec.get(), self.rule_active.get(), self.notes_var.get().strip(), prog_id, stop_id, now_str(), rid))
            con.commit(); self.load_rules_for_item(self.selected_item_id)
        finally: con.close()

    def run_schedule(self):
        if not self.selected_item_id: messagebox.showwarning("Select Item", "Select Item first."); return
        try:
            result = schedule_contract_item_quantity(self.selected_item_id)
            messagebox.showinfo("Result", str(result))
        except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    ContractMasterDetailGUI(root)
    root.mainloop()
