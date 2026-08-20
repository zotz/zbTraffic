#!/usr/bin/env python3

#
# File: prototype/log_reconcile.py
#
# Prototype / diagnostic GUI for reconciling exported zbTraffic
# spots against Rivendell playback results.
#

import argparse
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from traffic.database import get_connection


from traffic.rivendell import (
    CART_NUMBER_START,
    CART_NUMBER_END,
    TITLE_START,
    TITLE_END,
    LENGTH_START,
    LENGTH_END,
    MONTH_START,
    MONTH_END,
    DAY_START,
    DAY_END,
    YEAR_START,
    YEAR_END,
    HOUR_START,
    HOUR_END,
    MINUTE_START,
    MINUTE_END,
    SECOND_START,
    SECOND_END
)




#
# Matching states
#

MATCH = "MATCH"
TIME_WINDOW_MATCH = "TIME-WINDOW MATCH"
MISSING = "MISSING"
EXTRA = "EXTRA"


#
# Initial prototype setting.
#
# This is deliberately configurable in the GUI because we will
# probably want to learn what value makes sense from real logs.
#

DEFAULT_TIME_WINDOW_SECONDS = 190


#
# Time helpers
#

def time_to_seconds(value):

    hour, minute, second = (
        int(part)
        for part in value.split(":")
    )

    return (
        hour * 3600
        + minute * 60
        + second
    )


def format_difference(seconds):

    if seconds is None:
        return ""

    sign = "+" if seconds >= 0 else "-"

    seconds = abs(seconds)

    minutes = seconds // 60
    seconds = seconds % 60

    return f"{sign}{minutes}:{seconds:02d}"


def normalize_cart(value):

    if value is None:
        return ""

    text = str(value).strip()

    #
    # Database cart numbers and Rivendell cart numbers may
    # have different amounts of leading zeroes.
    #

    if text.isdigit():
        return str(int(text))

    return text


#
# Database
#

def load_exported_spots(
    air_date
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            spots.id,
            spots.air_date,
            spots.air_time,
            spots.status,

            commercials.cart_number,
            commercials.title,
            commercials.length_seconds

        FROM spots

        LEFT JOIN commercials
            ON spots.commercial_id = commercials.id

        WHERE

            spots.air_date = ?
            AND spots.status = 'Exported'

        ORDER BY
            spots.air_time,
            spots.id
        """,
        (
            air_date,
        )
    )

    spots = cursor.fetchall()

    connection.close()

    return spots


#
# Load spots from logfile and not db
#
def load_exported_spots_from_log(
    filename
):

    """
    Load the left-side traffic records from a zbTraffic
    Rivendell export log.

    The returned records have the same fields used by
    load_exported_spots(), so they can be passed directly
    to reconcile().
    """

    records = []

    with open(
        filename,
        "r",
        encoding="utf-8",
        errors="replace"
    ) as source:

        for line_number, raw_line in enumerate(
            source,
            start=1
        ):

            line = raw_line.rstrip(
                "\r\n"
            )

            if not line.strip():
                continue

            #
            # Ignore short/malformed records.
            #

            if len(line) < SECOND_END:
                continue

            #
            # Extract the fixed-width fields.
            #

            cart_number = line[
                CART_NUMBER_START:CART_NUMBER_END
            ].strip()

            title = line[
                TITLE_START:TITLE_END
            ].strip()

            length_text = line[
                LENGTH_START:LENGTH_END
            ].strip()

            month = line[
                MONTH_START:MONTH_END
            ].strip()

            day = line[
                DAY_START:DAY_END
            ].strip()

            year = line[
                YEAR_START:YEAR_END
            ].strip()

            hour = line[
                HOUR_START:HOUR_END
            ].strip()

            minute = line[
                MINUTE_START:MINUTE_END
            ].strip()

            second = line[
                SECOND_START:SECOND_END
            ].strip()

            #
            # Validate the numeric fields.
            #

            try:

                length_minutes = int(
                    length_text[:2]
                )

                length_seconds_part = int(
                    length_text[2:]
                )

                month = int(month)
                day = int(day)
                year = int(year)

                hour = int(hour)
                minute = int(minute)
                second = int(second)

            except ValueError:

                continue

            #
            # The export uses MMSS for commercial length.
            #

            length_seconds = (
                length_minutes * 60
                + length_seconds_part
            )

            #
            # Convert the two-digit year to the database's
            # four-digit ISO date format.
            #

            air_date = (
                f"20{year:02d}-"
                f"{month:02d}-"
                f"{day:02d}"
            )

            air_time = (
                f"{hour:02d}:"
                f"{minute:02d}:"
                f"{second:02d}"
            )

            records.append(
                {
                    #
                    # This is NOT a database spot ID.
                    # It is only a stable identifier for this
                    # record while performing the fake reconcile.
                    #
                    "id": line_number,

                    "air_date": air_date,
                    "air_time": air_time,
                    "status": "Exported",
                    "cart_number": cart_number,
                    "title": title,
                    "length_seconds": length_seconds
                }
            )

    return records




#
# Rivendell result parser
#

def parse_rivendell_file(
    filename
):

    """
    Parse the Rivendell result format.

    Example:

        16:45:00 16:49:06 0:00:30 00:00:29 000020 zbT Zephyr Life 30

    Fields:

        scheduled time
        actual time
        scheduled length
        played length
        cart number
        title
    """

    records = []

    with open(
        filename,
        "r",
        encoding="utf-8",
        errors="replace"
    ) as source:

        for line_number, raw_line in enumerate(
            source,
            start=1
        ):

            line = raw_line.rstrip(
                "\r\n"
            )

            if not line.strip():
                continue

            parts = line.split()

            if len(parts) < 6:
                continue

            scheduled_time = parts[0]
            actual_time = parts[1]
            scheduled_length = parts[2]
            played_length = parts[3]
            cart_number = parts[4]

            #
            # The title occupies the rest of the line.
            #

            title = " ".join(
                parts[5:]
            )

            try:

                scheduled_seconds = time_to_seconds(
                    scheduled_time
                )

                actual_seconds = time_to_seconds(
                    actual_time
                )


            except (
                ValueError,
                IndexError
            ):

                #
                # Ignore lines that don't look like Rivendell
                # result records.
                #

                continue

            records.append(
                {
                    "line_number": line_number,
                    "scheduled_time": scheduled_time,
                    "actual_time": actual_time,
                    "scheduled_length": scheduled_length,
                    "played_length": played_length,
                    "cart_number": cart_number,
                    "title": title,
                    "scheduled_seconds": scheduled_seconds,
                    "actual_seconds": actual_seconds
                }
            )

    return records


#
# Reconciliation
#

def reconcile(
    exported_spots,
    rivendell_records,
    time_window_seconds
):

    """
    Produce one reconciliation row for each exported spot
    and each unmatched Rivendell record.

    Matching rules:

        1. Same cart + exact scheduled time
        2. Same cart + scheduled times within the time window
        3. Exported spot with no counterpart = MISSING
        4. Rivendell record with no counterpart = EXTRA

    Rivendell actual playback time is deliberately NOT used
    for matching. The first Rivendell time is its scheduled time,
    which is the time corresponding to our traffic air_time.
    """

    unused_rivendell = set(
        range(
            len(rivendell_records)
        )
    )

    rows = []

    sorted_spots = sorted(
        exported_spots,
        key=lambda spot: (
            time_to_seconds(
                spot["air_time"]
            ),
            spot["id"]
        )
    )

    for spot in sorted_spots:

        cart = normalize_cart(
            spot["cart_number"]
        )

        our_seconds = time_to_seconds(
            spot["air_time"]
        )

        exact_matches = []

        window_matches = []

        for index in unused_rivendell:

            record = rivendell_records[index]

            if normalize_cart(
                record["cart_number"]
            ) != cart:

                continue

            difference = (
                record["scheduled_seconds"]
                - our_seconds
            )

            if difference == 0:

                exact_matches.append(
                    index
                )

            elif abs(difference) <= time_window_seconds:

                window_matches.append(
                    (
                        abs(difference),
                        index
                    )
                )

        if exact_matches:

            #
            # Normally there should only be one exact candidate.
            # Sorting makes the choice deterministic if there is
            # ever more than one.
            #

            index = sorted(
                exact_matches
            )[0]

            status = MATCH

        elif window_matches:

            #
            # If several candidates are within the window,
            # choose the closest one.
            #

            window_matches.sort()

            _, index = window_matches[0]

            status = TIME_WINDOW_MATCH

        else:

            index = None
            status = MISSING

        if index is not None:

            unused_rivendell.remove(
                index
            )

            record = rivendell_records[index]

            difference = (
                record["actual_seconds"]
                - our_seconds
            )

        else:

            record = None
            difference = None

        rows.append(
            {
                "status": status,

                #
                # Exact and time-window matches are initially
                # checked. The user can change this.
                #

                "checked": status in (
                    MATCH,
                    TIME_WINDOW_MATCH
                ),

                "spot": spot,
                "rivendell": record,
                "difference": difference
            }
        )

    #
    # Anything still unused on the Rivendell side is an
    # extra playback record.
    #

    remaining = sorted(
        unused_rivendell,
        key=lambda index: (
            rivendell_records[index]["scheduled_seconds"],
            index
        )
    )

    for index in remaining:

        rows.append(
            {
                "status": EXTRA,
                "checked": False,
                "spot": None,
                "rivendell": rivendell_records[index],
                "difference": None
            }
        )

    #
    # The rows above are initially ordered by our exported
    # spots, followed by extra Rivendell records. Sort the
    # combined reconciliation by the earliest time represented
    # by either side.
    #

    def row_sort_key(row):

        if row["spot"] is not None:

            return (
                time_to_seconds(
                    row["spot"]["air_time"]
                ),
                0
            )

        return (
            row["rivendell"]["scheduled_seconds"],
            1
        )

    rows.sort(
        key=row_sort_key
    )

    return rows


#
# GUI
#

class LogReconcileApp:

    def __init__(
        self,
        root
    ):

        self.root = root

        self.root.title(
            "zbTraffic Log Reconciliation"
        )

        self.root.geometry(
            "1450x750"
        )

        self.exported_spots = []
        self.rivendell_records = []
        self.rows = []

        self.build_gui()


    #
    # GUI construction
    #

    def build_gui(self):

        controls = ttk.Frame(
            self.root,
            padding=10
        )

        controls.pack(
            fill="x"
        )


        ttk.Label(
            controls,
            text="Air Date:"
        ).pack(
            side="left"
        )


        self.date_var = tk.StringVar()

        self.date_entry = ttk.Entry(
            controls,
            textvariable=self.date_var,
            width=12
        )

        self.date_entry.pack(
            side="left",
            padx=(5, 10)
        )


        ttk.Button(
            controls,
            text="Load Exported",
            command=self.load_exported
        ).pack(
            side="left",
            padx=3
        )


        ttk.Button(
            controls,
            text="Load Export Log",
            command=self.load_export_log
        ).pack(
            side="left",
            padx=3
        )




        ttk.Button(
            controls,
            text="Load Rivendell",
            command=self.load_rivendell
        ).pack(
            side="left",
            padx=3
        )


        ttk.Button(
            controls,
            text="Reconcile",
            command=self.do_reconcile
        ).pack(
            side="left",
            padx=3
        )


        ttk.Label(
            controls,
            text="Time window (sec):"
        ).pack(
            side="left",
            padx=(25, 5)
        )


        self.window_var = tk.StringVar(
            value=str(
                DEFAULT_TIME_WINDOW_SECONDS
            )
        )

        ttk.Entry(
            controls,
            textvariable=self.window_var,
            width=7
        ).pack(
            side="left"
        )


        #
        # Summary
        #

        summary = ttk.Frame(
            self.root,
            padding=(10, 0, 10, 10)
        )

        summary.pack(
            fill="x"
        )


        self.summary_var = tk.StringVar(
            value="No reconciliation loaded."
        )


        ttk.Label(
            summary,
            textvariable=self.summary_var
        ).pack(
            side="left"
        )


        #
        # Table
        #

        table_frame = ttk.Frame(
            self.root,
            padding=(10, 0, 10, 10)
        )

        table_frame.pack(
            fill="both",
            expand=True
        )


        columns = (
            "check",
            "status",
            "our_time",
            "our_cart",
            "our_title",
            "riv_scheduled",
            "riv_actual",
            "riv_cart",
            "riv_title",
            "difference"
        )


        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended"
        )


        headings = {
            "check": "",
            "status": "Match",
            "our_time": "Our Time",
            "our_cart": "Our Cart",
            "our_title": "Our Spot",
            "riv_scheduled": "Riv Scheduled",
            "riv_actual": "Riv Actual",
            "riv_cart": "Riv Cart",
            "riv_title": "Rivendell",
            "difference": "Time Diff"
        }


        widths = {
            "check": 45,
            "status": 125,
            "our_time": 80,
            "our_cart": 75,
            "our_title": 225,
            "riv_scheduled": 90,
            "riv_actual": 90,
            "riv_cart": 75,
            "riv_title": 250,
            "difference": 75
        }


        centered = {
            "check",
            "status",
            "our_time",
            "our_cart",
            "riv_scheduled",
            "riv_actual",
            "riv_cart",
            "difference"
        }


        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=widths[column],
                anchor=(
                    "center"
                    if column in centered
                    else "w"
                )
            )


        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )


        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )


        #
        # Prototype colors.
        #
        # We deliberately use tags here rather than baking colors
        # into the reconciliation algorithm. Later we can change
        # the visual rules without changing matching logic.
        #

        self.tree.tag_configure(
            "match_a",
            background="cyan4"
        )

        self.tree.tag_configure(
            "match_b",
            background="cyan3"
        )

        self.tree.tag_configure(
            "match_c",
            background="cyan2"
        )

        self.tree.tag_configure(
            "match_d",
            background="cyan"
        )

        self.tree.tag_configure(
            "match_a_checked",
            background="darkgreen"
        )

        self.tree.tag_configure(
            "match_b_checked",
            background="green4"
        )

        self.tree.tag_configure(
            "match_c_checked",
            background="green3"
        )

        self.tree.tag_configure(
            "match_d_checked",
            background="green2"
        )

        self.tree.tag_configure(
            "missing",
            background="misty rose"
        )

        self.tree.tag_configure(
            "extra",
            background="purple1"
        )


        #
        # Double-click a row to toggle its completion checkbox.
        #

        self.tree.bind(
            "<Double-1>",
            self.toggle_checked
        )


        #
        # Bottom actions
        #

        actions = ttk.Frame(
            self.root,
            padding=10
        )

        actions.pack(
            fill="x"
        )


        ttk.Button(
            actions,
            text="Mark Checked Completed",
            command=self.mark_checked_completed
        ).pack(
            side="left",
            padx=3
        )


        ttk.Button(
            actions,
            text="Mark All Matched Completed",
            command=self.mark_all_matched_completed
        ).pack(
            side="left",
            padx=3
        )


        ttk.Label(
            actions,
            text="Double-click a row to check/uncheck it."
        ).pack(
            side="right"
        )


    #
    # Loading
    #

    def load_exported(self):

        air_date = self.date_var.get().strip()

        if not air_date:

            messagebox.showwarning(
                "Air Date",
                "Enter an air date first."
            )

            return


        try:

            self.exported_spots = load_exported_spots(
                air_date
            )

        except Exception as error:

            messagebox.showerror(
                "Database Error",
                str(error)
            )

            return


        self.rows = []

        self.clear_table()


        self.summary_var.set(
            f"Loaded {len(self.exported_spots)} exported spot(s)."
        )


    def load_export_log(self):

        filename = filedialog.askopenfilename(
            title="Load zbTraffic Export Log",
            filetypes=(
                (
                    "zbTraffic log files",
                    "*.log"
                ),
                (
                    "All files",
                    "*"
                )
            )
        )

        if not filename:
            return


        try:

            self.exported_spots = load_exported_spots_from_log(
                filename
            )

        except Exception as error:

            messagebox.showerror(
                "Log Error",
                str(error)
            )

            return


        self.rows = []

        self.clear_table()


        self.summary_var.set(
            f"Loaded {len(self.exported_spots)} spot(s) "
            "from export log."
        )




    def load_rivendell(self):

        filename = filedialog.askopenfilename(
            title="Select Rivendell result file",
            filetypes=[
                (
                    "Text files",
                    "*.txt *.log"
                ),
                (
                    "All files",
                    "*"
                )
            ]
        )

        if not filename:
            return


        try:

            self.rivendell_records = parse_rivendell_file(
                filename
            )

        except Exception as error:

            messagebox.showerror(
                "Rivendell File Error",
                str(error)
            )

            return


        self.rows = []

        self.clear_table()


        self.summary_var.set(
            f"Loaded {len(self.rivendell_records)} Rivendell record(s)."
        )


    #
    # Reconcile
    #

    def do_reconcile(self):

        if not self.exported_spots:

            messagebox.showwarning(
                "Reconcile",
                "Load exported spots first."
            )

            return


        if not self.rivendell_records:

            messagebox.showwarning(
                "Reconcile",
                "Load a Rivendell result file first."
            )

            return


        try:

            time_window = int(
                self.window_var.get()
            )

            if time_window < 0:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Time Window",
                "Time window must be a non-negative number of seconds."
            )

            return


        self.rows = reconcile(
            self.exported_spots,
            self.rivendell_records,
            time_window
        )


        self.display_rows()


    #
    # Display
    #

    def clear_table(self):

        for item in self.tree.get_children():

            self.tree.delete(
                item
            )


    def display_rows(self):

        self.clear_table()


        counts = {
            MATCH: 0,
            TIME_WINDOW_MATCH: 0,
            MISSING: 0,
            EXTRA: 0
        }


        for row_number, row in enumerate(
            self.rows
        ):

            status = row["status"]

            counts[status] += 1


            spot = row["spot"]
            rivendell = row["rivendell"]


            if spot is not None:

                our_time = spot["air_time"]
                our_cart = spot["cart_number"]
                our_title = spot["title"] or ""

            else:

                our_time = ""
                our_cart = ""
                our_title = ""


            if rivendell is not None:

                riv_scheduled = (
                    rivendell["scheduled_time"]
                )

                riv_actual = (
                    rivendell["actual_time"]
                )

                riv_cart = (
                    rivendell["cart_number"]
                )

                riv_title = (
                    rivendell["title"]
                )

            else:

                riv_scheduled = ""
                riv_actual = ""
                riv_cart = ""
                riv_title = ""


            difference = format_difference(
                row["difference"]
            )


            checked = (
                "☑"
                if row["checked"]
                else "☐"
            )


            values = (
                checked,
                status,
                our_time,
                our_cart,
                our_title,
                riv_scheduled,
                riv_actual,
                riv_cart,
                riv_title,
                difference
            )

            if status in (
                MATCH,
                TIME_WINDOW_MATCH
            ):

                difference = row["difference"]

                if difference is None:

                    tag = "match_a"

                else:

                    difference_seconds = abs(
                        difference
                    )

                    if difference_seconds <= 180:

                        tag = "match_a"

                    elif difference_seconds <= 360:

                        tag = "match_b"

                    elif difference_seconds <= 600:

                        tag = "match_c"

                    else:

                        tag = "match_d"


                    if row["checked"]:

                        tag = f"{tag}_checked"

            elif status == MISSING:

                tag = "missing"

            else:

                tag = "extra"



            self.tree.insert(
                "",
                "end",
                iid=str(row_number),
                values=values,
                tags=(tag,)
            )


        self.update_summary(
            counts
        )


    def update_summary(
        self,
        counts
    ):

        checked = sum(
            1
            for row in self.rows
            if row["checked"]
        )


        self.summary_var.set(
            "Exported: "
            f"{len(self.exported_spots)}    "
            "Rivendell: "
            f"{len(self.rivendell_records)}    "
            "Match: "
            f"{counts[MATCH]}    "
            "Time-window: "
            f"{counts[TIME_WINDOW_MATCH]}    "
            "Missing: "
            f"{counts[MISSING]}    "
            "Extra: "
            f"{counts[EXTRA]}    "
            "Checked: "
            f"{checked}"
        )


    #
    # Checkbox handling
    #

    def toggle_checked(
        self,
        event
    ):

        item = self.tree.identify_row(
            event.y
        )

        if not item:
            return


        row_number = int(
            item
        )

        row = self.rows[row_number]


        #
        # A missing or extra row has no exported database spot
        # to complete, so it cannot be checked.
        #

        if row["spot"] is None:
            return


        row["checked"] = not row["checked"]


        self.display_rows()


    #
    # Completion
    #

    def mark_checked_completed(self):

        spot_ids = [
            row["spot"]["id"]
            for row in self.rows
            if (
                row["checked"]
                and row["spot"] is not None
            )
        ]


        if not spot_ids:

            messagebox.showinfo(
                "Complete Spots",
                "There are no checked spots to mark Completed."
            )

            return


        confirmed = messagebox.askyesno(
            "Complete Spots",
            f"Mark {len(spot_ids)} checked spot(s) as Completed?"
        )

        if not confirmed:
            return


        connection = get_connection()

        cursor = connection.cursor()


        try:

            for spot_id in spot_ids:

                cursor.execute(
                    """
                    UPDATE spots

                    SET status = 'Completed'

                    WHERE
                        id = ?
                        AND status = 'Exported'
                    """,
                    (
                        spot_id,
                    )
                )


            connection.commit()

        except Exception as error:

            connection.rollback()
            connection.close()

            messagebox.showerror(
                "Database Error",
                str(error)
            )

            return


        connection.close()


        self.reload_after_completion(
            len(spot_ids)
        )


    def mark_all_matched_completed(self):

        #
        # "Matched" deliberately means either an exact match or
        # a time-window match. Missing and extra rows are excluded.
        #

        spot_ids = [
            row["spot"]["id"]
            for row in self.rows
            if (
                row["spot"] is not None
                and row["rivendell"] is not None
            )
        ]


        if not spot_ids:

            messagebox.showinfo(
                "Complete All Matched",
                "There are no matched spots."
            )

            return


        confirmed = messagebox.askyesno(
            "Complete All Matched",
            f"Mark all {len(spot_ids)} matched spot(s) as Completed?"
        )

        if not confirmed:
            return


        connection = get_connection()

        cursor = connection.cursor()


        try:

            for spot_id in spot_ids:

                cursor.execute(
                    """
                    UPDATE spots

                    SET status = 'Completed'

                    WHERE
                        id = ?
                        AND status = 'Exported'
                    """,
                    (
                        spot_id,
                    )
                )


            connection.commit()

        except Exception as error:

            connection.rollback()
            connection.close()

            messagebox.showerror(
                "Database Error",
                str(error)
            )

            return


        connection.close()


        self.reload_after_completion(
            len(spot_ids)
        )


    def reload_after_completion(
        self,
        count
    ):

        #
        # Keep the Rivendell file loaded so the user can reconcile
        # the remaining Exported spots again.
        #

        try:

            self.exported_spots = load_exported_spots(
                self.date_var.get().strip()
            )

        except Exception as error:

            messagebox.showerror(
                "Database Error",
                str(error)
            )

            return


        self.rows = []


        self.clear_table()


        self.summary_var.set(
            f"Marked {count} spot(s) Completed. "
            "Press Reconcile to review the remaining Exported spots."
        )


#
# Main
#

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Prototype GUI for reconciling exported spots "
            "with Rivendell playback"
        )
    )


    parser.add_argument(
        "--date",
        help="Air date YYYY-MM-DD"
    )


    args = parser.parse_args()


    root = tk.Tk()

    app = LogReconcileApp(
        root
    )


    if args.date:

        app.date_var.set(
            args.date
        )


    root.mainloop()


if __name__ == "__main__":

    main()

