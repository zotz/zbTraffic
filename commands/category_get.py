#!/usr/bin/env python3

# File: commands/category_get.py

import argparse

from traffic.categories import (
    get_category,
    format_category
)


def main():

    parser = argparse.ArgumentParser(
        description="Get category details"
    )


    parser.add_argument(
        "category_id",
        type=int,
        help="Category ID"
    )


    args = parser.parse_args()


    category = get_category(
        args.category_id
    )


    if category is None:

        print(
            "Category not found:",
            args.category_id
        )

        return


    print(
        format_category(category)
    )



if __name__ == "__main__":

    main()
