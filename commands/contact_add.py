#!/usr/bin/env python3

# File: commands/contact_add.py

import argparse

from traffic.contacts import add_contact


def main():

    parser = argparse.ArgumentParser(
        description="Add a new contact"
    )


    parser.add_argument(
        "customer_id",
        type=int,
        help="Customer ID"
    )


    args = parser.parse_args()


    print()
    print("Add Contact")
    print("-----------")
    print()


    first_name = input(
        "First name: "
    )


    last_name = input(
        "Last name: "
    )


    job_title = input(
        "Job title (optional): "
    )


    telephone = input(
        "Telephone (optional): "
    )


    email = input(
        "Email (optional): "
    )


    contact_id, errors = add_contact(
        args.customer_id,
        first_name,
        last_name,
        job_title if job_title else None,
        telephone if telephone else None,
        email if email else None
    )


    if contact_id is None:

        print()
        print(
            "Contact could not be added."
        )

        for error in errors:

            print(
                "-",
                error
            )

        return


    print()

    print(
        "Contact added successfully."
    )

    print(
        "Contact ID:",
        contact_id
    )



if __name__ == "__main__":
    main()
