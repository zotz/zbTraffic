#!/usr/bin/env python3

# File: commands/category_activate.py

import argparse

from traffic.categories import (
    activate_category
)


def main():

    parser = argparse.ArgumentParser(
        description="Activate a category"
    )


    parser.add_argument(
        "category_id",
        type=int,
        help="Category ID"
    )


    args = parser.parse_args()


    success, errors = activate_category(
        args.category_id
    )


    if success:

        print()
        print(
            "Category activated successfully."
        )


    else:

        print()
        print(
            "Activation failed:"
        )


        for error in errors:

            print(
                "-",
                error
            )



if __name__ == "__main__":

    main()
