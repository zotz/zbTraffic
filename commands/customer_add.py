#!/usr/bin/env python3

# File: commands/customer_add.py

from traffic.customers import add_customer


def main():

    print()
    print("Add New Customer")
    print("----------------")
    print()

    company_name = input("Company name: ")

    telephone = input("Telephone: ")

    email = input("Email: ")


    customer_id, errors = add_customer(
        company_name,
        telephone,
        email
    )


    print()


    if errors:

        print("Customer was not added.")

        for error in errors:

            print("-", error)

    else:

        print("Customer added.")

        print(
            "Customer ID:",
            customer_id
        )


if __name__ == "__main__":
    main()
