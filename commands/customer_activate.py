#!/usr/bin/env python3

# File: commands/customer_activate.py

import argparse

from traffic.customers import (
    get_customer,
    activate_customer
)


def main():

    parser = argparse.ArgumentParser(
        description="Activate a customer"
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


    success, errors = activate_customer(
        args.customer_id
    )


    if success:

        print(
            "Customer activated:",
            customer["company_name"]
        )

    else:

        print(
            "Unable to activate customer."
        )

        for error in errors:

            print(
                "-",
                error
            )


if __name__ == "__main__":
    main()
