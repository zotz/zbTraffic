#!/usr/bin/env python3

# File: commands/avail_list.py

import argparse
import json

from traffic.avails import (
    list_avails,
    format_avail
)

def print_table(
    avails
):

    headers = [
        "ID",
        "Station",
        "Date",
        "Start",
        "Length",
        "Status"
    ]


    rows = []


    for avail in avails:

        rows.append(
            [
                str(avail["id"]),
                str(avail["station_id"]),
                avail["air_date"],
                avail["start_time"],
                str(avail["length_seconds"]),
                avail["status"] or ""
            ]
        )



    widths = []


    for index in range(
        len(headers)
    ):

        width = len(
            headers[index]
        )

        for row in rows:

            width = max(
                width,
                len(row[index])
            )

        widths.append(width)



    header_line = "  ".join(
        headers[i].ljust(widths[i])
        for i in range(len(headers))
    )


    print(
        header_line
    )


    print(
        "-" * len(header_line)
    )


    for row in rows:

        print(
            "  ".join(
                row[i].ljust(widths[i])
                for i in range(len(row))
            )
        )



def print_json(
    avails
):

    output = []


    for avail in avails:

        output.append(
            dict(avail)
        )


    print(
        json.dumps(
            output,
            indent=4
        )
    )

def main():

    parser = argparse.ArgumentParser(
        description="List avails"
    )


    parser.add_argument(
        "--station",
        type=int,
        help="Only show avails for this station ID"
    )


    parser.add_argument(
        "--date",
        help="Only show avails for this air date YYYY-MM-DD"
    )


    parser.add_argument(
        "--status",
        choices=[
            "Open",
            "Partial",
            "Filled",
            "Closed",
            "all"
        ],
        default="all",
        help="Avail status filter"
    )

    parser.add_argument(
        "--table",
        action="store_true",
        help="Display as table"
    )


    parser.add_argument(
        "--json",
        action="store_true",
        help="Display as JSON"
    )

    args = parser.parse_args()



    avails = list_avails(
        station_id=args.station,
        air_date=args.date,
        status=args.status
    )



    if not avails:

        print(
            "No avails found."
        )

        return



    if args.json:

        print_json(
            avails
        )

        return



    if args.table:

        print_table(
            avails
        )

        return



    for avail in avails:

        print()

        print(
            format_avail(
                avail
            )
        )

        print(
            "-" * 40
        )



if __name__ == "__main__":

    main()
