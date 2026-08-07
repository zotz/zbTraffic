#!/usr/bin/env python3

# File: database/test_assignment3.py

from traffic.assignment import (
    assign_spot_to_avail
)

from traffic.spots import (
    get_spot
)


def main():

    spot_id = 156

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

        print(
            errors
        )

        return



    print(
        "Assignment successful."
    )


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
