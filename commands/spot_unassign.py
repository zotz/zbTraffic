#!/usr/bin/env python3

# File: commands/spot_unassign.py


import sys

from traffic.assignment import (
    remove_spot_from_avail
)



def unassign(
    spot_id
):

    success, errors = remove_spot_from_avail(
        spot_id
    )


    if not success:

        print()

        print(
            "Unassign failed:"
        )

        for error in errors:

            print(
                error
            )

        return



    print()

    print(
        "Spot unassigned successfully."
    )

    print(
        f"Spot {spot_id} returned to Pending."
    )



def main():


    #
    # Command line mode
    #
    # Example:
    # python3 -m commands.spot_unassign 156
    #

    if len(sys.argv) == 2:

        try:

            spot_id = int(
                sys.argv[1]
            )

        except ValueError:

            print(
                "Spot ID must be a number."
            )

            return


        unassign(
            spot_id
        )

        return



    #
    # Interactive mode
    #

    print()

    print(
        "Unassign Spot from Avail"
    )

    print(
        "======================="
    )

    print()


    try:

        spot_id = int(
            input("Spot ID: ")
        )


    except ValueError:

        print(
            "Spot ID must be a number."
        )

        return



    unassign(
        spot_id
    )



if __name__ == "__main__":

    main()
