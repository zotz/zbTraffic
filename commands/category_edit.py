#!/usr/bin/env python3

# File: commands/category_edit.py

import argparse

from traffic.categories import (
    get_category,
    update_name,
    format_category
)


def display_category(category):

    print()

    print("Category Details")
    print("----------------")

    print(
        format_category(category)
    )

    print()



def main():

    parser = argparse.ArgumentParser(
        description="Edit category information"
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



    while True:

        display_category(
            category
        )


        print("Options")
        print("-------")
        print("1 - Name")
        print("2 - Quit")

        print()


        choice = input(
            "Selection: "
        )


        if choice == "1":

            new_name = input(
                "New category name: "
            )


            success, errors = update_name(
                args.category_id,
                new_name
            )


        elif choice == "2":

            print(
                "Leaving category edit."
            )

            break


        else:

            print(
                "Invalid selection."
            )

            continue



        if success:

            print()
            print(
                "Category updated successfully."
            )


        else:

            print()
            print(
                "Update failed:"
            )


            for error in errors:

                print(
                    "-",
                    error
                )



        category = get_category(
            args.category_id
        )



if __name__ == "__main__":

    main()
