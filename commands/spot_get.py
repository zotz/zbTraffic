#!/usr/bin/env python3

# File: commands/spot_get.py

import argparse

from traffic.spots import (
    get_spot,
    format_spot
)


def main():

    parser = argparse.ArgumentParser(
        description="Get spot"
    )

    parser.add_argument(
        "id",
        type=int,
        help="Spot ID"
    )


    args = parser.parse_args()


    spot = get_spot(
        args.id
    )


    if not spot:

        print(
            "Spot not found."
        )

        return


    print(
        format_spot(spot)
    )


if __name__ == "__main__":

    main()
