# File: prototype/met/contract_master_detail_gui_new.py


# File: prototype/met/contract_master_detail_gui.py - v4 improved
# - Keeps 3-pane design but more compact
# - LIKE search for stopsets (DB query after 2 chars, LIMIT 100) - scalable
# - Days as Mon,Tue checkboxes instead of 1,2
# - Auto-select first item -> Run Schedule enabled
# - Preferred program/stopset fields

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
from traffic.database import get_connection
from traffic.scheduler import schedule_contract_item_quantity

def now_str(): return datetime.now().isoformat(sep=' ', timespec='seconds')

# ---------- Days helpers: Mon,Tue instead of 1,2 ----------

DAY_ORDER = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
DAY_TO_NUM = {name: i+1 for i, name in enumerate(DAY_ORDER)}  # Mon=1 .. Sun=7
NUM_TO_DAY = {v:k for k,v in DAY_TO_NUM.items()}

def normalize_days_to_names(days_str):
    """Convert '1,2,3' or 'Mon,Tue' or '0,1' etc to 'Mon,Tue,Wed'"""
    if not days_str:
        return ""
    parts = [p.strip() for p in days_str.replace(";",",").split(",") if p.strip()]
    result = []
    for p in parts:
        if p in DAY_ORDER:
            result.append(p)
        elif p.isdigit():
            n = int(p)
            # handle 0=Sunday or 7=Sunday variants
            if n == 0: n = 7
            if n in NUM_TO_DAY:
                result.append(NUM_TO_DAY[n])
        else:
            # try case-insensitive Mon
            cap = p[:3].title()
            if cap in DAY_ORDER:
                result.append(cap)
    # preserve order Mon..Sun
    ordered = [d for d in DAY_ORDER if d in result]
    return ",".join(ordered)

def names_to_nums_if_needed(days_str):
    # If you still need to store as numbers for scheduler, use this
    # For now we store Mon,Tue as you requested
    return normalize_days_to_names(days_str)

# ---------- LIKE Searchable Combobox (DB-backed) ----------

class DBSearchableCombobox(ttk.Frame):
    """
    For long lists like stopsets.
    - Does NOT preload all rows.
    - After 2 chars typed, runs: SELECT ... WHERE label LIKE '%text%' LIMIT 100
    - Debounced (300ms) to avoid hammering DB
    """
    def __init__(self, parent, placeholder="-- Any / No Preference --", width=30, search_func=None):
        super().__init__(parent)
        self.placeholder = placeholder
        self.search_func = search_func  # func(text) -> list of (id, label)
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
            if foc not in (self.entry, self.listbox, self.btn):
                self.hide_list()

    def toggle_list(self):
        if self.listbox_frame and self.listbox_frame.winfo_ismapped():
            self.hide_list()
        else:
            self.show_list(initial=True)

    def show_list(self, initial=False):
        if self.listbox_frame:
            self.listbox_frame.destroy()
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
            # show placeholder + hint
            self.filtered = [(None, self.placeholder), (None, "Type 2+ letters to search...")]
        self.refresh()
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind("<Button-1>", self.on_select)

    def hide_list(self):
        if self.listbox_frame:
            self.listbox_frame.destroy()
            self.listbox_frame = None
            self.listbox = None

    def refresh(self):
        if not self.listbox: return
        self.listbox.delete(0, tk.END)
        for oid, label in self.filtered:
            if oid is None and "Type" in label:
                disp = label
            else:
                disp = f"{label}" if oid is None else f"{label} [{oid}]"
            self.listbox.insert(tk.END, disp)

    def on_keyrelease(self, e):
        if e.keysym in ("Up","Down","Return","Escape"):
            if e.keysym == "Escape":
                self.hide_list()
            return
        text = self.var_text.get().strip()
        # debounce
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(300, lambda: self.do_search(text))

    def do_search(self, text):
        if len(text) < 2:
            self.filtered = [(None, self.placeholder), (None, "Type 2+ letters to search...")]
            self.show_list()
            self.refresh()
            return
        try:
            results = self.search_func(text) if self.search_func else []
            # results is list of (id, label)
            self.filtered = [(None, self.placeholder)] + results[:100]
            self.id_to_label.update({oid: label for oid, label in results})
            self.show_list()
            self.refresh()
        except Exception as ex:
            print(f"DBSearch error: {ex}")
            self.filtered = [(None, self.placeholder), (None, f"Error: {ex}")]
            self.show_list()
            self.refresh()

    def on_select(self, e):
        if not self.listbox or not self.listbox.curselection(): return
        idx = self.listbox.curselection()[0]
        if idx >= len(self.filtered): return
        oid, label = self.filtered[idx]
        if label.startswith("Type"): return
        self.set_id(oid, label)
        self.hide_list()
        self.entry.focus_set()
        self.event_generate("<<ComboboxSelected>>")

    def get_id(self):
        return self.var_id

    def set_id(self, oid, label=None):
        self.var_id = oid
        if oid is None:
            self.var_text.set(self.placeholder if label is None else label)
        else:
            # try to resolve label
            resolved = label or self.id_to_label.get(oid, str(oid))
            self.var_text.set(resolved)
        # keep id_to_label
        if oid is not None and label:
            self.id_to_label[oid] = label

    def set_resolved(self, oid, label):
        """Set when loading existing rule with known id/label"""
        if oid is None:
            self.set_id(None)
        else:
            self.id_to_label[oid] = label
            self.set_id(oid, label)

# Simple searchable for programs (small list)
class SearchableComboboxSimple(ttk.Frame):
    def __init__(self, parent, options=None, placeholder="-- Any --", width=28):
        super().__init__(parent)
        self.all_options = [(None, placeholder)] + list(options or [])
        self.id_to_label = {oid: label for oid, label in self.all_options}
        self.var_text = tk.StringVar()
        self.var_id = None
        self.filtered = self.all_options
        self.entry = ttk.Entry(self, textvariable=self.var_text, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn = ttk.Button(self, text="▼", width=3, command=self.toggle_list)
        self.btn.pack(side=tk.LEFT)
        self.listbox_frame = None
        self.listbox = None
        self.entry.bind("<KeyRelease>", self.on_keyrelease)
        self.entry.bind("<FocusIn>", lambda e: self.show_list())
        self.entry.bind("<FocusOut>", lambda e: self.after(150, self.hide_if_not_focused))
    def hide_if_not_focused(self):
        if self.listbox_frame:
            foc = self.focus_get()
            if foc not in (self.entry, self.listbox, self.btn):
                self.hide_list()
    def toggle_list(self):
        if self.listbox_frame and self.listbox_frame.winfo_ismapped():
            self.hide_list()
        else:
            self.show_list()
    def show_list(self):
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
        self.refresh()
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind("<Button-1>", self.on_select)
    def hide_list(self):
        if self.listbox_frame:
            self.listbox_frame.destroy()
            self.listbox_frame = None
            self.listbox = None
    def refresh(self):
        if not self.listbox: return
        self.listbox.delete(0, tk.END)
        for oid, label in self.filtered:
            disp = f"{label}" if oid is None else f"{label} [{oid}]"
            self.listbox.insert(tk.END, disp)
    def on_keyrelease(self, e):
        if e.keysym in ("Up","Down","Return","Escape"):
            if e.keysym == "Escape": self.hide_list()
            return
        text = self.var_text.get().lower()
        self.filtered = self.all_options if not text else [o for o in self.all_options if text in o[1].lower() or text == str(o[0]).lower()]
        self.show_list()
        self.refresh()
    def on_select(self, e):
        if not self.listbox or not self.listbox.curselection(): return
        oid, label = self.filtered[self.listbox.curselection()[0]]
        self.set_id(oid)
        self.hide_list()
        self.entry.focus_set()
    def get_id(self): return self.var_id
    def set_id(self, oid):
        self.var_id = oid
        self.var_text.set(self.id_to_label.get(oid, ""))
        self.filtered = self.all_options
    def set_options(self, options, placeholder="-- Any --"):
        self.all_options = [(None, placeholder)] + list(options)
        self.id_to_label = {oid: label for oid, label in self.all_options}
        self.filtered = self.all_options

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
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        for c in columns:
            self.tree.heading(c, text=c.replace("_"," ").title())
            w=90
            if c in ("description","company_name","commercial_title","contract_number","notes","customer","commercial"):
                w=160
            if c in ("id","active","quantity","priority","max_spots_per_day","max_spots_per_week"):
                w=60
            if c in ("start_date","end_date","status","days_of_week"):
                w=80
            if c in ("pref_program","pref_stopset"):
                w=120
            self.tree.column(c, width=w, minwidth=40, stretch=True)

class ContractMasterDetailGUI:
    def __init__(self, root):
        self.root = root
        root.title("zbTraffic - Contracts -> Items -> Rules (Compact + LIKE search)")
        root.geometry("1350x900")
        self.customers = {}
        self.salespeople = {}
        self.stations = {}
        self.commercials = {}
        self.programs = {}
        self.programs_by_id = {}
        self.stopsets_by_id = {}
        self.contract_cache = {}
        self.item_cache = {}
        self.rule_cache = {}
        self.selected_contract_id = None
        self.selected_item_id = None
        self.build()
        self.load_lookups()
        self.load_contracts()
        self.update_button_states()

    def build(self):
        ctrl = ttk.Frame(self.root)
        ctrl.pack(fill="x", padx=5, pady=2)
        ttk.Label(ctrl, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        entry = ttk.Entry(ctrl, textvariable=self.filter_var, width=22)
        entry.pack(side="left", padx=5)
        entry.bind("<Return>", lambda e: self.load_contracts())
        ttk.Button(ctrl, text="Search", command=self.load_contracts).pack(side="left", padx=2)
        ttk.Button(ctrl, text="Clear", command=lambda: [self.filter_var.set(""), self.load_contracts()]).pack(side="left", padx=2)
        ttk.Separator(ctrl, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(ctrl, text="Refresh All", command=self.refresh_all).pack(side="left", padx=2)

        self.status_var = tk.StringVar(value="Select a contract...")
        ttk.Label(self.root, textvariable=self.status_var, foreground="#0a58ca").pack(anchor="w", padx=5)

        # MAIN LAYOUT RECOMMENDATION: Keep vertical but reduce heights and use horizontal paned for top
        paned_main = ttk.PanedWindow(self.root, orient="vertical")
        paned_main.pack(fill="both", expand=True, padx=5, pady=3)

        # ---- TOP HORIZONTAL PANED: Contracts | Items side by side to save vertical space ----
        top_h_paned = ttk.PanedWindow(paned_main, orient="horizontal")
        paned_main.add(top_h_paned, weight=3)

        contract_frame = ttk.LabelFrame(top_h_paned, text="1. Contracts")
        top_h_paned.add(contract_frame, weight=2)
        items_frame = ttk.LabelFrame(top_h_paned, text="2. Items (auto-selects first)")
        top_h_paned.add(items_frame, weight=2)

        # Contracts tree - COMPACT height 6 instead of 8
        contract_cols = ("id", "contract_number", "customer", "station", "salesperson", "status", "start_date", "end_date", "active")
        self.contract_tree_wrap = ScrolledTreeview(contract_frame, contract_cols, height=6)
        self.contract_tree_wrap.pack(fill="both", expand=True, padx=2, pady=2)
        self.contract_tree = self.contract_tree_wrap.tree
        self.contract_tree.bind("<<TreeviewSelect>>", self.on_contract_select)

        # Compact contract form - use 2 rows
        cf = ttk.Frame(contract_frame)
        cf.pack(fill="x", padx=2, pady=1)
        ttk.Label(cf, text="Cust:").grid(row=0, column=0, sticky="w")
        self.cust_cb = ttk.Combobox(cf, state="readonly", width=18)
        self.cust_cb.grid(row=0, column=1, padx=1)
        ttk.Label(cf, text="Sales:").grid(row=0, column=2, sticky="w")
        self.sales_cb = ttk.Combobox(cf, state="readonly", width=14)
        self.sales_cb.grid(row=0, column=3, padx=1)
        ttk.Label(cf, text="Sta:").grid(row=0, column=4, sticky="w")
        self.stat_cb = ttk.Combobox(cf, state="readonly", width=12)
        self.stat_cb.grid(row=0, column=5, padx=1)
        self.active_var = tk.IntVar(value=1)
        ttk.Checkbutton(cf, text="Act", variable=self.active_var).grid(row=0, column=6, padx=2)

        ttk.Label(cf, text="#:").grid(row=1, column=0, sticky="w")
        self.num_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.num_var, width=12).grid(row=1, column=1, padx=1, sticky="w")
        ttk.Label(cf, text="Sts:").grid(row=1, column=2, sticky="w")
        self.status_cb = ttk.Combobox(cf, values=["Draft","Active","Completed","Cancelled"], width=10)
        self.status_cb.grid(row=1, column=3, padx=1, sticky="w")
        self.status_cb.set("Draft")
        ttk.Label(cf, text="Start:").grid(row=1, column=4, sticky="w")
        self.start_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.start_var, width=10).grid(row=1, column=5, padx=1, sticky="w")
        ttk.Label(cf, text="End:").grid(row=1, column=6, sticky="w")
        self.end_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.end_var, width=10).grid(row=1, column=7, padx=1, sticky="w")

        btn_cf = ttk.Frame(contract_frame)
        btn_cf.pack(fill="x", padx=2, pady=1)
        ttk.Button(btn_cf, text="New", command=self.clear_contract_form).pack(side="left", padx=1)
        ttk.Button(btn_cf, text="Add", command=self.add_contract).pack(side="left", padx=2)
        ttk.Button(btn_cf, text="Update", command=self.update_contract).pack(side="left", padx=1)
        ttk.Button(btn_cf, text="Toggle Act", command=self.toggle_contract_active).pack(side="left", padx=8)

        # Items
        items_cols = ("id", "commercial", "quantity", "spot_length", "priority", "active")
        self.items_tree_wrap = ScrolledTreeview(items_frame, items_cols, height=6)
        self.items_tree_wrap.pack(fill="both", expand=True, padx=2, pady=2)
        self.items_tree = self.items_tree_wrap.tree
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_select)

        itf = ttk.Frame(items_frame)
        itf.pack(fill="x", padx=2, pady=1)
        ttk.Label(itf, text="Com:").grid(row=0, column=0, sticky="w")
        self.com_cb = ttk.Combobox(itf, state="readonly", width=24)
        self.com_cb.grid(row=0, column=1, padx=1)
        ttk.Label(itf, text="Qty:").grid(row=0, column=2, sticky="w")
        self.qty_var = tk.IntVar(value=0)
        ttk.Entry(itf, textvariable=self.qty_var, width=4).grid(row=0, column=3, padx=1)
        ttk.Label(itf, text="Len:").grid(row=0, column=4, sticky="w")
        self.len_var = tk.IntVar(value=30)
        ttk.Entry(itf, textvariable=self.len_var, width=4).grid(row=0, column=5, padx=1)
        self.item_active = tk.IntVar(value=1)
        ttk.Checkbutton(itf, text="Act", variable=self.item_active).grid(row=0, column=6, padx=2)

        btn_it = ttk.Frame(items_frame)
        btn_it.pack(fill="x", padx=2, pady=1)
        self.add_item_btn = ttk.Button(btn_it, text="Add Item", command=self.add_item)
        self.add_item_btn.pack(side="left", padx=1)
        self.update_item_btn = ttk.Button(btn_it, text="Upd Item", command=self.update_item)
        self.update_item_btn.pack(side="left", padx=1)
        self.item_status_lbl = ttk.Label(btn_it, text=" (select contract)", foreground="gray")
        self.item_status_lbl.pack(side="left", padx=5)

        # ---- RULES: Bottom pane - more compact ----
        rules_frame = ttk.LabelFrame(paned_main, text="3. Contract Item Rules")
        paned_main.add(rules_frame, weight=2)
        rules_cols = ("id", "days_of_week", "start_time", "end_time", "max_spots_per_day", "max_spots_per_week", "allow_news", "allow_special", "active", "pref_program", "pref_stopset", "notes")
        self.rules_tree_wrap = ScrolledTreeview(rules_frame, rules_cols, height=5)
        self.rules_tree_wrap.pack(fill="both", expand=True, padx=2, pady=2)
        self.rules_tree = self.rules_tree_wrap.tree
        self.rules_tree.bind("<<TreeviewSelect>>", self.on_rule_select)

        # Days as checkboxes Mon-Sun instead of text 1,2
        rf_days = ttk.Frame(rules_frame)
        rf_days.pack(fill="x", padx=3, pady=1)
        ttk.Label(rf_days, text="Days:").pack(side="left")
        self.day_vars = {}
        for d in DAY_ORDER:
            var = tk.BooleanVar(value=(d in ["Mon","Tue","Wed","Thu","Fri"]))
            self.day_vars[d] = var
            ttk.Checkbutton(rf_days, text=d, variable=var, command=self.sync_days_from_checkboxes).pack(side="left", padx=2)

        self.days_var = tk.StringVar(value="Mon,Tue,Wed,Thu,Fri")
        ttk.Label(rf_days, textvariable=self.days_var, foreground="gray").pack(side="left", padx=10)

        rf = ttk.Frame(rules_frame)
        rf.pack(fill="x", padx=3, pady=1)
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

        # Preferred row - LIKE search for stopsets
        rf_pref = ttk.Frame(rules_frame)
        rf_pref.pack(fill="x", padx=3, pady=1)
        ttk.Label(rf_pref, text="Pref Prog:").grid(row=0, column=0, sticky="w")
        self.pref_program_cb = ttk.Combobox(rf_pref, state="readonly", width=22)
        self.pref_program_cb.grid(row=0, column=1, padx=3, sticky="w")

        ttk.Label(rf_pref, text="Pref Stopset (LIKE search):").grid(row=0, column=2, sticky="w", padx=(10,2))
        self.pref_stopset_cb = DBSearchableCombobox(rf_pref, width=28, search_func=self.search_stopsets_like)
        self.pref_stopset_cb.grid(row=0, column=3, padx=3, sticky="w")
        ttk.Label(rf_pref, text="Type 2+ chars", foreground="gray").grid(row=0, column=4, sticky="w")

        rf2 = ttk.Frame(rules_frame)
        rf2.pack(fill="x", padx=3, pady=1)
        ttk.Label(rf2, text="Notes:").pack(side="left", padx=2)
        self.notes_var = tk.StringVar()
        ttk.Entry(rf2, textvariable=self.notes_var, width=30).pack(side="left", padx=2)
        self.add_rule_btn = ttk.Button(rf2, text="Add Rule", command=self.add_rule)
        self.add_rule_btn.pack(side="left", padx=8)
        self.update_rule_btn = ttk.Button(rf2, text="Update Rule", command=self.update_rule)
        self.update_rule_btn.pack(side="left", padx=2)
        self.rule_status_lbl = ttk.Label(rf2, text=" (select item)", foreground="gray")
        self.rule_status_lbl.pack(side="left", padx=8)

        sched_row = ttk.Frame(rules_frame)
        sched_row.pack(fill="x", padx=3, pady=4)
        self.schedule_info_var = tk.StringVar(value="Select an Item")
        ttk.Label(sched_row, textvariable=self.schedule_info_var, foreground="gray").pack(side="left", padx=5)
        self.schedule_run_btn = ttk.Button(sched_row, text="Run Schedule", command=self.run_schedule, state="disabled")
        self.schedule_run_btn.pack(side="right", padx=5)

    def sync_days_from_checkboxes(self):
        selected = [d for d, v in self.day_vars.items() if v.get()]
        self.days_var.set(",".join(selected))

    def sync_checkboxes_from_days(self, days_str):
        normalized = normalize_days_to_names(days_str)
        selected_set = set(normalized.split(",")) if normalized else set()
        for d, var in self.day_vars.items():
            var.set(d in selected_set)
        self.days_var.set(normalized)

    def search_stopsets_like(self, text):
        """LIKE search: SELECT ... WHERE name LIKE '%text%' LIMIT 100"""
        con = get_connection()
        cur = con.cursor()
        try:
            # Try a few schema variations
            queries = [
                "SELECT id, COALESCE(name, code, 'Stopset ' || id) as label FROM stopsets WHERE label LIKE ? ORDER BY label LIMIT 100",
                "SELECT id, name as label FROM stopsets WHERE name LIKE ? ORDER BY name LIMIT 100",
                "SELECT id, code as label FROM stopsets WHERE code LIKE ? ORDER BY code LIMIT 100",
            ]
            # Because COALESCE alias can't be used in WHERE in some SQLite versions, try direct columns
            fallback = [
                ("SELECT id, COALESCE(name, code, 'Stopset ' || id) as label FROM stopsets WHERE name LIKE ? OR code LIKE ? ORDER BY label LIMIT 100", 2),
                ("SELECT id, name as label FROM stopsets WHERE name LIKE ? ORDER BY name LIMIT 100", 1),
            ]
            pattern = f"%{text}%"
            for sql, param_count in fallback:
                try:
                    if param_count == 2:
                        cur.execute(sql, (pattern, pattern))
                    else:
                        cur.execute(sql, (pattern,))
                    rows = cur.fetchall()
                    return [(r["id"], r["label"]) for r in rows]
                except:
                    continue
            return []
        finally:
            con.close()

    def update_button_states(self):
        has_contract = self.selected_contract_id is not None
        has_item = self.selected_item_id is not None
        state_c = "normal" if has_contract else "disabled"
        state_i = "normal" if has_item else "disabled"
        if hasattr(self, 'add_item_btn'): self.add_item_btn.config(state=state_c)
        self.update_item_btn.config(state=state_i)
        self.item_status_lbl.config(text=f"→ Contract {self.selected_contract_id}" if has_contract else " (select contract)")
        if hasattr(self, 'add_rule_btn'): self.add_rule_btn.config(state=state_i)
        self.update_rule_btn.config(state="disabled")
        self.rule_status_lbl.config(text=f"→ Item {self.selected_item_id}" if has_item else " (select item)")
        if hasattr(self, 'schedule_run_btn'): self.schedule_run_btn.config(state=state_i)
        self.schedule_info_var.set(f"Ready to schedule Item {self.selected_item_id}" if has_item else "Select an Item")

    def load_lookups(self):
        con = get_connection()
        cur = con.cursor()
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
                self.pref_program_cb["values"] = ["-- Any --"]
                self.pref_program_cb.set("-- Any --")
        finally:
            con.close()

    def load_contracts(self):
        filter_text = self.filter_var.get().strip()
        con = get_connection()
        cur = con.cursor()
        try:
            base = """ SELECT co.id, co.contract_number, c.company_name, s.name as sname,
             sp.first_name || ' ' || sp.last_name as sales_name,
             co.status, co.active, co.start_date, co.end_date, co.description, co.notes,
             co.customer_id, co.salesperson_id, co.station_id
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
                self.contract_tree.insert("", "end", values=(r["id"], r["contract_number"], r["company_name"], r["sname"], r["sales_name"], r["status"], r["start_date"], r["end_date"], r["active"]))
            self.status_var.set(f"Loaded {len(rows)} contracts")
        finally:
            con.close()

    def on_contract_select(self, event):
        sel = self.contract_tree.selection()
        if not sel: return
        vals = self.contract_tree.item(sel[0], "values")
        cid = int(vals[0])
        self.selected_contract_id = cid
        self.selected_item_id = None
        r = self.contract_cache.get(cid)
        if r:
            for name, i in self.customers.items():
                if i == r["customer_id"]:
                    self.cust_cb.set(name); break
            for name, i in self.salespeople.items():
                if i == r["salesperson_id"]:
                    self.sales_cb.set(name); break
            for name, i in self.stations.items():
                if i == r["station_id"]:
                    self.stat_cb.set(name); break
            self.num_var.set(r["contract_number"] or "")
            self.status_cb.set(r["status"] or "Draft")
            self.start_var.set(r["start_date"] or "")
            self.end_var.set(r["end_date"] or "")
            self.active_var.set(r["active"])
            self.load_items_for_contract(cid)
            self.update_button_states()

    def load_items_for_contract(self, contract_id):
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute(""" SELECT ci.id, com.title as title, ci.commercial_title, ci.quantity, ci.spot_length_seconds,
             ci.priority, ci.active, ci.description, ci.commercial_id, ci.contract_id
            FROM contract_items ci LEFT JOIN commercials com ON ci.commercial_id=com.id
            WHERE ci.contract_id=? ORDER BY ci.id """, (contract_id,))
            rows = cur.fetchall()
            self.items_tree.delete(*self.items_tree.get_children())
            self.item_cache = {r["id"]: r for r in rows}
            for r in rows:
                disp_title = r["title"] or r["commercial_title"] or "(no title)"
                self.items_tree.insert("", "end", values=(r["id"], disp_title, r["quantity"], r["spot_length_seconds"], r["priority"], r["active"]))
            self.rules_tree.delete(*self.rules_tree.get_children())
            self.status_var.set(f"Contract {contract_id}: {len(rows)} items")
            if rows:
                first = self.items_tree.get_children()[0]
                self.items_tree.selection_set(first)
                self.items_tree.focus(first)
                self.items_tree.see(first)
                self.root.after(10, lambda: self.on_item_select(None))
        finally:
            con.close()

    def on_item_select(self, event):
        sel = self.items_tree.selection()
        if not sel: return
        vals = self.items_tree.item(sel[0], "values")
        item_id = int(vals[0])
        self.selected_item_id = item_id
        r = self.item_cache.get(item_id)
        if r:
            for name, i in self.commercials.items():
                if i == r["commercial_id"]:
                    self.com_cb.set(name); break
            else:
                self.com_cb.set(r["commercial_title"] or "")
            self.qty_var.set(r["quantity"] or 0)
            self.len_var.set(r["spot_length_seconds"] or 30)
            self.item_active.set(r["active"])
            self.load_rules_for_item(item_id)
            self.update_button_states()

    def load_rules_for_item(self, item_id):
        con = get_connection()
        cur = con.cursor()
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
                # stopset label - we don't have all, so show id; on select we resolve
                stop_id = r["preferred_stopset_id"]
                pref_stop_disp = f"[{stop_id}]" if stop_id else ""
                if stop_id and stop_id in self.stopsets_by_id:
                    pref_stop_disp = f"{self.stopsets_by_id[stop_id]} [{stop_id}]"
                days_norm = normalize_days_to_names(r["days_of_week"])
                self.rules_tree.insert("", "end", values=(r["id"], days_norm, r["start_time"], r["end_time"], r["max_spots_per_day"], r["max_spots_per_week"], r["allow_news"], r["allow_special_events"], r["active"], pref_prog_disp, pref_stop_disp, r["notes"]))
            self.status_var.set(f"Item {item_id}: {len(rows)} rules")
        finally:
            con.close()

    def on_rule_select(self, event):
        sel = self.rules_tree.selection()
        if not sel: return
        rid = int(self.rules_tree.item(sel[0], "values")[0])
        r = self.rule_cache.get(rid)
        if not r: return
        self.sync_checkboxes_from_days(r["days_of_week"] or "")
        self.rule_start.set(r["start_time"] or "")
        self.rule_end.set(r["end_time"] or "")
        self.per_day.set(r["max_spots_per_day"] or 0)
        self.per_week.set(r["max_spots_per_week"] or 0)
        self.allow_news.set(r["allow_news"])
        self.allow_spec.set(r["allow_special_events"])
        self.rule_active.set(r["active"])
        self.notes_var.set(r["notes"] or "")
        prog_id = r["preferred_program_id"]
        stop_id = r["preferred_stopset_id"]
        if prog_id and prog_id in self.programs_by_id:
            self.pref_program_cb.set(self.programs_by_id[prog_id])
        else:
            self.pref_program_cb.set("-- Any --")
        # resolve stopset label for display
        if stop_id:
            # try to fetch label
            con = get_connection()
            cur = con.cursor()
            try:
                cur.execute("SELECT COALESCE(name, code, 'Stopset ' || id) as label FROM stopsets WHERE id=?", (stop_id,))
                row = cur.fetchone()
                label = row["label"] if row else f"Stopset {stop_id}"
                self.stopsets_by_id[stop_id] = label
                self.pref_stopset_cb.set_resolved(stop_id, label)
            except:
                self.pref_stopset_cb.set_resolved(stop_id, f"Stopset {stop_id}")
            finally:
                con.close()
        else:
            self.pref_stopset_cb.set_id(None)
        self.update_rule_btn.config(state="normal")

    def refresh_all(self):
        self.load_lookups()
        self.load_contracts()
        self.items_tree.delete(*self.items_tree.get_children())
        self.rules_tree.delete(*self.rules_tree.get_children())
        self.selected_contract_id = None
        self.selected_item_id = None
        self.update_button_states()

    def clear_contract_form(self):
        self.selected_contract_id = None
        self.selected_item_id = None
        self.contract_tree.selection_remove(self.contract_tree.selection())
        self.items_tree.delete(*self.items_tree.get_children())
        self.rules_tree.delete(*self.rules_tree.get_children())
        self.cust_cb.set(""); self.sales_cb.set(""); self.stat_cb.set("")
        self.num_var.set(""); self.status_cb.set("Draft")
        self.start_var.set(""); self.end_var.set("")
        self.active_var.set(1)
        self.update_button_states()
        self.status_var.set("New contract")

    def add_contract(self):
        cust_id = self.customers.get(self.cust_cb.get())
        sales_id = self.salespeople.get(self.sales_cb.get())
        stat_id = self.stations.get(self.stat_cb.get())
        if not cust_id or not sales_id or not stat_id:
            messagebox.showwarning("Validation", "Select customer, salesperson, and station"); return
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" INSERT INTO contracts (customer_id, salesperson_id, station_id, contract_number, description, status, start_date, end_date, notes, active, created_date, modified_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?) """,
                        (cust_id, sales_id, stat_id, self.num_var.get().strip(), "", self.status_cb.get(), self.start_var.get().strip() or None, self.end_var.get().strip() or None, "", self.active_var.get(), now_str(), now_str()))
            con.commit(); self.load_contracts()
        except Exception as e: messagebox.showerror("Error", str(e))
        finally: con.close()

    def update_contract(self):
        if not self.selected_contract_id: messagebox.showwarning("Select", "Select a contract"); return
        cust_id = self.customers.get(self.cust_cb.get()); sales_id = self.salespeople.get(self.sales_cb.get()); stat_id = self.stations.get(self.stat_cb.get())
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" UPDATE contracts SET customer_id=?, salesperson_id=?, station_id=?, contract_number=?, status=?, start_date=?, end_date=?, active=?, modified_date=? WHERE id=? """,
                        (cust_id, sales_id, stat_id, self.num_var.get().strip(), self.status_cb.get(), self.start_var.get().strip() or None, self.end_var.get().strip() or None, self.active_var.get(), now_str(), self.selected_contract_id))
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

    def add_item(self):
        if not self.selected_contract_id: messagebox.showwarning("Select", "Select a contract first"); return
        com_id = self.commercials.get(self.com_cb.get())
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" INSERT INTO contract_items (contract_id, commercial_id, commercial_title, quantity, spot_length_seconds, priority, description, active, created_date, modified_date) VALUES (?,?,?,?,?,?,?,?,?,?) """,
                        (self.selected_contract_id, com_id, self.com_cb.get().strip(), self.qty_var.get(), self.len_var.get(), 1, "", self.item_active.get(), now_str(), now_str()))
            con.commit(); self.load_items_for_contract(self.selected_contract_id)
        except Exception as e: messagebox.showerror("Error", str(e))
        finally: con.close()

    def update_item(self):
        if not self.selected_item_id: return
        com_id = self.commercials.get(self.com_cb.get())
        con = get_connection(); cur = con.cursor()
        try:
            cur.execute(""" UPDATE contract_items SET commercial_id=?, commercial_title=?, quantity=?, spot_length_seconds=?, active=?, modified_date=? WHERE id=? """,
                        (com_id, self.com_cb.get().strip(), self.qty_var.get(), self.len_var.get(), self.item_active.get(), now_str(), self.selected_item_id))
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
