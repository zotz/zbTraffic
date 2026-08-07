#!/usr/bin/env python3

# File: commands/customer_deactivate.py

import argparse

from traffic.customers import (
    get_customer,
    deactivate_customer
)


def main():

    parser = argparse.ArgumentParser(
        description="Deactivate a customer"
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

        print("Customer not found.")

        return


    print()

    print(
        "Deactivate customer:"
    )

    print(
        customer["company_name"]
    )

    print()


    confirm = input(
        "Continue? (y/n): "
    )


    if confirm.lower() != "y":

        print(
            "Cancelled."
        )

        return


    success, errors = deactivate_customer(
        args.customer_id
    )


    if success:

        print(
            "Customer deactivated."
        )

    else:

        print(
            "Unable to deactivate customer."
        )

        for error in errors:

            print(
                "-",
                error
            )


if __name__ == "__main__":
    main()
