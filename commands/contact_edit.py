#!/usr/bin/env python3

# File: commands/contact_edit.py

import argparse

from traffic.contacts import (
    get_contact,
    update_first_name,
    update_last_name,
    update_job_title,
    update_telephone,
    update_email
)


def display_contact(contact):

    print()

    print("Contact Details")
    print("----------------")

    print("ID:", contact["id"])
    print("Customer:", contact["company_name"])
    print(
        "Name:",
        contact["first_name"],
        contact["last_name"]
    )
    print("Job Title:", contact["job_title"])
    print("Telephone:", contact["telephone"])
    print("Email:", contact["email"])

    print()



def main():

    parser = argparse.ArgumentParser(
        description="Edit contact information"
    )


    parser.add_argument(
        "contact_id",
        type=int,
        help="Contact ID"
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



    while True:

        display_contact(contact)


        print("Options")
        print("-------")
        print("1 - First Name")
        print("2 - Last Name")
        print("3 - Job Title")
        print("4 - Telephone")
        print("5 - Email")
        print("6 - Quit")

        print()


        choice = input(
            "Selection: "
        )


        if choice == "1":

            value = input(
                "New first name: "
            )

            success, errors = update_first_name(
                args.contact_id,
                value
            )


        elif choice == "2":

            value = input(
                "New last name: "
            )

            success, errors = update_last_name(
                args.contact_id,
                value
            )


        elif choice == "3":

            value = input(
                "New job title: "
            )

            success, errors = update_job_title(
                args.contact_id,
                value
            )


        elif choice == "4":

            value = input(
                "New telephone: "
            )

            success, errors = update_telephone(
                args.contact_id,
                value
            )


        elif choice == "5":

            value = input(
                "New email: "
            )

            success, errors = update_email(
                args.contact_id,
                value
            )


        elif choice == "6":

            print(
                "Leaving contact edit."
            )

            break


        else:

            print(
                "Invalid selection."
            )

            continue



        if success:

            print(
                "Contact updated successfully."
            )

        else:

            print(
                "Update failed:"
            )

            for error in errors:

                print(
                    "-",
                    error
                )


        # Refresh displayed information

        contact = get_contact(
            args.contact_id
        )



if __name__ == "__main__":
    main()
