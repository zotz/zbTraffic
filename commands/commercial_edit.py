#!/usr/bin/env python3

import argparse

from traffic.commercials import (
    get_commercial,
    update_title,
    update_length,
    update_filename,
    update_cart_number,
    update_category,
    format_commercial
)


def display_commercial(commercial):

    print()

    print("Commercial Details")
    print("------------------")

    print(
        format_commercial(commercial)
    )

    print()



def main():

    parser = argparse.ArgumentParser(
        description="Edit commercial information"
    )

    parser.add_argument(
        "commercial_id",
        type=int,
        help="Commercial ID"
    )

    args = parser.parse_args()


    commercial = get_commercial(
        args.commercial_id
    )


    if commercial is None:

        print(
            "Commercial not found:",
            args.commercial_id
        )

        return


    while True:

        display_commercial(
            commercial
        )


        print("Options")
        print("-------")
        print("1 - Title")
        print("2 - Length")
        print("3 - Filename")
        print("4 - Cart Number")
        print("5 - Category")
        print("6 - Quit")

        print()


        choice = input(
            "Selection: "
        )


        if choice == "1":

            new_title = input(
                "New title: "
            )

            success, errors = update_title(
                args.commercial_id,
                new_title
            )


        elif choice == "2":

            new_length = input(
                "New length in seconds: "
            )

            success, errors = update_length(
                args.commercial_id,
                new_length
            )


        elif choice == "3":

            new_filename = input(
                "New filename: "
            )

            success, errors = update_filename(
                args.commercial_id,
                new_filename
            )


        elif choice == "4":

            new_cart = input(
                "New cart number: "
            )

            success, errors = update_cart_number(
                args.commercial_id,
                new_cart
            )


        elif choice == "5":

            new_category = input(
                "New category ID: "
            )


            try:

                new_category = int(
                    new_category
                )

            except ValueError:

                print(
                    "Category ID must be a number."
                )

                continue


            success, errors = update_category(
                args.commercial_id,
                new_category
            )


        elif choice == "6":

            print(
                "Leaving commercial edit."
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
                "Commercial updated successfully."
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


        # Refresh displayed information

        commercial = get_commercial(
            args.commercial_id
        )



if __name__ == "__main__":

    main()
