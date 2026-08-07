#!/usr/bin/env python3

# File: commands/customer_edit.py

import argparse

from traffic.customers import (
    get_customer,
    update_company_name,
    update_telephone,
    update_email
)


def display_customer(customer):

    print()

    print("Customer Details")
    print("----------------")

    print("ID:", customer["id"])
    print("Company:", customer["company_name"])
    print("Telephone:", customer["telephone"])
    print("Email:", customer["email"])

    print()



def main():

    parser = argparse.ArgumentParser(
        description="Edit customer information"
    )

    parser.add_argument(
        "customer_id",
        type=int,
        help="Customer ID"
    )

    args = parser.parse_args()


    customer = get_customer(
        args.customer_id
    )


    if customer is None:

        print(
            "Customer not found:",
            args.customer_id
        )

        return


    while True:

        display_customer(customer)

        print("Options")
        print("-------")
        print("1 - Company Name")
        print("2 - Telephone")
        print("3 - Email")
        print("4 - Quit")

        print()

        choice = input(
            "Selection: "
        )


        if choice == "1":

            new_name = input(
                "New company name: "
            )


            success, errors = update_company_name(
                args.customer_id,
                new_name
            )


        elif choice == "2":

            new_phone = input(
                "New telephone: "
            )


            success, errors = update_telephone(
                args.customer_id,
                new_phone
            )


        elif choice == "3":

            new_email = input(
                "New email: "
            )


            success, errors = update_email(
                args.customer_id,
                new_email
            )


        elif choice == "4":

            print("Leaving customer edit.")

            break


        else:

            print(
                "Invalid selection."
            )

            continue


        if success:

            print(
                "Customer updated successfully."
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
        customer = get_customer(
            args.customer_id
        )



if __name__ == "__main__":
    main()
