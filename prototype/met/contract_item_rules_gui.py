# File: prototype/met/contract_item_rules_gui.py

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
        self.root=root; root.title("Contract Item Rules"); root.geometry("1150x550")
        self.items={}
        self.build(); self.load_items(); self.load()
    def build(self):
        top=ttk.Frame(self.root); top.pack(fill='x',padx=5,pady=3)
        ttk.Label(top,text="Filter days/start/end:").pack(side='left'); self.filter_var=tk.StringVar(); e=ttk.Entry(top,textvariable=self.filter_var,width=25); e.pack(side='left',padx=5); e.bind("<KeyRelease>", lambda _: self.apply_filter())
        ttk.Button(top,text="Clear",command=lambda:[self.filter_var.set(""),self.apply_filter()]).pack(side='left'); ttk.Button(top,text="Refresh",command=self.load).pack(side='right')
        form=ttk.Frame(self.root); form.pack(fill='x',padx=5,pady=2)
        self.item_cb=ttk.Combobox(form,state='readonly',width=10); self.item_cb.grid(row=0,column=0,padx=2)
        self.days=tk.StringVar(); ttk.Entry(form,textvariable=self.days,width=18).grid(row=0,column=1,padx=2)
        self.start=tk.StringVar(); ttk.Entry(form,textvariable=self.start,width=8).grid(row=0,column=2,padx=2)
        self.end=tk.StringVar(); ttk.Entry(form,textvariable=self.end,width=8).grid(row=0,column=3,padx=2)
        self.spd=tk.IntVar(); ttk.Entry(form,textvariable=self.spd,width=5).grid(row=0,column=4,padx=2)
        self.spw=tk.IntVar(); ttk.Entry(form,textvariable=self.spw,width=5).grid(row=0,column=5,padx=2)
        self.allow_news=tk.IntVar(value=1); ttk.Checkbutton(form,text="News",variable=self.allow_news).grid(row=0,column=6,padx=2)
        self.allow_spec=tk.IntVar(value=1); ttk.Checkbutton(form,text="Special",variable=self.allow_spec).grid(row=0,column=7,padx=2)
        self.active=tk.IntVar(value=1); ttk.Checkbutton(form,text="Active",variable=self.active).grid(row=0,column=8,padx=2)
        ttk.Button(form,text="Add",command=self.add).grid(row=0,column=9,padx=3); ttk.Button(form,text="Update",command=self.update).grid(row=0,column=10,padx=3)
        cols=("id","contract_item","days","start","end","per_day","per_week","active")
        self.wrap=ScrolledTreeview(self.root,cols,height=15); self.wrap.pack(fill='both',expand=True,padx=5,pady=5)
        self.tree=self.wrap.tree; self.tree.bind("<<TreeviewSelect>>",self.on_select); self.all_rows=[]
    def load_items(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT id FROM contract_items ORDER BY id DESC")
        self.items={str(r["id"]):r["id"] for r in cur.fetchall()}; self.item_cb["values"]=list(self.items.keys()); con.close()
    def load(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT id,contract_item_id,days_of_week,start_time,end_time,spots_per_day,spots_per_week,active FROM contract_item_rules ORDER BY id DESC")
        self.all_rows=[dict(r) for r in cur.fetchall()]; con.close(); self.apply_filter()
    def apply_filter(self):
        f=self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for r in self.all_rows:
            if f and f not in f"{r['days_of_week'] or ''} {r['start_time'] or ''} {r['end_time'] or ''}".lower(): continue
            self.tree.insert("", "end", values=(r["id"],r["contract_item_id"],r["days_of_week"],r["start_time"],r["end_time"],r["spots_per_day"],r["spots_per_week"],r["active"]))
    def on_select(self,e):
        sel=self.tree.selection()
        if not sel: return
        rid=int(self.tree.item(sel[0],"values")[0])
        for r in self.all_rows:
            if r["id"]==rid:
                self.item_cb.set(str(r["contract_item_id"])); self.days.set(r["days_of_week"] or ""); self.start.set(r["start_time"] or ""); self.end.set(r["end_time"] or ""); self.spd.set(r["spots_per_day"] or 0); self.spw.set(r["spots_per_week"] or 0); self.active.set(r["active"]); break
    def add(self):
        item_id=self.items.get(self.item_cb.get())
        if not item_id: return
        con=get_connection(); cur=con.cursor()
        cur.execute("INSERT INTO contract_item_rules (contract_item_id,days_of_week,start_time,end_time,spots_per_day,spots_per_week,allow_news,allow_special_events,active,created_date,modified_date) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(item_id,self.days.get().strip(),self.start.get().strip(),self.end.get().strip(),self.spd.get(),self.spw.get(),self.allow_news.get(),self.allow_spec.get(),self.active.get(),now_str(),now_str())); con.commit(); con.close(); self.load()
    def update(self):
        sel=self.tree.selection()
        if not sel: return
        rid=self.tree.item(sel[0],"values")[0]; item_id=self.items.get(self.item_cb.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("UPDATE contract_item_rules SET contract_item_id=?,days_of_week=?,start_time=?,end_time=?,spots_per_day=?,spots_per_week=?,allow_news=?,allow_special_events=?,active=?,modified_date=? WHERE id=?",(item_id,self.days.get().strip(),self.start.get().strip(),self.end.get().strip(),self.spd.get(),self.spw.get(),self.allow_news.get(),self.allow_spec.get(),self.active.get(),now_str(),rid)); con.commit(); con.close(); self.load()
if __name__=="__main__":
    root=tk.Tk(); GUI(root); root.mainloop()
