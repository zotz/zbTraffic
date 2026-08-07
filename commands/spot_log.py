#!/usr/bin/env python3

# File: commands/spot_log.py

import argparse

from traffic.spots import (
    list_spots_by_date
)


def main():

    parser = argparse.ArgumentParser(
        description="Display spots for a date"
    )


    parser.add_argument(
        "date",
        help="Air date YYYY-MM-DD"
    )


    args = parser.parse_args()


    spots = list_spots_by_date(
        args.date
    )


    print()

    print(
        "Traffic Log:",
        args.date
    )

    print(
        "-" * 70
    )


    if not spots:

        print(
            "No spots found."
        )

        return


    for spot in spots:

        print(
            f"{spot['air_time']}  "
            f"{spot['cart_number']}  "
            f"{spot['title']}  "
            f"{spot['length_seconds']:>3}s  "
            f"{spot['status']}"
        )


if __name__ == "__main__":

    main()
