#!/usr/bin/env python3

# File: commands/spot_cancel.py

import argparse

from traffic.spots import (
    cancel_spot,
    get_spot,
    format_spot
)


def main():

    parser = argparse.ArgumentParser(
        description="Cancel spot"
    )


    parser.add_argument(
        "id",
        type=int,
        help="Spot ID"
    )


    args = parser.parse_args()


    changed = cancel_spot(
        args.id
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
