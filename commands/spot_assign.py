#!/usr/bin/env python3

# File: commands/spot_assign.py

import sys

from traffic.assignment import (
    assign_spot_to_avail
)

from traffic.spots import (
    get_spot
)


def assign(
    spot_id,
    avail_id
):

    success, errors = assign_spot_to_avail(
        spot_id,
        avail_id
    )


    if not success:

        print(
            "Assignment failed:"
        )

        for error in errors:

            print(
                f"- {error}"
            )

        return False



    print(
        "Assignment successful."
    )


    spot = get_spot(
        spot_id
    )


    print()

    print(
        "Updated Spot:"
    )

    print(
        f"ID:        {spot['id']}"
    )

    print(
        f"Status:    {spot['status']}"
    )

    print(
        f"Avail ID:  {spot['avail_id']}"
    )

    print(
        f"Air Date:  {spot['air_date']}"
    )

    print(
        f"Air Time:  {spot['air_time']}"
    )


    return True



def main():

    #
    # Command line mode
    #
    # Example:
    # python3 -m commands.spot_assign 156 6
    #

    if len(sys.argv) == 3:

        try:

            spot_id = int(
                sys.argv[1]
            )

            avail_id = int(
                sys.argv[2]
            )

        except ValueError:

            print(
                "Spot ID and Avail ID must be numbers."
            )

            return


        assign(
            spot_id,
            avail_id
        )

        return



    #
    # Interactive mode
    #

    print()
    print(
        "Assign Spot to Avail"
    )
    print(
        "===================="
    )
    print()


    try:

        spot_id = int(
            input("Spot ID: ")
        )

        avail_id = int(
            input("Avail ID: ")
        )

    except ValueError:

        print(
            "Spot ID and Avail ID must be numbers."
        )

        return



    assign(
        spot_id,
        avail_id
    )



if __name__ == "__main__":

    main()
