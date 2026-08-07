#!/usr/bin/env python3

# File: commands/contact_deactivate.py

import argparse

from traffic.contacts import deactivate_contact


def main():

    parser = argparse.ArgumentParser(
        description="Deactivate a contact"
    )


    parser.add_argument(
        "contact_id",
        type=int,
        help="Contact ID"
    )


    args = parser.parse_args()


    success, errors = deactivate_contact(
        args.contact_id
    )


    if success:

        print(
            "Contact deactivated successfully."
        )

        return


    print(
        "Unable to deactivate contact."
    )


    for error in errors:

        print(
            "-",
            error
        )



if __name__ == "__main__":
    main()
