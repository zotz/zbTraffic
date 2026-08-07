#!/usr/bin/env python3

# File: commands/commercial_list.py

import argparse
import json

from traffic.commercials import (
    list_commercials,
    format_commercial_summary
)


def print_table(
    commercials
):

    headers = [
        "ID",
        "Customer",
        "Cart",
        "Title",
        "Length",
        "Status"
    ]


    rows = []

    for commercial in commercials:

        status = (
            "Active"
            if commercial["active"]
            else "Inactive"
        )


        rows.append(
            [
                str(commercial["id"]),
                commercial["company_name"],
                commercial["cart_number"] or "",
                commercial["title"],
                f"{commercial['length_seconds']} sec",
                status
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
    commercials
):

    output = []

    for commercial in commercials:

        output.append(
            dict(commercial)
        )


    print(
        json.dumps(
            output,
            indent=4
        )
    )



def main():

    parser = argparse.ArgumentParser(
        description="List commercials"
    )


    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Show inactive commercials only"
    )


    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all commercials"
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



    if args.all:

        status = "all"

    elif args.inactive:

        status = "inactive"

    else:

        status = "active"



    commercials = list_commercials(
        status
    )


    if not commercials:

        print(
            "No commercials found."
        )

        return



    if args.json:

        print_json(
            commercials
        )

        return



    if args.table:

        print_table(
            commercials
        )

        return



    print()

    print(
        "Commercials"
    )

    print(
        "-----------"
    )


    for commercial in commercials:

        print()

        print(
            format_commercial_summary(
                commercial
            )
        )



if __name__ == "__main__":

    main()
