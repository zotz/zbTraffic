#!/usr/bin/env python3

# File: database/test_assignment.py
#
# Test spot assignment logic.

from traffic.assignment import (
    assign_spot_to_avail
)

from traffic.spots import (
    get_spot
)


def main():

    #
    # Change these IDs to match
    # records in your test database.
    #

    spot_id = 154

    avail_id = 6



    print(
        "Assigning spot..."
    )


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
                error
            )

        return



    print(
        "Assignment successful."
    )



    #
    # Verify the result
    #

    spot = get_spot(
        spot_id
    )


    print()

    print(
        "Updated spot:"
    )


    print(
        f"ID: {spot['id']}"
    )

    print(
        f"Status: {spot['status']}"
    )

    print(
        f"Avail ID: {spot['avail_id']}"
    )

    print(
        f"Air Date: {spot['air_date']}"
    )

    print(
        f"Air Time: {spot['air_time']}"
    )



if __name__ == "__main__":

    main()
