# File: prototype/met/commercials_gui.py

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
        self.root=root; root.title("Commercials"); root.geometry("1100x600")
        self.customers={}; self.categories={}
        self.build(); self.load_lookups(); self.load()
    def build(self):
        top=ttk.Frame(self.root); top.pack(fill='x',padx=5,pady=3)
        ttk.Label(top,text="Filter title/customer/cart:").pack(side='left')
        self.filter_var=tk.StringVar(); e=ttk.Entry(top,textvariable=self.filter_var,width=30); e.pack(side='left',padx=5); e.bind("<KeyRelease>", lambda _: self.apply_filter())
        ttk.Button(top,text="Clear",command=lambda:[self.filter_var.set(""),self.apply_filter()]).pack(side='left')
        ttk.Button(top,text="Refresh",command=self.load).pack(side='right')
        form=ttk.Frame(self.root); form.pack(fill='x',padx=5,pady=2)
        self.cust_cb=ttk.Combobox(form,state='readonly',width=22); self.cust_cb.grid(row=0,column=0,padx=2)
        self.title_var=tk.StringVar(); ttk.Entry(form,textvariable=self.title_var,width=25).grid(row=0,column=1,padx=2)
        self.length_var=tk.IntVar(value=30); ttk.Entry(form,textvariable=self.length_var,width=5).grid(row=0,column=2,padx=2)
        self.cart_var=tk.StringVar(); ttk.Entry(form,textvariable=self.cart_var,width=12).grid(row=0,column=3,padx=2)
        self.cat_cb=ttk.Combobox(form,state='readonly',width=15); self.cat_cb.grid(row=0,column=4,padx=2)
        self.active_var=tk.IntVar(value=1); ttk.Checkbutton(form,text="Active",variable=self.active_var).grid(row=0,column=5,padx=2)
        ttk.Button(form,text="Add",command=self.add).grid(row=0,column=6,padx=3); ttk.Button(form,text="Update",command=self.update).grid(row=0,column=7,padx=3)
        cols=("id","customer","title","length","cart","category","active")
        self.wrap=ScrolledTreeview(self.root,cols,height=15); self.wrap.pack(fill='both',expand=True,padx=5,pady=5)
        self.tree=self.wrap.tree; self.tree.bind("<<TreeviewSelect>>",self.on_select)
        self.all_rows=[]
    def load_lookups(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT id,company_name FROM customers WHERE active=1 ORDER BY company_name")
        self.customers={r["company_name"]:r["id"] for r in cur.fetchall()}; self.cust_cb["values"]=list(self.customers.keys())
        cur.execute("SELECT id,name FROM categories WHERE active=1 ORDER BY name")
        self.categories={r["name"]:r["id"] for r in cur.fetchall()}; self.cat_cb["values"]=list(self.categories.keys()); con.close()
    def load(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT co.id,c.company_name,co.title,co.length_seconds,co.cart_number,cat.name as cat_name,co.active,co.filename FROM commercials co JOIN customers c ON co.customer_id=c.id LEFT JOIN categories cat ON co.category_id=cat.id ORDER BY c.company_name,co.title")
        self.all_rows=[dict(r) for r in cur.fetchall()]; con.close(); self.apply_filter()
    def apply_filter(self):
        f=self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for r in self.all_rows:
            hay=f"{r['company_name'] or ''} {r['title'] or ''} {r['cart_number'] or ''}".lower()
            if f and f not in hay: continue
            self.tree.insert("", "end", values=(r["id"],r["company_name"],r["title"],r["length_seconds"],r["cart_number"],r["cat_name"],r["active"]))
    def on_select(self,e):
        sel=self.tree.selection()
        if not sel: return
        rid=int(self.tree.item(sel[0],"values")[0])
        for r in self.all_rows:
            if r["id"]==rid:
                self.cust_cb.set(r["company_name"] or ""); self.title_var.set(r["title"] or ""); self.length_var.set(r["length_seconds"] or 30); self.cart_var.set(r["cart_number"] or ""); self.cat_cb.set(r["cat_name"] or ""); self.active_var.set(r["active"]); break
    def add(self):
        cust_id=self.customers.get(self.cust_cb.get())
        if not cust_id or not self.title_var.get().strip(): return
        cat_id=self.categories.get(self.cat_cb.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("INSERT INTO commercials (customer_id,title,length_seconds,cart_number,category_id,active,created_date,modified_date) VALUES (?,?,?,?,?,?,?,?)",(cust_id,self.title_var.get().strip(),self.length_var.get(),self.cart_var.get().strip(),cat_id,self.active_var.get(),now_str(),now_str())); con.commit(); con.close(); self.load()
    def update(self):
        sel=self.tree.selection()
        if not sel: return
        cid=self.tree.item(sel[0],"values")[0]; cust_id=self.customers.get(self.cust_cb.get()); cat_id=self.categories.get(self.cat_cb.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("UPDATE commercials SET customer_id=?,title=?,length_seconds=?,cart_number=?,category_id=?,active=?,modified_date=? WHERE id=?",(cust_id,self.title_var.get().strip(),self.length_var.get(),self.cart_var.get().strip(),cat_id,self.active_var.get(),now_str(),cid)); con.commit(); con.close(); self.load()
if __name__=="__main__":
    root=tk.Tk(); GUI(root); root.mainloop()
