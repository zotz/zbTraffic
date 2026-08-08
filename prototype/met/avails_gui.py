# File: prototype/met/avails_gui.py

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
from datetime import datetime, date
from tkcalendar import DateEntry
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
        self.root=root; root.title("Avails Viewer"); root.geometry("1100x600")
        self.build(); self.load()
    def build(self):
        top=ttk.Frame(self.root); top.pack(fill='x',padx=5,pady=3)
        ttk.Label(top,text="Air Date:").pack(side='left')
        self.date_var=tk.StringVar(value=date.today().isoformat())
        self.date_picker=DateEntry(top,textvariable=self.date_var,width=12,date_pattern="yyyy-mm-dd"); self.date_picker.pack(side='left',padx=5)
        self.date_picker.bind("<<DateEntrySelected>>", lambda e: self.load())
        ttk.Label(top,text="Filter station/status:").pack(side='left',padx=10)
        self.filter_var=tk.StringVar(); e=ttk.Entry(top,textvariable=self.filter_var,width=20); e.pack(side='left',padx=5); e.bind("<KeyRelease>", lambda _: self.apply_filter())
        ttk.Button(top,text="Refresh",command=self.load).pack(side='left',padx=5)
        cols=("id","station","stopset","air_date","start_time","length","status")
        self.wrap=ScrolledTreeview(self.root,cols,height=20); self.wrap.pack(fill='both',expand=True,padx=5,pady=5)
        self.tree=self.wrap.tree; self.all_rows=[]
    def load(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("SELECT a.id,s.name as station_name,ss.name as stopset_name,a.air_date,a.start_time,a.length_seconds,a.status FROM avails a JOIN stations s ON a.station_id=s.id LEFT JOIN stopsets ss ON a.stopset_id=ss.id WHERE a.air_date=? ORDER BY a.start_time",(self.date_var.get(),))
        self.all_rows=[dict(r) for r in cur.fetchall()]; con.close(); self.apply_filter()
    def apply_filter(self):
        f=self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for r in self.all_rows:
            if f and f not in f"{r['station_name'] or ''} {r['status'] or ''}".lower(): continue
            self.tree.insert("", "end", values=(r["id"],r["station_name"],r["stopset_name"],r["air_date"],r["start_time"],r["length_seconds"],r["status"]))
if __name__=="__main__":
    root=tk.Tk(); GUI(root); root.mainloop()
