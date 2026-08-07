#!/usr/bin/env python3

# File: commands/category_deactivate.py

import argparse

from traffic.categories import (
    deactivate_category
)


def main():

    parser = argparse.ArgumentParser(
        description="Deactivate a category"
    )


    parser.add_argument(
        "category_id",
        type=int,
        help="Category ID"
    )


    args = parser.parse_args()


    success, errors = deactivate_category(
        args.category_id
    )


    if success:

        print()
        print(
            "Category deactivated successfully."
        )


    else:

        print()
        print(
            "Deactivation failed:"
        )


        for error in errors:

            print(
                "-",
                error
            )



if __name__ == "__main__":

    main()
