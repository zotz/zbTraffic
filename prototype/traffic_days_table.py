#!/usr/bin/env python3

# File: /prototype/traffic_days_table.py

"""Prototype flat table view of scheduled traffic."""

import tkinter as tk
from tkinter import ttk

from datetime import date, timedelta

from tkcalendar import DateEntry

from traffic.database import get_connection


class TrafficDaysTable:

    def __init__(self, root):

        self.root = root

        root.title("zbTraffic Prototype Traffic Days - Table")
        root.geometry("1500x800")

        self.sort_column = None
        self.sort_reverse = False

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
            text="\u25C0\u25C0",
            command=self.previous_range
        ).pack(side="left")

        ttk.Button(
            top,
            text="\u25C0",
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
            text="\u25B8",
            command=self.next_end
        ).pack(
            side="left",
            padx=(10,5)
        )

        ttk.Button(
            top,
            text="\u25B8\u25B8",
            command=self.next_range
        ).pack(side="left")



        #
        # Table
        #

        frame = ttk.Frame(self.root)

        frame.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )


        columns = (
            "air_date",
            "avail_time",
            "avail_id",
            "avail_length",
            "avail_status",
            "spot_id",
            "spot_time",
            "customer",
            "commercial",
            "spot_length",
            "spot_status"
        )


        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings"
        )


        headings = {
            "air_date": "Date",
            "avail_time": "Avail Time",
            "avail_id": "Avail ID",
            "avail_length": "Avail Length",
            "avail_status": "Avail Status",
            "spot_id": "Spot ID",
            "spot_time": "Spot Time",
            "customer": "Customer",
            "commercial": "Commercial",
            "spot_length": "Spot Length",
            "spot_status": "Spot Status"
        }


        widths = {
            "air_date": 100,
            "avail_time": 90,
            "avail_id": 80,
            "avail_length": 100,
            "avail_status": 100,
            "spot_id": 80,
            "spot_time": 90,
            "customer": 220,
            "commercial": 260,
            "spot_length": 100,
            "spot_status": 110
        }


        for column in columns:

            self.tree.heading(
                column,
                text=headings[column],
                command=lambda c=column: self.sort_by(c)
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
        # Validate dates.
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
        # Clear existing rows.
        #

        self.tree.delete(
            *self.tree.get_children()
        )


        #
        # Load scheduled spots joined with
        # their avails, commercials, and
        # customers.
        #

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT

                a.air_date,
                a.start_time AS avail_time,
                a.id AS avail_id,
                a.length_seconds AS avail_length,
                a.status AS avail_status,

                s.id AS spot_id,
                s.air_time AS spot_time,
                s.status AS spot_status,

                c.title AS commercial,
                c.length_seconds AS spot_length,

                cu.company_name AS customer

            FROM spots s

            JOIN avails a
                ON s.avail_id = a.id

            LEFT JOIN commercials c
                ON s.commercial_id = c.id

            LEFT JOIN customers cu
                ON c.customer_id = cu.id

            WHERE a.air_date >= ?
              AND a.air_date <= ?

            ORDER BY
                a.air_date,
                a.start_time,
                s.air_time,
                s.id
            """,
            (
                start_date,
                end_date
            )
        )


        rows = cursor.fetchall()


        connection.close()


        #
        # Insert rows.
        #

        for row in rows:

            self.tree.insert(
                "",
                "end",
                values=(
                    row["air_date"],
                    row["avail_time"],
                    row["avail_id"],
                    row["avail_length"],
                    row["avail_status"],
                    row["spot_id"],
                    row["spot_time"],
                    row["customer"] or "",
                    row["commercial"] or "",
                    row["spot_length"] or 0,
                    row["spot_status"]
                )
            )


        self.status.set(
            f"{len(rows)} scheduled spots"
        )


    def sort_by(self, column):

        #
        # Get all rows.
        #

        rows = []

        for item in self.tree.get_children():

            value = self.tree.set(
                item,
                column
            )

            rows.append(
                (
                    value,
                    item
                )
            )


        #
        # Toggle direction when the same
        # column is clicked again.
        #

        if self.sort_column == column:

            self.sort_reverse = not self.sort_reverse

        else:

            self.sort_column = column
            self.sort_reverse = False


        #
        # Sort.
        #

        rows.sort(
            key=lambda row: row[0],
            reverse=self.sort_reverse
        )


        #
        # Reorder rows.
        #

        for index, (_, item) in enumerate(rows):

            self.tree.move(
                item,
                "",
                index
            )


if __name__ == "__main__":

    root = tk.Tk()

    TrafficDaysTable(root)

    root.mainloop()


