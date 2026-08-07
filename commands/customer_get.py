#!/usr/bin/env python3

# File: commands/customer_get.py

import argparse

from traffic.customers import get_customer


def main():

    parser = argparse.ArgumentParser(
        description="Display customer information"
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


    print()

    if customer is None:

        print(
            "Customer not found:",
            args.customer_id
        )

        return


    print("Customer Details")
    print("----------------")

    print(
        "ID:",
        customer["id"]
    )

    print(
        "Company:",
        customer["company_name"]
    )

    print(
        "Telephone:",
        customer["telephone"]
    )

    print(
        "Email:",
        customer["email"]
    )


if __name__ == "__main__":
    main()
