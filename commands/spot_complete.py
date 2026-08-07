#!/usr/bin/env python3

# File: commands/spot_complete.py

import argparse

from traffic.spots import (
    complete_spot,
    get_spot,
    format_spot
)


def main():

    parser = argparse.ArgumentParser(
        description="Complete spot"
    )


    parser.add_argument(
        "id",
        type=int,
        help="Spot ID"
    )


    parser.add_argument(
        "--time",
        dest="actual_air_time",
        help="Actual air time"
    )


    args = parser.parse_args()


    changed = complete_spot(
        args.id,
        actual_air_time=args.actual_air_time
    )


    if changed == 0:

        print(
            "No spot updated."
        )

        return


    spot = get_spot(
        args.id
    )


    print(
        format_spot(spot)
    )


if __name__ == "__main__":

    main()
