#!/usr/bin/env python3

from traffic.commercials import add_commercial


def main():

    print()
    print("Add Commercial")
    print("----------------")
    print()

    #
    # Customer ID
    #

    customer_id = input(
        "Customer ID: "
    ).strip()


    if not customer_id.isdigit():

        print()
        print(
            "Customer ID must be a number."
        )
        return


    customer_id = int(
        customer_id
    )


    #
    # Title
    #

    title = input(
        "Title: "
    ).strip()


    #
    # Length
    #

    length_seconds = input(
        "Length in seconds: "
    ).strip()


    if not length_seconds.isdigit():

        print()
        print(
            "Length must be an integer."
        )
        return


    length_seconds = int(
        length_seconds
    )


    #
    # Optional fields
    #

    filename = input(
        "Filename (optional): "
    ).strip()


    if filename == "":

        filename = None


    cart_number = input(
        "Cart Number (optional): "
    ).strip()


    if cart_number == "":

        cart_number = None


    category_id = input(
        "Category ID (optional): "
    ).strip()


    if category_id == "":

        category_id = None

    else:

        if not category_id.isdigit():

            print()
            print(
                "Category ID must be a number."
            )
            return


        category_id = int(
            category_id
        )


    #
    # Add the commercial
    #

    commercial_id, errors = add_commercial(

        customer_id,
        title,
        length_seconds,
        filename,
        cart_number,
        category_id

    )


    if errors:

        print()

        for error in errors:

            print(
                f"ERROR: {error}"
            )

        return


    print()
    print(
        f"Commercial {commercial_id} added successfully."
    )
    print()


if __name__ == "__main__":

    main()
