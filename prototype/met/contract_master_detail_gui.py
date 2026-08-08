# File: prototype/met/contract_master_detail_gui.py

import sys
import pathlib
# Find zbTraffic root by looking for traffic/ folder
_HERE = pathlib.Path(__file__).resolve()
# Check _HERE.parent first (if file is in project root), then all parents
for _p in [_HERE.parent, *_HERE.parents]:
    if (_p / "traffic").is_dir():
        # Found project root
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from traffic.database import get_connection

def now_str():
    return datetime.now().isoformat(sep=' ', timespec='seconds')

class ScrolledTreeview(ttk.Frame):
    def __init__(self, parent, columns, height=6, **kwargs):
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
            self.tree.heading(c, text=c)
            w=120
            if c in ("description", "company_name", "commercial_title", "contract_number"):
                w=200
            if c == "id":
                w=50
            self.tree.column(c, width=w, minwidth=50, stretch=True)

class ContractMasterDetailGUI:
    def __init__(self, root):
        self.root = root
        root.title("zbTraffic - Contract -> Items -> Rules Master-Detail")
        root.geometry("1200x850")
        
        self.customers = {}
        self.salespeople = {}
        self.stations = {}
        self.commercials = {}
        self.contract_cache = {}
        self.item_cache = {}
        self.rule_cache = {}
        
        self.selected_contract_id = None
        self.selected_item_id = None
        
        self.build()
        self.load_lookups()
        self.load_contracts()

    def build(self):
        # ---- Top controls ----
        ctrl = ttk.Frame(self.root)
        ctrl.pack(fill="x", padx=5, pady=3)
        
        ttk.Label(ctrl, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        entry = ttk.Entry(ctrl, textvariable=self.filter_var, width=25)
        entry.pack(side="left", padx=5)
        entry.bind("<Return>", lambda e: self.load_contracts())
        ttk.Button(ctrl, text="Search", command=self.load_contracts).pack(side="left", padx=3)
        ttk.Button(ctrl, text="Clear", command=lambda: [self.filter_var.set(""), self.load_contracts()]).pack(side="left", padx=3)
        
        ttk.Separator(ctrl, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Button(ctrl, text="Refresh All", command=self.refresh_all).pack(side="left", padx=3)
        ttk.Button(ctrl, text="Open Items GUI", command=self.open_items_gui).pack(side="right", padx=3)
        ttk.Button(ctrl, text="Open Rules GUI", command=self.open_rules_gui).pack(side="right", padx=3)
        
        self.status_var = tk.StringVar(value="Select a contract to see its items...")
        ttk.Label(self.root, textvariable=self.status_var, foreground="blue").pack(anchor="w", padx=5)
        
        # ---- Paned Window for resizable sections ----
        paned = ttk.PanedWindow(self.root, orient="vertical")
        paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ---- CONTRACTS Section ----
        contract_frame = ttk.LabelFrame(paned, text="1. Contracts (Top Level) - Click to load items")
        paned.add(contract_frame, weight=2)
        
        contract_cols = ("id", "contract_number", "customer", "station", "salesperson", "status", "active", "start_date", "end_date", "description")
        self.contract_tree_wrap = ScrolledTreeview(contract_frame, contract_cols, height=8)
        self.contract_tree_wrap.pack(fill="both", expand=True, padx=3, pady=3)
        self.contract_tree = self.contract_tree_wrap.tree
        self.contract_tree.bind("<<TreeviewSelect>>", self.on_contract_select)
        
        # Contract form
        cf = ttk.Frame(contract_frame)
        cf.pack(fill="x", padx=3, pady=2)
        ttk.Label(cf, text="Cust:").grid(row=0, column=0, sticky="w")
        self.cust_cb = ttk.Combobox(cf, state="readonly", width=20)
        self.cust_cb.grid(row=0, column=1, padx=2, pady=1)
        ttk.Label(cf, text="Sales:").grid(row=0, column=2, sticky="w")
        self.sales_cb = ttk.Combobox(cf, state="readonly", width=18)
        self.sales_cb.grid(row=0, column=3, padx=2)
        ttk.Label(cf, text="Station:").grid(row=0, column=4, sticky="w")
        self.stat_cb = ttk.Combobox(cf, state="readonly", width=15)
        self.stat_cb.grid(row=0, column=5, padx=2)
        ttk.Label(cf, text="Num:").grid(row=1, column=0, sticky="w")
        self.num_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.num_var, width=15).grid(row=1, column=1, padx=2, sticky="w")
        ttk.Label(cf, text="Status:").grid(row=1, column=2, sticky="w")
        self.status_cb = ttk.Combobox(cf, values=["Draft", "Active", "Completed", "Cancelled"], width=12)
        self.status_cb.grid(row=1, column=3, padx=2, sticky="w")
        self.status_cb.set("Draft")
        ttk.Label(cf, text="Desc:").grid(row=1, column=4, sticky="w")
        self.desc_var = tk.StringVar()
        ttk.Entry(cf, textvariable=self.desc_var, width=30).grid(row=1, column=5, padx=2, sticky="w")
        self.active_var = tk.IntVar(value=1)
        ttk.Checkbutton(cf, text="Active", variable=self.active_var).grid(row=1, column=6, padx=5)
        
        btn_cf = ttk.Frame(contract_frame)
        btn_cf.pack(fill="x", padx=3, pady=1)
        ttk.Button(btn_cf, text="Add Contract", command=self.add_contract).pack(side="left", padx=2)
        ttk.Button(btn_cf, text="Update Contract", command=self.update_contract).pack(side="left", padx=2)
        
        # ---- CONTRACT ITEMS Section ----
        items_frame = ttk.LabelFrame(paned, text="2. Contract Items (Middle) - Click to load rules")
        paned.add(items_frame, weight=2)
        
        items_cols = ("id", "commercial", "commercial_title", "quantity", "spot_length", "priority", "active", "description", "created_date")
        self.items_tree_wrap = ScrolledTreeview(items_frame, items_cols, height=7)
        self.items_tree_wrap.pack(fill="both", expand=True, padx=3, pady=3)
        self.items_tree = self.items_tree_wrap.tree
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_select)
        
        # Item form
        itf = ttk.Frame(items_frame)
        itf.pack(fill="x", padx=3, pady=2)
        ttk.Label(itf, text="Commercial:").grid(row=0, column=0, sticky="w")
        self.com_cb = ttk.Combobox(itf, state="readonly", width=30)
        self.com_cb.grid(row=0, column=1, padx=2)
        ttk.Label(itf, text="Qty:").grid(row=0, column=2, sticky="w")
        self.qty_var = tk.IntVar(value=0)
        ttk.Entry(itf, textvariable=self.qty_var, width=6).grid(row=0, column=3, padx=2)
        ttk.Label(itf, text="Len:").grid(row=0, column=4, sticky="w")
        self.len_var = tk.IntVar(value=30)
        ttk.Entry(itf, textvariable=self.len_var, width=6).grid(row=0, column=5, padx=2)
        ttk.Label(itf, text="Prio:").grid(row=0, column=6, sticky="w")
        self.prio_var = tk.IntVar(value=1)
        ttk.Entry(itf, textvariable=self.prio_var, width=6).grid(row=0, column=7, padx=2)
        self.item_active = tk.IntVar(value=1)
        ttk.Checkbutton(itf, text="Active", variable=self.item_active).grid(row=0, column=8, padx=5)
        ttk.Label(itf, text="Desc:").grid(row=1, column=0, sticky="w")
        self.item_desc = tk.StringVar()
        ttk.Entry(itf, textvariable=self.item_desc, width=50).grid(row=1, column=1, columnspan=4, padx=2, sticky="w")
        
        btn_it = ttk.Frame(items_frame)
        btn_it.pack(fill="x", padx=3, pady=1)
        ttk.Button(btn_it, text="Add Item to Selected Contract", command=self.add_item).pack(side="left", padx=2)
        ttk.Button(btn_it, text="Update Selected Item", command=self.update_item).pack(side="left", padx=2)
        
        # ---- RULES Section ----
        rules_frame = ttk.LabelFrame(paned, text="3. Contract Item Rules (Bottom) - Dayparts and scheduling rules")
        paned.add(rules_frame, weight=2)
        
        rules_cols = ("id", "contract_item_id", "days_of_week", "start_time", "end_time", "spots_per_day", "spots_per_week", "allow_news", "allow_special", "active", "notes")
        self.rules_tree_wrap = ScrolledTreeview(rules_frame, rules_cols, height=6)
        self.rules_tree_wrap.pack(fill="both", expand=True, padx=3, pady=3)
        self.rules_tree = self.rules_tree_wrap.tree
        
        # Rule form
        rf = ttk.Frame(rules_frame)
        rf.pack(fill="x", padx=3, pady=2)
        ttk.Label(rf, text="Days:").grid(row=0, column=0, sticky="w")
        self.days_var = tk.StringVar(value="1,2,3,4,5")
        ttk.Entry(rf, textvariable=self.days_var, width=20).grid(row=0, column=1, padx=2)
        ttk.Label(rf, text="Start:").grid(row=0, column=2, sticky="w")
        self.rule_start = tk.StringVar()
        ttk.Entry(rf, textvariable=self.rule_start, width=8).grid(row=0, column=3, padx=2)
        ttk.Label(rf, text="End:").grid(row=0, column=4, sticky="w")
        self.rule_end = tk.StringVar()
        ttk.Entry(rf, textvariable=self.rule_end, width=8).grid(row=0, column=5, padx=2)
        ttk.Label(rf, text="Per Day:").grid(row=0, column=6, sticky="w")
        self.per_day = tk.IntVar()
        ttk.Entry(rf, textvariable=self.per_day, width=6).grid(row=0, column=7, padx=2)
        ttk.Label(rf, text="Per Week:").grid(row=0, column=8, sticky="w")
        self.per_week = tk.IntVar()
        ttk.Entry(rf, textvariable=self.per_week, width=6).grid(row=0, column=9, padx=2)
        
        rf2 = ttk.Frame(rules_frame)
        rf2.pack(fill="x", padx=3, pady=1)
        self.allow_news = tk.IntVar(value=1)
        ttk.Checkbutton(rf2, text="Allow News", variable=self.allow_news).pack(side="left", padx=5)
        self.allow_spec = tk.IntVar(value=1)
        ttk.Checkbutton(rf2, text="Allow Special", variable=self.allow_spec).pack(side="left", padx=5)
        self.rule_active = tk.IntVar(value=1)
        ttk.Checkbutton(rf2, text="Active", variable=self.rule_active).pack(side="left", padx=5)
        ttk.Label(rf2, text="Notes:").pack(side="left", padx=5)
        self.notes_var = tk.StringVar()
        ttk.Entry(rf2, textvariable=self.notes_var, width=30).pack(side="left", padx=2)
        ttk.Button(rf2, text="Add Rule", command=self.add_rule).pack(side="left", padx=10)
        ttk.Button(rf2, text="Update Rule", command=self.update_rule).pack(side="left", padx=2)

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
        finally:
            con.close()

    def load_contracts(self):
        filter_text = self.filter_var.get().strip()
        con = get_connection()
        cur = con.cursor()
        try:
            if filter_text:
                cur.execute("""
                    SELECT co.id, co.contract_number, c.company_name, s.name as sname, 
                           sp.first_name || ' ' || sp.last_name as sales_name,
                           co.status, co.active, co.start_date, co.end_date, co.description,
                           co.customer_id, co.salesperson_id, co.station_id
                    FROM contracts co
                    JOIN customers c ON co.customer_id=c.id
                    JOIN stations s ON co.station_id=s.id
                    JOIN salespeople sp ON co.salesperson_id=sp.id
                    WHERE co.contract_number LIKE ? OR c.company_name LIKE ?
                    ORDER BY co.id DESC
                """, (f"%{filter_text}%", f"%{filter_text}%"))
            else:
                cur.execute("""
                    SELECT co.id, co.contract_number, c.company_name, s.name as sname, 
                           sp.first_name || ' ' || sp.last_name as sales_name,
                           co.status, co.active, co.start_date, co.end_date, co.description,
                           co.customer_id, co.salesperson_id, co.station_id
                    FROM contracts co
                    JOIN customers c ON co.customer_id=c.id
                    JOIN stations s ON co.station_id=s.id
                    JOIN salespeople sp ON co.salesperson_id=sp.id
                    ORDER BY co.id DESC
                """)
            rows = cur.fetchall()
            self.contract_tree.delete(*self.contract_tree.get_children())
            self.contract_cache = {r["id"]: r for r in rows}
            for r in rows:
                self.contract_tree.insert("", "end", values=(
                    r["id"], r["contract_number"], r["company_name"], r["sname"],
                    r["sales_name"], r["status"], r["active"], r["start_date"], r["end_date"], r["description"]
                ))
            self.status_var.set(f"Loaded {len(rows)} contracts. Select one to see items.")
        finally:
            con.close()

    def on_contract_select(self, event):
        sel = self.contract_tree.selection()
        if not sel:
            return
        vals = self.contract_tree.item(sel[0], "values")
        cid = int(vals[0])
        self.selected_contract_id = cid
        
        r = self.contract_cache.get(cid)
        if r:
            # Fill form - reverse lookup
            for name, i in self.customers.items():
                if i == r["customer_id"]:
                    self.cust_cb.set(name)
                    break
            for name, i in self.salespeople.items():
                if i == r["salesperson_id"]:
                    self.sales_cb.set(name)
                    break
            for name, i in self.stations.items():
                if i == r["station_id"]:
                    self.stat_cb.set(name)
                    break
            self.num_var.set(r["contract_number"] or "")
            self.status_cb.set(r["status"] or "Draft")
            self.desc_var.set(r["description"] or "")
            self.active_var.set(r["active"])
        
        self.load_items_for_contract(cid)

    def load_items_for_contract(self, contract_id):
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT ci.id, com.title, ci.commercial_title, ci.quantity, ci.spot_length_seconds, 
                       ci.priority, ci.active, ci.description, ci.created_date, ci.commercial_id, ci.contract_id
                FROM contract_items ci
                LEFT JOIN commercials com ON ci.commercial_id=com.id
                WHERE ci.contract_id=?
                ORDER BY ci.id
            """, (contract_id,))
            rows = cur.fetchall()
            self.items_tree.delete(*self.items_tree.get_children())
            self.item_cache = {r["id"]: r for r in rows}
            for r in rows:
                self.items_tree.insert("", "end", values=(
                    r["id"], r["title"], r["commercial_title"], r["quantity"],
                    r["spot_length_seconds"], r["priority"], r["active"], r["description"], r["created_date"]
                ))
            # Clear rules
            self.rules_tree.delete(*self.rules_tree.get_children())
            self.status_var.set(f"Contract {contract_id}: {len(rows)} items. Select an item to see its rules.")
        finally:
            con.close()

    def on_item_select(self, event):
        sel = self.items_tree.selection()
        if not sel:
            return
        vals = self.items_tree.item(sel[0], "values")
        item_id = int(vals[0])
        self.selected_item_id = item_id
        
        r = self.item_cache.get(item_id)
        if r:
            for name, i in self.commercials.items():
                if i == r["commercial_id"]:
                    self.com_cb.set(name)
                    break
            self.qty_var.set(r["quantity"] or 0)
            self.len_var.set(r["spot_length_seconds"] or 30)
            self.prio_var.set(r["priority"] or 1)
            self.item_desc.set(r["description"] or "")
            self.item_active.set(r["active"])
        
        self.load_rules_for_item(item_id)

    def load_rules_for_item(self, item_id):
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT id, contract_item_id, days_of_week, start_time, end_time, 
                       spots_per_day, spots_per_week, allow_news, allow_special_events, active, notes
                FROM contract_item_rules
                WHERE contract_item_id=?
                ORDER BY id
            """, (item_id,))
            rows = cur.fetchall()
            self.rules_tree.delete(*self.rules_tree.get_children())
            self.rule_cache = {r["id"]: r for r in rows}
            for r in rows:
                self.rules_tree.insert("", "end", values=(
                    r["id"], r["contract_item_id"], r["days_of_week"], r["start_time"], r["end_time"],
                    r["spots_per_day"], r["spots_per_week"], r["allow_news"], r["allow_special_events"], r["active"], r["notes"]
                ))
            self.status_var.set(f"Contract Item {item_id}: {len(rows)} rules.")
        finally:
            con.close()

    def refresh_all(self):
        self.load_lookups()
        self.load_contracts()
        self.items_tree.delete(*self.items_tree.get_children())
        self.rules_tree.delete(*self.rules_tree.get_children())

    # ---- CRUD actions ----
    def add_contract(self):
        cust_id = self.customers.get(self.cust_cb.get())
        sales_id = self.salespeople.get(self.sales_cb.get())
        stat_id = self.stations.get(self.stat_cb.get())
        if not cust_id or not sales_id or not stat_id:
            messagebox.showwarning("Validation", "Select customer, salesperson, and station")
            return
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO contracts (customer_id, salesperson_id, station_id, contract_number, description, status, active, created_date, modified_date)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (cust_id, sales_id, stat_id, self.num_var.get().strip(), self.desc_var.get().strip(), self.status_cb.get(), self.active_var.get(), now_str(), now_str()))
            con.commit()
            self.load_contracts()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            con.close()

    def update_contract(self):
        if not self.selected_contract_id:
            return
        cust_id = self.customers.get(self.cust_cb.get())
        sales_id = self.salespeople.get(self.sales_cb.get())
        stat_id = self.stations.get(self.stat_cb.get())
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                UPDATE contracts SET customer_id=?, salesperson_id=?, station_id=?, contract_number=?, description=?, status=?, active=?, modified_date=?
                WHERE id=?
            """, (cust_id, sales_id, stat_id, self.num_var.get().strip(), self.desc_var.get().strip(), self.status_cb.get(), self.active_var.get(), now_str(), self.selected_contract_id))
            con.commit()
            self.load_contracts()
        finally:
            con.close()

    def add_item(self):
        if not self.selected_contract_id:
            messagebox.showwarning("Select", "Select a contract first")
            return
        com_id = self.commercials.get(self.com_cb.get())
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO contract_items (contract_id, commercial_id, quantity, spot_length_seconds, priority, description, active, created_date, modified_date)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (self.selected_contract_id, com_id, self.qty_var.get(), self.len_var.get(), self.prio_var.get(), self.item_desc.get().strip(), self.item_active.get(), now_str(), now_str()))
            con.commit()
            self.load_items_for_contract(self.selected_contract_id)
        finally:
            con.close()

    def update_item(self):
        if not self.selected_item_id:
            return
        com_id = self.commercials.get(self.com_cb.get())
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                UPDATE contract_items SET commercial_id=?, quantity=?, spot_length_seconds=?, priority=?, description=?, active=?, modified_date=?
                WHERE id=?
            """, (com_id, self.qty_var.get(), self.len_var.get(), self.prio_var.get(), self.item_desc.get().strip(), self.item_active.get(), now_str(), self.selected_item_id))
            con.commit()
            self.load_items_for_contract(self.selected_contract_id)
        finally:
            con.close()

    def add_rule(self):
        if not self.selected_item_id:
            messagebox.showwarning("Select", "Select a contract item first")
            return
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO contract_item_rules (contract_item_id, days_of_week, start_time, end_time, spots_per_day, spots_per_week, allow_news, allow_special_events, active, notes, created_date, modified_date)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (self.selected_item_id, self.days_var.get().strip(), self.rule_start.get().strip(), self.rule_end.get().strip(),
                  self.per_day.get(), self.per_week.get(), self.allow_news.get(), self.allow_spec.get(), self.rule_active.get(),
                  self.notes_var.get().strip(), now_str(), now_str()))
            con.commit()
            self.load_rules_for_item(self.selected_item_id)
        finally:
            con.close()

    def update_rule(self):
        sel = self.rules_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a rule to update")
            return
        rid = int(self.rules_tree.item(sel[0], "values")[0])
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                UPDATE contract_item_rules SET days_of_week=?, start_time=?, end_time=?, spots_per_day=?, spots_per_week=?, allow_news=?, allow_special_events=?, active=?, notes=?, modified_date=?
                WHERE id=?
            """, (self.days_var.get().strip(), self.rule_start.get().strip(), self.rule_end.get().strip(),
                  self.per_day.get(), self.per_week.get(), self.allow_news.get(), self.allow_spec.get(), self.rule_active.get(),
                  self.notes_var.get().strip(), now_str(), rid))
            con.commit()
            self.load_rules_for_item(self.selected_item_id)
        finally:
            con.close()

    def open_items_gui(self):
        import subprocess, sys, pathlib
        p = pathlib.Path(__file__).parent / "contract_items_gui.py"
        if p.exists():
            subprocess.Popen([sys.executable, str(p)])

    def open_rules_gui(self):
        import subprocess, sys, pathlib
        p = pathlib.Path(__file__).parent / "contract_item_rules_gui.py"
        if p.exists():
            subprocess.Popen([sys.executable, str(p)])

if __name__ == "__main__":
    root = tk.Tk()
    ContractMasterDetailGUI(root)
    root.mainloop()
