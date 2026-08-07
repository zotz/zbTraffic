#!/usr/bin/env python3

# File: commands/spot_list.py

import argparse
import json

from traffic.spots import (
    list_spots_with_details,
    format_spot
)

def display_value(
    value
):

    if value is None:

        return ""

    return str(value)

def print_table(
    spots
):

    headers = [
        "ID",
        "Date",
        "Time",
        "Customer",
        "Cart",
        "Title",
        "Status"
    ]


    rows = []

    for spot in spots:

        rows.append(
            [
                str(spot["id"]),
                display_value(spot["air_date"]),
                display_value(spot["air_time"]),
                display_value(spot["company_name"]),
                display_value(spot["cart_number"]),
                display_value(spot["title"]),
                display_value(spot["status"])
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



def json_output(
    spots
):

    output = []

    for spot in spots:

        output.append(
            dict(spot)
        )


    print(
        json.dumps(
            output,
            indent=4
        )
    )



def main():

    parser = argparse.ArgumentParser(
        description="List spots"
    )


    parser.add_argument(
        "--status",
        help="Filter by status"
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


    spots = list_spots_with_details(
        args.status
    )


    if not spots:

        print(
            "No spots found."
        )

        return


    if args.json:

        json_output(
            spots
        )

        return


    if args.table:

        print_table(
            spots
        )

        return


    for spot in spots:

        print(
            format_spot(spot)
        )

        print(
            "-" * 40
        )



if __name__ == "__main__":

    main()
