# File: prototype/met/contract_items_gui.py

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
        self.root=root; root.title("Contract Items"); root.geometry("1100x550")
        self.contracts={}; self.commercials={}
        self.build(); self.load_lookups(); self.load()
    def build(self):
        top=ttk.Frame(self.root); top.pack(fill='x',padx=5,pady=3)
        ttk.Label(top,text="Filter commercial/contract:").pack(side='left'); self.filter_var=tk.StringVar(); e=ttk.Entry(top,textvariable=self.filter_var,width=25); e.pack(side='left',padx=5); e.bind("<KeyRelease>", lambda _: self.apply_filter())
        ttk.Button(top,text="Clear",command=lambda:[self.filter_var.set(""),self.apply_filter()]).pack(side='left'); ttk.Button(top,text="Refresh",command=self.load).pack(side='right')
        form=ttk.Frame(self.root); form.pack(fill='x',padx=5,pady=2)
        self.cont_cb=ttk.Combobox(form,state='readonly',width=18); self.cont_cb.grid(row=0,column=0,padx=2)
        self.com_cb=ttk.Combobox(form,state='readonly',width=22); self.com_cb.grid(row=0,column=1,padx=2)
        self.qty=tk.IntVar(value=0); ttk.Entry(form,textvariable=self.qty,width=6).grid(row=0,column=2,padx=2)
        self.len_var=tk.IntVar(value=30); ttk.Entry(form,textvariable=self.len_var,width=6).grid(row=0,column=3,padx=2)
        self.prio=tk.IntVar(value=1); ttk.Entry(form,textvariable=self.prio,width=6).grid(row=0,column=4,padx=2)
        self.desc=tk.StringVar(); ttk.Entry(form,textvariable=self.desc,width=20).grid(row=0,column=5,padx=2)
        self.active=tk.IntVar(value=1); ttk.Checkbutton(form,text="Active",variable=self.active).grid(row=0,column=6,padx=2)
        ttk.Button(form,text="Add",command=self.add).grid(row=0,column=7,padx=3); ttk.Button(form,text="Update",command=self.update).grid(row=0,column=8,padx=3)
        cols=("id","contract","commercial","qty","length","priority","active")
        self.wrap=ScrolledTreeview(self.root,cols,height=15); self.wrap.pack(fill='both',expand=True,padx=5,pady=5)
        self.tree=self.wrap.tree; self.tree.bind("<<TreeviewSelect>>",self.on_select); self.all_rows=[]
    def load_lookups(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT id,contract_number FROM contracts ORDER BY id DESC")
        self.contracts={r["contract_number"] or f"#{r['id']}":r["id"] for r in cur.fetchall()}; self.cont_cb["values"]=list(self.contracts.keys())
        cur.execute("SELECT id,title FROM commercials WHERE active=1 ORDER BY title")
        self.commercials={r["title"]:r["id"] for r in cur.fetchall()}; self.com_cb["values"]=list(self.commercials.keys()); con.close()
    def load(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT ci.id,co.contract_number,com.title,ci.quantity,ci.spot_length_seconds,ci.priority,ci.active,ci.commercial_id,ci.contract_id,ci.description FROM contract_items ci JOIN contracts co ON ci.contract_id=co.id LEFT JOIN commercials com ON ci.commercial_id=com.id ORDER BY ci.id DESC")
        self.all_rows=[dict(r) for r in cur.fetchall()]; con.close(); self.apply_filter()
    def apply_filter(self):
        f=self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for r in self.all_rows:
            if f and f not in f"{r['contract_number'] or ''} {r['title'] or ''}".lower(): continue
            self.tree.insert("", "end", values=(r["id"],r["contract_number"],r["title"],r["quantity"],r["spot_length_seconds"],r["priority"],r["active"]))
    def on_select(self,e):
        sel=self.tree.selection()
        if not sel: return
        rid=int(self.tree.item(sel[0],"values")[0])
        for r in self.all_rows:
            if r["id"]==rid:
                for k,v in self.contracts.items():
                    if v==r["contract_id"]: self.cont_cb.set(k); break
                for k,v in self.commercials.items():
                    if v==r["commercial_id"]: self.com_cb.set(k); break
                self.qty.set(r["quantity"] or 0); self.len_var.set(r["spot_length_seconds"] or 0); self.prio.set(r["priority"] or 1); self.desc.set(r["description"] or ""); self.active.set(r["active"]); break
    def add(self):
        cont_id=self.contracts.get(self.cont_cb.get()); com_id=self.commercials.get(self.com_cb.get())
        if not cont_id: return
        con=get_connection(); cur=con.cursor()
        cur.execute("INSERT INTO contract_items (contract_id,commercial_id,quantity,spot_length_seconds,priority,description,active,created_date,modified_date) VALUES (?,?,?,?,?,?,?,?,?)",(cont_id,com_id,self.qty.get(),self.len_var.get(),self.prio.get(),self.desc.get().strip(),self.active.get(),now_str(),now_str())); con.commit(); con.close(); self.load()
    def update(self):
        sel=self.tree.selection()
        if not sel: return
        iid=self.tree.item(sel[0],"values")[0]; cont_id=self.contracts.get(self.cont_cb.get()); com_id=self.commercials.get(self.com_cb.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("UPDATE contract_items SET contract_id=?,commercial_id=?,quantity=?,spot_length_seconds=?,priority=?,description=?,active=?,modified_date=? WHERE id=?",(cont_id,com_id,self.qty.get(),self.len_var.get(),self.prio.get(),self.desc.get().strip(),self.active.get(),now_str(),iid)); con.commit(); con.close(); self.load()
if __name__=="__main__":
    root=tk.Tk(); GUI(root); root.mainloop()
