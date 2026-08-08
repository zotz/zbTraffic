# File: prototype/met/separation_rules_gui.py

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
        self.root=root; root.title("Separation Rules"); root.geometry("900x500")
        self.cats={}
        self.build(); self.load_cats(); self.load()
    def build(self):
        top=ttk.Frame(self.root); top.pack(fill='x',padx=5,pady=3)
        ttk.Label(top,text="Filter:").pack(side='left'); self.filter_var=tk.StringVar(); e=ttk.Entry(top,textvariable=self.filter_var,width=25); e.pack(side='left',padx=5); e.bind("<KeyRelease>", lambda _: self.apply_filter())
        ttk.Button(top,text="Clear",command=lambda:[self.filter_var.set(""),self.apply_filter()]).pack(side='left'); ttk.Button(top,text="Refresh",command=self.load).pack(side='right')
        f=ttk.Frame(self.root); f.pack(fill='x',padx=5,pady=2)
        self.c1=ttk.Combobox(f,state='readonly',width=18); self.c1.pack(side='left',padx=2)
        self.c2=ttk.Combobox(f,state='readonly',width=18); self.c2.pack(side='left',padx=2)
        self.mins=tk.IntVar(value=30); ttk.Entry(f,textvariable=self.mins,width=6).pack(side='left',padx=2)
        self.active=tk.IntVar(value=1); ttk.Checkbutton(f,text="Active",variable=self.active).pack(side='left',padx=3)
        ttk.Button(f,text="Add",command=self.add).pack(side='left',padx=5); ttk.Button(f,text="Update",command=self.update).pack(side='left',padx=3)
        cols=("id","cat1","cat2","mins","active")
        self.wrap=ScrolledTreeview(self.root,cols,height=15); self.wrap.pack(fill='both',expand=True,padx=5,pady=5)
        self.tree=self.wrap.tree; self.tree.bind("<<TreeviewSelect>>",self.on_select); self.all_rows=[]
    def load_cats(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT id,name FROM categories WHERE active=1 ORDER BY name")
        self.cats={r["name"]:r["id"] for r in cur.fetchall()}; self.c1["values"]=list(self.cats.keys()); self.c2["values"]=list(self.cats.keys()); con.close()
    def load(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT sr.id,c1.name as n1,c2.name as n2,sr.minimum_minutes,sr.active FROM separation_rules sr JOIN categories c1 ON sr.category1_id=c1.id JOIN categories c2 ON sr.category2_id=c2.id ORDER BY c1.name,c2.name")
        self.all_rows=[dict(r) for r in cur.fetchall()]; con.close(); self.apply_filter()
    def apply_filter(self):
        f=self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for r in self.all_rows:
            if f and f not in (f"{r['n1']} {r['n2']}".lower()): continue
            self.tree.insert("", "end", values=(r["id"],r["n1"],r["n2"],r["minimum_minutes"],r["active"]))
    def on_select(self,e):
        sel=self.tree.selection()
        if not sel: return
        v=self.tree.item(sel[0],"values"); self.c1.set(v[1]); self.c2.set(v[2]); self.mins.set(int(v[3])); self.active.set(int(v[4]))
    def add(self):
        id1=self.cats.get(self.c1.get()); id2=self.cats.get(self.c2.get())
        if not id1 or not id2: return
        con=get_connection(); cur=con.cursor()
        cur.execute("INSERT INTO separation_rules (category1_id,category2_id,minimum_minutes,active,created_date,modified_date) VALUES (?,?,?,?,?,?)",(id1,id2,self.mins.get(),self.active.get(),now_str(),now_str())); con.commit(); con.close(); self.load()
    def update(self):
        sel=self.tree.selection()
        if not sel: return
        rid=self.tree.item(sel[0],"values")[0]; id1=self.cats.get(self.c1.get()); id2=self.cats.get(self.c2.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("UPDATE separation_rules SET category1_id=?,category2_id=?,minimum_minutes=?,active=?,modified_date=? WHERE id=?",(id1,id2,self.mins.get(),self.active.get(),now_str(),rid)); con.commit(); con.close(); self.load()
if __name__=="__main__":
    root=tk.Tk(); GUI(root); root.mainloop()
