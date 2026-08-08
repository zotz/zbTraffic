# File: prototype/met/customers_gui.py
# Version: v4-international-fixed - uses address_line1, locality, administrative_area, country_code

import sys
import pathlib
_HERE = pathlib.Path(__file__).resolve()
for _p in [_HERE.parent, *_HERE.parents]:
    if (_p / "traffic").is_dir():
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
            if c in ("company_name","address_line1","locality"): w=180
            if c=="id": w=50
            self.tree.column(c, width=w, minwidth=40, stretch=True)

class GUI:
    def __init__(self, root):
        self.root=root; root.title("Customers - International v4"); root.geometry("1350x700")
        self.cat_map={}
        self.build(); self.load_cats(); self.load()

    def build(self):
        top=ttk.Frame(self.root); top.pack(fill='x',padx=5,pady=3)
        ttk.Label(top,text="Filter company / locality / country:").pack(side='left')
        self.filter_var=tk.StringVar()
        e=ttk.Entry(top,textvariable=self.filter_var,width=35); e.pack(side='left',padx=5)
        e.bind("<KeyRelease>", lambda _: self.apply_filter())
        ttk.Button(top,text="Clear",command=lambda:[self.filter_var.set(""),self.apply_filter()]).pack(side='left')
        ttk.Button(top,text="Refresh",command=self.load).pack(side='right')

        form=ttk.LabelFrame(self.root,text="Customer Form - International Address"); form.pack(fill='x',padx=5,pady=2)
        ttk.Label(form,text="Company:").grid(row=0,column=0,sticky='w')
        self.company=tk.StringVar(); ttk.Entry(form,textvariable=self.company,width=30).grid(row=0,column=1,padx=3,sticky='w')
        ttk.Label(form,text="Category:").grid(row=0,column=2,sticky='w')
        self.category=ttk.Combobox(form,state='readonly',width=18); self.category.grid(row=0,column=3,padx=3,sticky='w')
        self.active_var=tk.IntVar(value=1); ttk.Checkbutton(form,text="Active",variable=self.active_var).grid(row=0,column=4,padx=5,sticky='w')

        ttk.Label(form,text="Address Line 1:").grid(row=1,column=0,sticky='w')
        self.addr1=tk.StringVar(); ttk.Entry(form,textvariable=self.addr1,width=35).grid(row=1,column=1,padx=3,sticky='w')
        ttk.Label(form,text="Line 2:").grid(row=1,column=2,sticky='w')
        self.addr2=tk.StringVar(); ttk.Entry(form,textvariable=self.addr2,width=30).grid(row=1,column=3,padx=3,sticky='w')

        ttk.Label(form,text="Locality (City):").grid(row=2,column=0,sticky='w')
        self.locality=tk.StringVar(); ttk.Entry(form,textvariable=self.locality,width=20).grid(row=2,column=1,padx=3,sticky='w')
        ttk.Label(form,text="Admin Area (State/Province):").grid(row=2,column=2,sticky='w')
        self.admin_area=tk.StringVar(); ttk.Entry(form,textvariable=self.admin_area,width=18).grid(row=2,column=3,padx=3,sticky='w')
        ttk.Label(form,text="Postal Code:").grid(row=2,column=4,sticky='w')
        self.postal=tk.StringVar(); ttk.Entry(form,textvariable=self.postal,width=12).grid(row=2,column=5,padx=3,sticky='w')
        ttk.Label(form,text="Country Code (BS/US/GB):").grid(row=2,column=6,sticky='w')
        self.country=tk.StringVar(); ttk.Entry(form,textvariable=self.country,width=8).grid(row=2,column=7,padx=3,sticky='w')

        ttk.Label(form,text="Phone:").grid(row=3,column=0,sticky='w')
        self.phone=tk.StringVar(); ttk.Entry(form,textvariable=self.phone,width=20).grid(row=3,column=1,padx=3,sticky='w')
        ttk.Label(form,text="Email:").grid(row=3,column=2,sticky='w')
        self.email=tk.StringVar(); ttk.Entry(form,textvariable=self.email,width=30).grid(row=3,column=3,padx=3,sticky='w')

        btn=ttk.Frame(self.root); btn.pack(fill='x',padx=5,pady=2)
        ttk.Button(btn,text="Add",command=self.add).pack(side='left',padx=3)
        ttk.Button(btn,text="Update",command=self.update).pack(side='left',padx=3)
        ttk.Button(btn,text="Clear Form",command=self.clear_form).pack(side='left',padx=10)

        cols=("id","company_name","locality","administrative_area","country_code","telephone","category","active")
        self.wrap=ScrolledTreeview(self.root,cols,height=15); self.wrap.pack(fill='both',expand=True,padx=5,pady=5)
        self.tree=self.wrap.tree; self.tree.bind("<<TreeviewSelect>>",self.on_select)
        self.all_rows=[]

    def load_cats(self):
        con=get_connection(); cur=con.cursor()
        try:
            cur.execute("SELECT id,name FROM categories WHERE active=1 ORDER BY name")
            self.cat_map={r["name"]:r["id"] for r in cur.fetchall()}; self.category["values"]=list(self.cat_map.keys())
        except Exception as e:
            print(e)
        con.close()

    def load(self):
        con=get_connection(); cur=con.cursor()
        # International schema - no c.city, no c.state
        cur.execute("""SELECT c.id,c.company_name,c.address_line1,c.address_line2,c.locality,c.administrative_area,c.postal_code,c.country_code,c.telephone,c.email,cat.name as cat_name,c.active,c.category_id
                       FROM customers c LEFT JOIN categories cat ON c.category_id=cat.id ORDER BY c.company_name""")
        self.all_rows=[dict(r) for r in cur.fetchall()]; con.close(); self.apply_filter()

    def apply_filter(self):
        f=self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for r in self.all_rows:
            hay = f"{r.get('company_name','') or ''} {r.get('locality','') or ''} {r.get('administrative_area','') or ''} {r.get('country_code','') or ''}".lower()
            if f and f not in hay: continue
            self.tree.insert("", "end", values=(r["id"],r["company_name"],r.get("locality",""),r.get("administrative_area",""),r.get("country_code",""),r.get("telephone",""),r.get("cat_name",""),r["active"]))

    def on_select(self,e):
        sel=self.tree.selection()
        if not sel: return
        rid=int(self.tree.item(sel[0],"values")[0])
        for r in self.all_rows:
            if r["id"]==rid:
                self.company.set(r["company_name"] or "")
                self.addr1.set(r.get("address_line1","") or "")
                self.addr2.set(r.get("address_line2","") or "")
                self.locality.set(r.get("locality","") or "")
                self.admin_area.set(r.get("administrative_area","") or "")
                self.postal.set(r.get("postal_code","") or "")
                self.country.set(r.get("country_code","") or "")
                self.phone.set(r.get("telephone","") or "")
                self.email.set(r.get("email","") or "")
                for k,v in self.cat_map.items():
                    if v==r.get("category_id"):
                        self.category.set(k); break
                else:
                    self.category.set(r.get("cat_name","") or "")
                self.active_var.set(r.get("active",1))
                break

    def clear_form(self):
        for v in [self.company,self.addr1,self.addr2,self.locality,self.admin_area,self.postal,self.country,self.phone,self.email]:
            v.set("")
        self.active_var.set(1); self.category.set("")

    def add(self):
        if not self.company.get().strip():
            messagebox.showwarning("Validation","Company name required"); return
        cat_id=self.cat_map.get(self.category.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("""INSERT INTO customers
            (company_name,address_line1,address_line2,locality,administrative_area,postal_code,country_code,telephone,email,category_id,active,created_date,modified_date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (self.company.get().strip(),self.addr1.get().strip(),self.addr2.get().strip(),self.locality.get().strip(),self.admin_area.get().strip(),self.postal.get().strip(),self.country.get().strip().upper(),self.phone.get().strip(),self.email.get().strip(),cat_id,self.active_var.get(),now_str(),now_str()))
        con.commit(); con.close(); self.load()

    def update(self):
        sel=self.tree.selection()
        if not sel:
            messagebox.showwarning("Select","Select a row to update"); return
        cid=self.tree.item(sel[0],"values")[0]; cat_id=self.cat_map.get(self.category.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("""UPDATE customers SET
            company_name=?,address_line1=?,address_line2=?,locality=?,administrative_area=?,postal_code=?,country_code=?,telephone=?,email=?,category_id=?,active=?,modified_date=?
            WHERE id=?""",
            (self.company.get().strip(),self.addr1.get().strip(),self.addr2.get().strip(),self.locality.get().strip(),self.admin_area.get().strip(),self.postal.get().strip(),self.country.get().strip().upper(),self.phone.get().strip(),self.email.get().strip(),cat_id,self.active_var.get(),now_str(),cid))
        con.commit(); con.close(); self.load()

if __name__=="__main__":
    root=tk.Tk(); GUI(root); root.mainloop()
