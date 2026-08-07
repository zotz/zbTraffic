#!/usr/bin/env python3

# File: prototype/traffic_board.py

"""Prototype traffic board."""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import date, timedelta


from tkcalendar import DateEntry

from traffic.database import get_connection
from traffic.assignment import assign_spot_to_avail
from traffic.assignment import remove_spot_from_avail
from traffic.avails import get_remaining_seconds

class TrafficBoard:
    def __init__(self, root):
        self.root=root
        root.title("zbTraffic Prototype Traffic Board")
        root.geometry("1200x800")
        self.selected_spot=None
        self.selected_avail=None
        self.build()

    def build(self):
        top=ttk.Frame(self.root); top.pack(fill="x",padx=5,pady=5)
        ttk.Label(top,text="Air Date:").pack(side="left")
        self.date_var = tk.StringVar(
            value=(date.today()+timedelta(days=1)).isoformat()
        )

        self.date_picker = DateEntry(
            top,
            textvariable=self.date_var,
            width=12,
            date_pattern="yyyy-mm-dd"
        )

        self.date_picker.pack(
            side="left",
            padx=5
        )

        self.date_picker.bind(
            "<<DateEntrySelected>>",
            lambda e: self.load_avails()
        )
        ttk.Label(top,text="Customer:").pack(side="left")
        self.customer=ttk.Combobox(top,state="readonly",width=40)
        self.customer.pack(side="left",padx=5)
        self.customer.bind("<<ComboboxSelected>>",lambda e:self.load_pending())
        ttk.Button(
            top,
            text="Refresh",
            command=self.refresh
        ).pack(
            side="right",
            padx=5
        )

        ttk.Button(
            top,
            text="Refresh Avails",
            command=self.load_avails
        ).pack(
            side="right",
            padx=5
        )

        self.pending=self.make_tree("Pending Spots")

        self.avails=self.make_tree("Avails")

        self.avail_contents=self.make_tree(
            "Avail Contents"
        )

        self.avails.bind(
            "<<TreeviewSelect>>",
            self.avail_selected
        )

        self.avail_contents.bind(
            "<Double-1>",
            self.avail_contents_double_click
        )



        btn=ttk.Frame(self.root); btn.pack(fill="x",pady=5)
        ttk.Button(btn,text="Schedule",command=self.schedule).pack(side="left",padx=5)
        ttk.Button(btn,text="Unschedule",command=self.unschedule).pack(side="left",padx=5)
        self.status=tk.StringVar()
        ttk.Label(self.root,textvariable=self.status).pack(anchor="w")
        self.load_customers(); self.load_avails()

    def make_tree(self,title):

        ttk.Label(
            self.root,
            text=title
        ).pack(
            anchor="w"
        )


        f=ttk.Frame(self.root)

        f.pack(
            fill="both",
            padx=5,
            pady=2
        )


        t=ttk.Treeview(
            f,
            show="headings",
            height=8
        )


        ys=ttk.Scrollbar(
            f,
            orient="vertical",
            command=t.yview
        )

        xs=ttk.Scrollbar(
            f,
            orient="horizontal",
            command=t.xview
        )


        t.configure(
            yscrollcommand=ys.set,
            xscrollcommand=xs.set
        )


        t.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        ys.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        xs.grid(
            row=1,
            column=0,
            sticky="ew"
        )


        f.rowconfigure(
            0,
            weight=1
        )

        f.columnconfigure(
            0,
            weight=1
        )


        return t

    def load_customers(self):
        con=get_connection(); cur=con.cursor()
        cur.execute("select id,company_name from customers where active=1 order by company_name")
        rows=cur.fetchall(); con.close()
        self.customers={r["company_name"]:r["id"] for r in rows}
        self.customer["values"]=list(self.customers.keys())
        if rows:
            self.customer.current(0)
            self.load_pending()

    def load_pending(self):
        cid=self.customers.get(self.customer.get())
        con=get_connection(); cur=con.cursor()
        cur.execute("""
    SELECT ss.id, c.title, ss.air_date, ss.air_time, ss.status
    FROM spots ss
    JOIN commercials c ON ss.commercial_id = c.id
    WHERE c.customer_id = ? AND ss.status = 'Pending' ORDER BY c.title, ss.id
""", (cid,))
        rows=cur.fetchall(); con.close()
        cols=["id","title","air_date","air_time","status"]
        self.pending["columns"]=cols
        for c in cols: self.pending.heading(c,text=c); self.pending.column(c,width=140)
        self.pending.delete(*self.pending.get_children())
        for r in rows: self.pending.insert("", "end", values=[r[c] for c in cols])

    def load_avails(self):

        con = get_connection()
        cur = con.cursor()

        cur.execute(
            """
            SELECT
                id,
                air_date,
                start_time,
                length_seconds,
                status

            FROM avails

            WHERE air_date = ?
            AND status IN ('Open', 'Partial', 'Filled')

            ORDER BY start_time
            """,
            (
                self.date_var.get(),
            )
        )

        rows = cur.fetchall()

        con.close()


        cols = [
            "id",
            "air_date",
            "start_time",
            "length_seconds",
            "used_seconds",
            "remaining_seconds",
            "status"
        ]


        self.avails["columns"] = cols


        for c in cols:

            self.avails.heading(
                c,
                text=c
            )

            self.avails.column(
                c,
                width=120
            )


        self.avails.delete(
            *self.avails.get_children()
        )


        for r in rows:

            remaining = get_remaining_seconds(
                r["id"]
            )

            used = (
                r["length_seconds"]
                -
                remaining
            )


            self.avails.insert(
                "",
                "end",
                values=[
                    r["id"],
                    r["air_date"],
                    r["start_time"],
                    r["length_seconds"],
                    used,
                    remaining,
                    r["status"]
                ]
            )


    def refresh(self):
        self.load_pending(); self.load_avails()


    def schedule(self):

        spot_selection = self.pending.selection()
        avail_selection = self.avails.selection()


        if not spot_selection:

            self.status.set(
                "No pending spot selected."
            )

            return


        if not avail_selection:

            self.status.set(
                "No avail selected."
            )

            return


        #
        # Get selected IDs
        #

        spot_values = self.pending.item(
            spot_selection[0],
            "values"
        )

        avail_values = self.avails.item(
            avail_selection[0],
            "values"
        )


        spot_id = int(
            spot_values[0]
        )

        avail_id = int(
            avail_values[0]
        )


        #
        # Assign
        #

        success, errors = assign_spot_to_avail(
            spot_id,
            avail_id
        )


        if not success:

            self.status.set(
                "Assignment failed: " +
                ", ".join(errors)
            )

            return


        self.status.set(
            f"Spot {spot_id} to avail {avail_id}"
        )


        #
        # Reload data
        #

        self.refresh()

        self.select_avail(
            avail_id
        )

        self.load_avail_contents(
            avail_id
        )

    def avail_selected(self, event):

        selection = self.avails.selection()


        if not selection:

            return


        values = self.avails.item(
            selection[0],
            "values"
        )


        avail_id = int(
            values[0]
        )


        self.load_avail_contents(
            avail_id
        )



    def avail_contents_double_click(
        self,
        event
    ):

        self.unschedule()






    def select_avail(
        self,
        avail_id
    ):

        for item in self.avails.get_children():

            values = self.avails.item(
                item,
                "values"
            )


            if int(values[0]) == avail_id:

                self.avails.selection_set(
                    item
                )

                self.avails.focus(
                    item
                )

                self.avails.see(
                    item
                )

                break


    def load_avail_contents(
        self,
        avail_id
    ):

        con = get_connection()
        cur = con.cursor()


        cur.execute(
            """
            SELECT
                ss.id,
                cu.company_name,
                c.title,
                c.cart_number,
                c.length_seconds,
                ss.air_time,
                ss.status

            FROM spots ss


            JOIN commercials c

            ON ss.commercial_id = c.id


            JOIN customers cu

            ON c.customer_id = cu.id


            WHERE ss.avail_id = ?

            ORDER BY ss.id
            """,
            (
                avail_id,
            )
        )


        rows = cur.fetchall()

        con.close()



        cols = [
            "id",
            "company_name",
            "title",
            "cart_number",
            "length_seconds",
            "air_time",
            "status"
        ]


        self.avail_contents["columns"] = cols


        widths = {
            "id": 20,
            "company_name": 150,
            "title": 200,
            "cart_number": 100,
            "length_seconds": 80,
            "air_time": 90,
            "status": 100
        }


        for c in cols:

            self.avail_contents.heading(
                c,
                text=c
            )

            self.avail_contents.column(
                c,
                width=widths.get(
                    c,
                    120
                )
            )



        self.avail_contents.delete(
            *self.avail_contents.get_children()
        )



        for r in rows:

            self.avail_contents.insert(
                "",
                "end",
                values=[
                    r[c]
                    for c in cols
                ]
            )




    def unschedule(self):

        spot_selection = self.avail_contents.selection()


        if not spot_selection:

            self.status.set(
                "No spot selected."
            )

            return



        spot_values = self.avail_contents.item(
            spot_selection[0],
            "values"
        )


        spot_id = int(
            spot_values[0]
        )

        confirm = messagebox.askyesno(
            "Confirm Unschedule",
            f"Remove spot {spot_id} from its avail?"
        )


        if not confirm:

            self.status.set(
                "Unschedule cancelled."
            )

            return


        success, errors = remove_spot_from_avail(
            spot_id
        )


        if not success:

            self.status.set(
                "Unschedule failed: "
                + ", ".join(errors)
            )

            return



        self.status.set(
            f"Unscheduled spot {spot_id}"
        )


        #
        # Remember the current avail before refresh
        #

        avail_selection = self.avails.selection()


        avail_id = None


        if avail_selection:

            avail_values = self.avails.item(
                avail_selection[0],
                "values"
            )

            avail_id = int(
                avail_values[0]
            )



        #
        # Refresh the displays
        #

        self.refresh()



        if avail_id is not None:

            self.select_avail(
                avail_id
            )

            self.load_avail_contents(
                avail_id
            )

if __name__=="__main__":
    root=tk.Tk()
    TrafficBoard(root)
    root.mainloop()
