#!/usr/bin/env python3

# File: commands/contact_activate.py

import argparse

from traffic.contacts import activate_contact


def main():

    parser = argparse.ArgumentParser(
        description="Activate a contact"
    )


    parser.add_argument(
        "contact_id",
        type=int,
        help="Contact ID"
    )


    args = parser.parse_args()


    success, errors = activate_contact(
        args.contact_id
    )


    if success:

        print(
            "Contact activated successfully."
        )

        return


    print(
        "Unable to activate contact."
    )


    for error in errors:

        print(
            "-",
            error
        )



if __name__ == "__main__":
    main()
