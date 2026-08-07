#!/usr/bin/env python3

# File: commands/category_list.py

import argparse
import json

from traffic.categories import (
    list_categories,
    format_category
)


def print_table(
    categories
):

    headers = [
        "ID",
        "Name",
        "Status"
    ]


    rows = []

    for category in categories:

        status = (
            "Active"
            if category["active"]
            else "Inactive"
        )


        rows.append(
            [
                str(category["id"]),
                category["name"],
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
    categories
):

    output = []

    for category in categories:

        output.append(
            dict(category)
        )


    print(
        json.dumps(
            output,
            indent=4
        )
    )



def main():

    parser = argparse.ArgumentParser(
        description="List categories"
    )


    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Show inactive categories only"
    )


    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all categories"
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



    categories = list_categories(
        status
    )


    if not categories:

        print(
            "No categories found."
        )

        return



    if args.json:

        print_json(
            categories
        )

        return



    if args.table:

        print_table(
            categories
        )

        return



    for category in categories:

        print(
            format_category(category)
        )

        print(
            "-" * 30
        )



if __name__ == "__main__":

    main()
