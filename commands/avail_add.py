#!/usr/bin/env python3

# File: commands/avail_add.py

import argparse

from traffic.avails import (
    add_avail
)


def main():

    parser = argparse.ArgumentParser(
        description="Add a commercial avail"
    )


    parser.add_argument(
        "station_id",
        type=int,
        help="Station ID"
    )


    parser.add_argument(
        "air_date",
        help="Air date YYYY-MM-DD"
    )


    parser.add_argument(
        "start_time",
        help="Avail start time HH:MM:SS"
    )


    parser.add_argument(
        "length_seconds",
        type=int,
        help="Avail length in seconds"
    )


    parser.add_argument(
        "--status",
        choices=[
            "Open",
            "Partial",
            "Filled",
            "Closed"
        ],
        help="Initial avail status"
    )


    parser.add_argument(
        "--notes",
        help="Optional notes"
    )


    args = parser.parse_args()



    avail_id = add_avail(
        station_id=args.station_id,
        air_date=args.air_date,
        start_time=args.start_time,
        length_seconds=args.length_seconds,
        status=args.status,
        notes=args.notes
    )


    print()

    print(
        "Avail created:"
    )


    print(
        f"ID: {avail_id}"
    )



if __name__ == "__main__":

    main()
