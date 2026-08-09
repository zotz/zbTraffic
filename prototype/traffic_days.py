#!/usr/bin/env python3

# File: prototype/traffic_days.py

"""Prototype traffic view for one or more days."""

import tkinter as tk
from tkinter import ttk

from datetime import date, timedelta

from tkcalendar import DateEntry

from traffic.database import get_connection


class TrafficDays:

    def __init__(self, root):

        self.root = root

        root.title("zbTraffic Prototype Traffic Days")
        root.geometry("1300x800")

        self.build()

        self.load_data()

        root.bind(
            "<Left>",
            lambda event: self.previous_range()
        )

        root.bind(
            "<Right>",
            lambda event: self.next_range()
        )

    def set_dates(self, start_date, end_date):

        self.start_date_var.set(
            start_date.isoformat()
        )

        self.end_date_var.set(
            end_date.isoformat()
        )

        self.load_data()


    def previous_range(self):

        start = (
            date.fromisoformat(self.start_date_var.get())
            - timedelta(days=1)
        )

        end = (
            date.fromisoformat(self.end_date_var.get())
            - timedelta(days=1)
        )

        self.set_dates(start, end)


    def previous_start(self):

        start = (
            date.fromisoformat(self.start_date_var.get())
            - timedelta(days=1)
        )

        end = date.fromisoformat(
            self.end_date_var.get()
        )

        self.set_dates(start, end)


    def today(self):

        today = date.today()

        self.set_dates(
            today,
            today
        )


    def next_end(self):

        start = date.fromisoformat(
            self.start_date_var.get()
        )

        end = (
            date.fromisoformat(self.end_date_var.get())
            + timedelta(days=1)
        )

        self.set_dates(start, end)


    def next_range(self):

        start = (
            date.fromisoformat(self.start_date_var.get())
            + timedelta(days=1)
        )

        end = (
            date.fromisoformat(self.end_date_var.get())
            + timedelta(days=1)
        )

        self.set_dates(start, end)







    def build(self):

        #
        # Date controls
        #

        top = ttk.Frame(self.root)
        top.pack(
            fill="x",
            padx=5,
            pady=5
        )

        ttk.Button(
            top,
            text="<<",
            command=self.previous_range
        ).pack(side="left")

        ttk.Button(
            top,
            text="<",
            command=self.previous_start
        ).pack(
            side="left",
            padx=(5,10)
        )

        ttk.Button(
            top,
            text="Today",
            command=self.today
        ).pack(
            side="left",
            padx=(0,15)
        )




        ttk.Label(
            top,
            text="Start Date:"
        ).pack(
            side="left"
        )

        self.start_date_var = tk.StringVar(
            value=date.today().isoformat()
        )

        self.start_date = DateEntry(
            top,
            textvariable=self.start_date_var,
            width=12,
            date_pattern="yyyy-mm-dd"
        )

        self.start_date.pack(
            side="left",
            padx=5
        )


        ttk.Label(
            top,
            text="End Date:"
        ).pack(
            side="left"
        )

        self.end_date_var = tk.StringVar(
            value=date.today().isoformat()
        )

        self.end_date = DateEntry(
            top,
            textvariable=self.end_date_var,
            width=12,
            date_pattern="yyyy-mm-dd"
        )

        self.end_date.pack(
            side="left",
            padx=5
        )


        ttk.Button(
            top,
            text="Load",
            command=self.load_data
        ).pack(
            side="left",
            padx=10
        )


        ttk.Button(
            top,
            text=">",
            command=self.next_end
        ).pack(
            side="left",
            padx=(10,5)
        )

        ttk.Button(
            top,
            text=">>",
            command=self.next_range
        ).pack(side="left")



        #
        # Tree
        #

        frame = ttk.Frame(self.root)

        frame.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )


        columns = (
            "date",
            "time",
            "type",
            "id",
            "customer",
            "commercial",
            "cart",
            "length",
            "used",
            "remaining",
            "status"
        )


        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="tree headings"
        )


        self.tree.heading(
            "#0",
            text="Traffic"
        )

        self.tree.column(
            "#0",
            width=40,
            stretch=False
        )


        headings = {
            "date": "Date",
            "time": "Time",
            "type": "Type",
            "id": "ID",
            "customer": "Customer",
            "commercial": "Commercial",
            "cart": "Cart",
            "length": "Length",
            "used": "Used",
            "remaining": "Remaining",
            "status": "Status"
        }


        widths = {
            "date": 95,
            "time": 80,
            "type": 80,
            "id": 60,
            "customer": 180,
            "commercial": 220,
            "cart": 100,
            "length": 80,
            "used": 80,
            "remaining": 90,
            "status": 100
        }


        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=widths[column],
                anchor="w"
            )


        #
        # Scrollbars
        #

        vertical = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.tree.yview
        )

        horizontal = ttk.Scrollbar(
            frame,
            orient="horizontal",
            command=self.tree.xview
        )


        self.tree.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set
        )


        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        vertical.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        horizontal.grid(
            row=1,
            column=0,
            sticky="ew"
        )


        frame.rowconfigure(
            0,
            weight=1
        )

        frame.columnconfigure(
            0,
            weight=1
        )


        #
        # Status
        #

        self.status = tk.StringVar()

        ttk.Label(
            self.root,
            textvariable=self.status
        ).pack(
            anchor="w",
            padx=5,
            pady=3
        )


    def load_data(self):

        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()


        #
        # Basic date validation
        #

        try:

            start = date.fromisoformat(
                start_date
            )

            end = date.fromisoformat(
                end_date
            )

        except ValueError:

            self.status.set(
                "Invalid date."
            )

            return


        if start > end:

            self.status.set(
                "Start date cannot be after end date."
            )

            return


        #
        # Clear existing data
        #

        self.tree.delete(
            *self.tree.get_children()
        )


        #
        # Load avails
        #

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                a.id,
                a.station_id,
                a.stopset_id,
                a.air_date,
                a.start_time,
                a.length_seconds,
                a.status

            FROM avails a

            WHERE a.air_date >= ?
              AND a.air_date <= ?

            ORDER BY
                a.air_date,
                a.start_time,
                a.id
            """,
            (
                start_date,
                end_date
            )
        )


        avails = cursor.fetchall()


        #
        # Load spots for all avails in one query.
        #

        cursor.execute(
            """
            SELECT
                s.id,
                s.avail_id,
                s.air_date,
                s.air_time,
                s.status,

                c.title,
                c.cart_number,
                c.length_seconds,

                cu.company_name

            FROM spots s

            LEFT JOIN commercials c
                ON s.commercial_id = c.id

            LEFT JOIN customers cu
                ON c.customer_id = cu.id

            WHERE s.avail_id IN
            (
                SELECT id
                FROM avails
                WHERE air_date >= ?
                  AND air_date <= ?
            )

            ORDER BY
                s.air_date,
                s.air_time,
                s.id
            """,
            (
                start_date,
                end_date
            )
        )


        spots = cursor.fetchall()


        connection.close()


        #
        # Group spots by avail.
        #

        spots_by_avail = {}

        for spot in spots:

            avail_id = spot["avail_id"]

            spots_by_avail.setdefault(
                avail_id,
                []
            ).append(
                spot
            )


        #
        # Display avails and their spots.
        #

        avail_count = 0
        spot_count = 0


        current_date = None
        date_node = None


        for avail in avails:

            avail_count += 1


            #
            # Create a date heading when
            # the air date changes.
            #

            if avail["air_date"] != current_date:

                current_date = avail["air_date"]

                date_node = self.tree.insert(
                    "",
                    "end",
                    text="",
                    values=(
                        current_date,
                        "",
                        "DAY",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        ""
                    ),
                    open=True
                )


            #
            # Calculate used/remaining time.
            #

            avail_spots = spots_by_avail.get(
                avail["id"],
                []
            )


            used_seconds = sum(
                spot["length_seconds"] or 0
                for spot in avail_spots
            )


            remaining_seconds = (
                avail["length_seconds"]
                - used_seconds
            )


            #
            # Insert avail.
            #

            avail_node = self.tree.insert(
                date_node,
                "end",
                text="",
                values=(
                    avail["air_date"],
                    avail["start_time"],
                    "AVAIL",
                    avail["id"],
                    "",
                    "",
                    "",
                    avail["length_seconds"],
                    used_seconds,
                    remaining_seconds,
                    avail["status"]
                ),
                open=True
            )


            #
            # Insert spots underneath the avail.
            #

            for spot in avail_spots:

                spot_count += 1


                self.tree.insert(
                    avail_node,
                    "end",
                    text="",
                    values=(
                        spot["air_date"],
                        spot["air_time"],
                        "SPOT",
                        spot["id"],
                        spot["company_name"] or "",
                        spot["title"] or "",
                        spot["cart_number"] or "",
                        spot["length_seconds"] or 0,
                        "",
                        "",
                        spot["status"]
                    )
                )


        self.status.set(
            f"{avail_count} avails, "
            f"{spot_count} spots"
        )


        #
        # Expand the top-level date rows.
        #

        for item in self.tree.get_children():

            self.tree.item(
                item,
                open=True
            )


        #
        # Expand the avails underneath each date.
        #

        for day in self.tree.get_children():

            for avail in self.tree.get_children(day):

                self.tree.item(
                    avail,
                    open=True
                )


if __name__ == "__main__":

    root = tk.Tk()

    TrafficDays(root)

    root.mainloop()


