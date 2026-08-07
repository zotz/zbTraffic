#!/usr/bin/env python3

# File: gui/database_browser.py

import tkinter as tk

from tkinter import ttk

from traffic.database import (
    get_connection
)



class DatabaseBrowser:


    def __init__(
        self,
        root
    ):

        self.root = root

        self.root.title(
            "zbTraffic Database Browser"
        )

        self.root.geometry(
            "1100x700"
        )


        self.current_table = None

        self.columns = []

        self.sort_column = None

        self.sort_reverse = False


        self.build_interface()

        self.load_tables()



    def build_interface(
        self
    ):


        #
        # Main layout
        #

        main_frame = ttk.Frame(
            self.root
        )

        main_frame.pack(
            fill="both",
            expand=True
        )



        #
        # Left side - tables
        #

        left_frame = ttk.Frame(
            main_frame,
            width=200
        )

        left_frame.pack(
            side="left",
            fill="y",
            padx=5,
            pady=5
        )


        ttk.Label(
            left_frame,
            text="Tables"
        ).pack()


        self.table_list = tk.Listbox(
            left_frame
        )

        self.table_list.pack(
            fill="both",
            expand=True
        )


        self.table_list.bind(
            "<<ListboxSelect>>",
            self.table_selected
        )



        #
        # Right side
        #

        right_frame = ttk.Frame(
            main_frame
        )

        right_frame.pack(
            side="right",
            fill="both",
            expand=True
        )



        #
        # Filter area
        #

        filter_frame = ttk.Frame(
            right_frame
        )

        filter_frame.pack(
            fill="x",
            pady=5
        )


        ttk.Label(
            filter_frame,
            text="Filter:"
        ).pack(
            side="left"
        )


        self.filter_text = tk.StringVar()


        self.filter_entry = ttk.Entry(
            filter_frame,
            textvariable=self.filter_text
        )

        self.filter_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )


        self.filter_entry.bind(
            "<KeyRelease>",
            self.refresh_data
        )


        ttk.Button(
            filter_frame,
            text="Clear",
            command=self.clear_filter
        ).pack(
            side="left"
        )



        #
        # Data table
        #

        table_frame = ttk.Frame(
            right_frame
        )

        table_frame.pack(
            fill="both",
            expand=True
        )


        self.tree = ttk.Treeview(
            table_frame
        )


        vertical_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )


        horizontal_scroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview
        )


        self.tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set
        )


        vertical_scroll.pack(
            side="right",
            fill="y"
        )


        horizontal_scroll.pack(
            side="bottom",
            fill="x"
        )


        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )


        self.tree.bind(
            "<Double-1>",
            self.show_record
        )


        #
        # Status
        #

        self.status = ttk.Label(
            right_frame,
            text=""
        )

        self.status.pack(
            anchor="w"
        )



    def load_tables(
        self
    ):

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """
        )


        tables = cursor.fetchall()

        connection.close()



        for table in tables:

            name = table["name"]

            self.table_list.insert(
                "end",
                name
            )



    def table_selected(
        self,
        event=None
    ):


        selection = self.table_list.curselection()


        if not selection:

            return


        self.current_table = (
            self.table_list.get(
                selection[0]
            )
        )


        self.sort_column = None

        self.sort_reverse = False


        self.load_columns()

        self.refresh_data()



    def load_columns(
        self
    ):

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            f"""
            PRAGMA table_info(
                {self.current_table}
            )
            """
        )


        columns = cursor.fetchall()


        connection.close()


        self.columns = [
            column["name"]
            for column in columns
        ]



    def refresh_data(
        self,
        event=None
    ):


        if not self.current_table:

            return


        connection = get_connection()

        cursor = connection.cursor()


        query = (
            f"SELECT * FROM {self.current_table}"
        )


        parameters = []


        search = (
            self.filter_text.get()
            .strip()
        )


        if search:

            conditions = []

            for column in self.columns:

                conditions.append(
                    f"CAST({column} AS TEXT) LIKE ?"
                )

                parameters.append(
                    f"%{search}%"
                )


            query += (
                " WHERE "
                + " OR ".join(conditions)
            )



        if self.sort_column:

            direction = (
                "DESC"
                if self.sort_reverse
                else "ASC"
            )

            query += (
                f" ORDER BY "
                f"{self.sort_column} "
                f"{direction}"
            )



        cursor.execute(
            query,
            parameters
        )


        rows = cursor.fetchall()

        connection.close()


        self.display_rows(
            rows
        )



    def display_rows(
        self,
        rows
    ):


        self.tree.delete(
            *self.tree.get_children()
        )


        self.tree["columns"] = self.columns

        self.tree["show"] = "headings"


        for column in self.columns:

            self.tree.heading(
                column,
                text=column,
                command=lambda c=column:
                    self.sort_by(c)
            )


            self.tree.column(
                column,
                width=120,
                minwidth=80,
                stretch=False
            )



        for row in rows:

            values = [
                row[column]
                for column in self.columns
            ]

            self.tree.insert(
                "",
                "end",
                values=values
            )


        self.status.config(
            text=f"Showing {len(rows)} records"
        )


    def show_record(
        self,
        event=None
    ):


        selection = self.tree.selection()


        if not selection:

            return


        item = self.tree.item(
            selection[0]
        )


        values = item["values"]


        detail_window = tk.Toplevel(
            self.root
        )


        detail_window.title(
            f"{self.current_table} Record"
        )


        detail_window.geometry(
            "500x600"
        )


        frame = ttk.Frame(
            detail_window
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )


        for column, value in zip(
            self.columns,
            values
        ):

            row = ttk.Frame(
                frame
            )

            row.pack(
                fill="x",
                pady=3
            )


            ttk.Label(
                row,
                text=f"{column}:",
                width=20
            ).pack(
                side="left",
                anchor="w"
            )


            value_label = ttk.Label(
                row,
                text=str(value),
                wraplength=300
            )

            value_label.pack(
                side="left",
                anchor="w"
            )
    

    def sort_by(
        self,
        column
    ):


        if self.sort_column == column:

            self.sort_reverse = (
                not self.sort_reverse
            )

        else:

            self.sort_column = column

            self.sort_reverse = False


        self.refresh_data()



    def clear_filter(
        self
    ):

        self.filter_text.set("")

        self.refresh_data()




def main():

    root = tk.Tk()

    DatabaseBrowser(
        root
    )

    root.mainloop()



if __name__ == "__main__":

    main()
