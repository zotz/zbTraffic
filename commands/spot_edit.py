#!/usr/bin/env python3

# File: commands/spot_edit.py

import argparse

from traffic.spots import (
    update_spot,
    get_spot,
    format_spot
)


def main():

    parser = argparse.ArgumentParser(
        description="Edit spot"
    )


    parser.add_argument(
        "id",
        type=int,
        help="Spot ID"
    )


    parser.add_argument(
        "--date",
        dest="air_date",
        help="Air date YYYY-MM-DD"
    )


    parser.add_argument(
        "--time",
        dest="air_time",
        help="Air time HH:MM:SS"
    )


    parser.add_argument(
        "--status",
        help="New status"
    )


    parser.add_argument(
        "--notes",
        help="Notes"
    )


    args = parser.parse_args()


    changed = update_spot(
        args.id,
        air_date=args.air_date,
        air_time=args.air_time,
        status=args.status,
        notes=args.notes
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
