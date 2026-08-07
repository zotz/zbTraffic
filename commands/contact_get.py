#!/usr/bin/env python3

# File: commands/contact_get.py

import argparse

from traffic.contacts import (
    get_contact,
    format_contact
)


def main():

    parser = argparse.ArgumentParser(
        description="Display contact information"
    )


    parser.add_argument(
        "contact_id",
        type=int,
        help="Contact ID"
    )


    parser.add_argument(
        "--details",
        action="store_true",
        help="Include status information"
    )


    args = parser.parse_args()


    contact = get_contact(
        args.contact_id
    )


    if contact is None:

        print(
            "Contact not found:",
            args.contact_id
        )

        return


    print()

    print(
        format_contact(
            contact,
            include_status=args.details
        )
    )

    print()



if __name__ == "__main__":
    main()
