# File: prototype/met/contracts_gui.py

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
    def __init__(self, parent, columns, height=10):
        super().__init__(parent)
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=height)
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
            if c in ("company_name","title","name","description","commercial_title","contract_number","customer","commercial"): w=200
            if c=="id": w=50
            self.tree.column(c, width=w, minwidth=40, stretch=True)

class GUI:
    def __init__(self, root):
        self.root=root; root.title("Contracts"); root.geometry("1100x550")
        self.customers={}; self.salespeople={}; self.stations={}
        self.build(); self.load_lookups(); self.load()
    def build(self):
        top=ttk.Frame(self.root); top.pack(fill='x',padx=5,pady=3)
        ttk.Label(top,text="Filter number/customer:").pack(side='left'); self.filter_var=tk.StringVar(); e=ttk.Entry(top,textvariable=self.filter_var,width=25); e.pack(side='left',padx=5); e.bind("<KeyRelease>", lambda _: self.apply_filter())
        ttk.Button(top,text="Clear",command=lambda:[self.filter_var.set(""),self.apply_filter()]).pack(side='left'); ttk.Button(top,text="Refresh",command=self.load).pack(side='right')
        form=ttk.Frame(self.root); form.pack(fill='x',padx=5,pady=2)
        self.cust_cb=ttk.Combobox(form,state='readonly',width=20); self.cust_cb.grid(row=0,column=0,padx=2)
        self.sales_cb=ttk.Combobox(form,state='readonly',width=18); self.sales_cb.grid(row=0,column=1,padx=2)
        self.stat_cb=ttk.Combobox(form,state='readonly',width=15); self.stat_cb.grid(row=0,column=2,padx=2)
        self.num_var=tk.StringVar(); ttk.Entry(form,textvariable=self.num_var,width=12).grid(row=0,column=3,padx=2)
        self.status_cb=ttk.Combobox(form,values=["Draft","Active","Completed","Cancelled"],width=12); self.status_cb.grid(row=0,column=4,padx=2); self.status_cb.set("Draft")
        self.active_var=tk.IntVar(value=1); ttk.Checkbutton(form,text="Active",variable=self.active_var).grid(row=0,column=5,padx=3)
        self.desc_var=tk.StringVar(); ttk.Entry(form,textvariable=self.desc_var,width=20).grid(row=0,column=6,padx=2)
        ttk.Button(form,text="Add",command=self.add).grid(row=0,column=7,padx=3); ttk.Button(form,text="Update",command=self.update).grid(row=0,column=8,padx=3)
        cols=("id","contract_number","customer","station","status","active","start","end")
        self.wrap=ScrolledTreeview(self.root,cols,height=15); self.wrap.pack(fill='both',expand=True,padx=5,pady=5)
        self.tree=self.wrap.tree; self.tree.bind("<<TreeviewSelect>>",self.on_select); self.all_rows=[]
    def load_lookups(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT id,company_name FROM customers WHERE active=1 ORDER BY company_name")
        self.customers={r["company_name"]:r["id"] for r in cur.fetchall()}; self.cust_cb["values"]=list(self.customers.keys())
        cur.execute("SELECT id,first_name,last_name FROM salespeople WHERE active=1 ORDER BY last_name")
        self.salespeople={f"{r['first_name']} {r['last_name']}":r["id"] for r in cur.fetchall()}; self.sales_cb["values"]=list(self.salespeople.keys())
        cur.execute("SELECT id,name FROM stations WHERE active=1 ORDER BY name")
        self.stations={r["name"]:r["id"] for r in cur.fetchall()}; self.stat_cb["values"]=list(self.stations.keys()); con.close()
    def load(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT co.id,co.contract_number,c.company_name,s.name as sname,co.status,co.active,co.start_date,co.end_date,co.description,co.customer_id,co.salesperson_id,co.station_id FROM contracts co JOIN customers c ON co.customer_id=c.id JOIN stations s ON co.station_id=s.id ORDER BY co.id DESC")
        self.all_rows=[dict(r) for r in cur.fetchall()]; con.close(); self.apply_filter()
    def apply_filter(self):
        f=self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for r in self.all_rows:
            if f and f not in f"{r['contract_number'] or ''} {r['company_name'] or ''}".lower(): continue
            self.tree.insert("", "end", values=(r["id"],r["contract_number"],r["company_name"],r["sname"],r["status"],r["active"],r["start_date"],r["end_date"]))
    def on_select(self,e):
        sel=self.tree.selection()
        if not sel: return
        rid=int(self.tree.item(sel[0],"values")[0])
        for r in self.all_rows:
            if r["id"]==rid:
                for k,v in self.customers.items():
                    if v==r["customer_id"]: self.cust_cb.set(k); break
                for k,v in self.salespeople.items():
                    if v==r["salesperson_id"]: self.sales_cb.set(k); break
                for k,v in self.stations.items():
                    if v==r["station_id"]: self.stat_cb.set(k); break
                self.num_var.set(r["contract_number"] or ""); self.status_cb.set(r["status"] or "Draft"); self.desc_var.set(r["description"] or ""); self.active_var.set(r["active"]); break
    def add(self):
        cust_id=self.customers.get(self.cust_cb.get()); sales_id=self.salespeople.get(self.sales_cb.get()); stat_id=self.stations.get(self.stat_cb.get())
        if not cust_id or not sales_id or not stat_id: return
        con=get_connection(); cur=con.cursor()
        cur.execute("INSERT INTO contracts (customer_id,salesperson_id,station_id,contract_number,description,status,active,created_date,modified_date) VALUES (?,?,?,?,?,?,?,?,?)",(cust_id,sales_id,stat_id,self.num_var.get().strip(),self.desc_var.get().strip(),self.status_cb.get(),self.active_var.get(),now_str(),now_str())); con.commit(); con.close(); self.load()
    def update(self):
        sel=self.tree.selection()
        if not sel: return
        cid=self.tree.item(sel[0],"values")[0]; cust_id=self.customers.get(self.cust_cb.get()); sales_id=self.salespeople.get(self.sales_cb.get()); stat_id=self.stations.get(self.stat_cb.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("UPDATE contracts SET customer_id=?,salesperson_id=?,station_id=?,contract_number=?,description=?,status=?,active=?,modified_date=? WHERE id=?",(cust_id,sales_id,stat_id,self.num_var.get().strip(),self.desc_var.get().strip(),self.status_cb.get(),self.active_var.get(),now_str(),cid)); con.commit(); con.close(); self.load()
if __name__=="__main__":
    root=tk.Tk(); GUI(root); root.mainloop()
