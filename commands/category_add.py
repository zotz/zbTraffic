#!/usr/bin/env python3

# File: commands/category_add.py

import argparse

from traffic.categories import add_category



def main():

    parser = argparse.ArgumentParser(
        description="Add a new category"
    )


    parser.add_argument(
        "name",
        help="Category name"
    )


    args = parser.parse_args()


    category_id, errors = add_category(
        args.name
    )


    if category_id is None:

        print(
            "Category could not be added."
        )

        for error in errors:

            print(
                "-",
                error
            )

        return


    print(
        "Category added successfully."
    )

    print(
        "ID:",
        category_id
    )



if __name__ == "__main__":

    main()
