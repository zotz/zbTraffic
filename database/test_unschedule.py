#!/usr/bin/env python3

# File: database/test_unschedule.py


from traffic.assignment import (
    remove_spot_from_avail
)

from traffic.spots import (
    get_spot
)


def main():

    spot_id = 156


    print(
        "Removing spot from avail..."
    )


    success, errors = remove_spot_from_avail(
        spot_id
    )


    if not success:

        print(
            "Unschedule failed:"
        )

        print(
            errors
        )

        return



    print(
        "Unschedule successful."
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
