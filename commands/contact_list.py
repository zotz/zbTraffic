#!/usr/bin/env python3

# File: commands/contact_list.py

import argparse
import json

from traffic.contacts import (
    list_contacts,
    format_contact
)


def print_table(
    contacts
):

    headers = [
        "ID",
        "Customer",
        "Name",
        "Title",
        "Telephone",
        "Email",
        "Status"
    ]


    rows = []

    for contact in contacts:

        status = (
            "Active"
            if contact["active"]
            else "Inactive"
        )


        rows.append(
            [
                str(contact["id"]),
                contact["company_name"],
                (
                    f"{contact['first_name']} "
                    f"{contact['last_name']}"
                ),
                contact["job_title"] or "",
                contact["telephone"] or "",
                contact["email"] or "",
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
    contacts
):

    output = []

    for contact in contacts:

        output.append(
            dict(contact)
        )


    print(
        json.dumps(
            output,
            indent=4
        )
    )



def main():

    parser = argparse.ArgumentParser(
        description="List contacts"
    )


    parser.add_argument(
        "--customer",
        type=int,
        help="Only show contacts for this customer ID"
    )


    parser.add_argument(
        "--status",
        choices=[
            "active",
            "inactive",
            "all"
        ],
        default="active",
        help="Contact status filter"
    )


    parser.add_argument(
        "--details",
        action="store_true",
        help="Include status information"
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


    try:

        contacts = list_contacts(
            customer_id=args.customer,
            status=args.status
        )


    except ValueError as error:

        print(
            error
        )

        return



    if not contacts:

        print(
            "No contacts found."
        )

        return



    if args.json:

        print_json(
            contacts
        )

        return



    if args.table:

        print_table(
            contacts
        )

        return



    for contact in contacts:

        print()

        print(
            format_contact(
                contact,
                include_status=args.details
            )
        )

        print(
            "-" * 40
        )



if __name__ == "__main__":

    main()
