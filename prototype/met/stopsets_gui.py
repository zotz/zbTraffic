# File: prototype/met/stopsets_gui.py

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
        self.root=root; root.title("Stopsets"); root.geometry("1050x500")
        self.programs={}
        self.build(); self.load_programs(); self.load()
    def build(self):
        top=ttk.Frame(self.root); top.pack(fill='x',padx=5,pady=3)
        ttk.Label(top,text="Filter:").pack(side='left'); self.filter_var=tk.StringVar(); e=ttk.Entry(top,textvariable=self.filter_var,width=25); e.pack(side='left',padx=5); e.bind("<KeyRelease>", lambda _: self.apply_filter())
        ttk.Button(top,text="Clear",command=lambda:[self.filter_var.set(""),self.apply_filter()]).pack(side='left'); ttk.Button(top,text="Refresh",command=self.load).pack(side='right')
        f=ttk.Frame(self.root); f.pack(fill='x',padx=5,pady=2)
        self.prog_cb=ttk.Combobox(f,state='readonly',width=25); self.prog_cb.pack(side='left',padx=3)
        self.name_var=tk.StringVar(); ttk.Entry(f,textvariable=self.name_var,width=18).pack(side='left',padx=2)
        self.start_var=tk.StringVar(); ttk.Entry(f,textvariable=self.start_var,width=8).pack(side='left',padx=2)
        self.end_var=tk.StringVar(); ttk.Entry(f,textvariable=self.end_var,width=8).pack(side='left',padx=2)
        self.max_var=tk.IntVar(value=120); ttk.Entry(f,textvariable=self.max_var,width=6).pack(side='left',padx=2)
        self.active_var=tk.IntVar(value=1); ttk.Checkbutton(f,text="Active",variable=self.active_var).pack(side='left',padx=3)
        ttk.Button(f,text="Add",command=self.add).pack(side='left',padx=5); ttk.Button(f,text="Update",command=self.update).pack(side='left',padx=3)
        cols=("id","program","name","start_time","end_time","max_sec","active")
        self.wrap=ScrolledTreeview(self.root,cols,height=15); self.wrap.pack(fill='both',expand=True,padx=5,pady=5)
        self.tree=self.wrap.tree; self.tree.bind("<<TreeviewSelect>>",self.on_select); self.all_rows=[]
    def load_programs(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT p.id,p.name,s.name as sname FROM programs p JOIN stations s ON p.station_id=s.id WHERE p.active=1 ORDER BY s.name,p.name")
        self.programs={f"{r['sname']} - {r['name']}":r["id"] for r in cur.fetchall()}; self.prog_cb["values"]=list(self.programs.keys()); con.close()
    def load(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT ss.id,p.name as pname,ss.name,ss.start_time,ss.end_time,ss.maximum_seconds,ss.active FROM stopsets ss JOIN programs p ON ss.program_id=p.id ORDER BY p.name,ss.start_time")
        self.all_rows=[dict(r) for r in cur.fetchall()]; con.close(); self.apply_filter()
    def apply_filter(self):
        f=self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for r in self.all_rows:
            if f and f not in (f"{r['pname']} {r['name'] or ''}".lower()): continue
            self.tree.insert("", "end", values=(r["id"],r["pname"],r["name"],r["start_time"],r["end_time"],r["maximum_seconds"],r["active"]))
    def on_select(self,e):
        sel=self.tree.selection()
        if not sel: return
        v=self.tree.item(sel[0],"values")
        for display in self.programs:
            if v[1] in display: self.prog_cb.set(display); break
        self.name_var.set(v[2] or ""); self.start_var.set(v[3] or ""); self.end_var.set(v[4] or ""); 
        try: self.max_var.set(int(v[5] or 0))
        except: pass
        self.active_var.set(int(v[6]))
    def add(self):
        prog_id=self.programs.get(self.prog_cb.get())
        if not prog_id: return
        con=get_connection(); cur=con.cursor()
        cur.execute("INSERT INTO stopsets (program_id,name,start_time,end_time,maximum_seconds,active,created_date,modified_date) VALUES (?,?,?,?,?,?,?,?)",(prog_id,self.name_var.get().strip(),self.start_var.get().strip(),self.end_var.get().strip(),self.max_var.get(),self.active_var.get(),now_str(),now_str())); con.commit(); con.close(); self.load()
    def update(self):
        sel=self.tree.selection()
        if not sel: return
        sid=self.tree.item(sel[0],"values")[0]; prog_id=self.programs.get(self.prog_cb.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("UPDATE stopsets SET program_id=?,name=?,start_time=?,end_time=?,maximum_seconds=?,active=?,modified_date=? WHERE id=?",(prog_id,self.name_var.get().strip(),self.start_var.get().strip(),self.end_var.get().strip(),self.max_var.get(),self.active_var.get(),now_str(),sid)); con.commit(); con.close(); self.load()
if __name__=="__main__":
    root=tk.Tk(); GUI(root); root.mainloop()
