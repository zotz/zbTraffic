#!/usr/bin/env python3

# File: commands/customer_list.py

import argparse
import json

from traffic.customers import (
    list_customers,
    format_customer
)


def print_table(
    customers
):

    headers = [
        "ID",
        "Company",
        "Telephone",
        "Email",
        "Active"
    ]


    rows = []

    for customer in customers:

        rows.append(
            [
                str(customer["id"]),
                customer["company_name"] or "",
                customer["telephone"] or "",
                customer["email"] or "",
                str(customer["active"])
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
    customers
):

    output = []

    for customer in customers:

        output.append(
            dict(customer)
        )


    print(
        json.dumps(
            output,
            indent=4
        )
    )



def main():

    parser = argparse.ArgumentParser(
        description="List customers"
    )


    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Show inactive customers only"
    )


    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all customers"
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



    customers = list_customers(
        status
    )



    if not customers:

        print(
            "No customers found."
        )

        return



    if args.json:

        print_json(
            customers
        )

        return



    if args.table:

        print_table(
            customers
        )

        return



    print()

    if status == "active":

        print(
            "Active Customers"
        )

    elif status == "inactive":

        print(
            "Inactive Customers"
        )

    else:

        print(
            "All Customers"
        )


    print(
        "----------------"
    )

    print()


    for customer in customers:

        print(
            format_customer(
                customer,
                include_status=(status == "all")
            )
        )

        print()
        

if __name__ == "__main__":

    main()
