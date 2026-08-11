#!/usr/bin/env python3

#
# database/seed2big_database.py
#
# Import the expanded customer and commercial test data.
#
# This script is intentionally separate from seed2_database.py.
# The existing seed scripts remain unchanged while this new
# CSV-based import system is developed and tested.
#

from database.import_customers_csv import import_customers_csv
from database.import_commercials_csv import import_commercials_csv


CUSTOMERS_CSV = "database/data/customers_big.csv"
COMMERCIALS_CSV = "database/data/commercials_big.csv"


def main():

    print()
    print("========================================")
    print("Expanded Seed Data")
    print("========================================")
    print()

    #
    # Customers
    #

    print("Importing expanded customers...")
    print()

    customer_count = import_customers_csv(
        CUSTOMERS_CSV
    )

    print()
    print(
        f"Imported {customer_count} expanded customers."
    )
    print()

    #
    # Commercials
    #

    print("Importing expanded commercials...")
    print()

    commercial_count = import_commercials_csv(
        COMMERCIALS_CSV
    )

    print()
    print(
        f"Imported {commercial_count} expanded commercials."
    )
    print()


if __name__ == "__main__":
    main()

