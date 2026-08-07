#!/usr/bin/env python3

# File: database/seed_avails_database.py
#
# Development/test seed for avails.
#
# Requires:
#   seed_database.py has already been run.
#

import argparse

from datetime import date

from database.seed_common import (
    check_prerequisites,
    get_first_station_id,
)


def seed_avails(
    station_id,
    seed_date
):

    from traffic.avails import (
        add_avail
    )


    print(
        "Creating avails..."
    )


    avails = []


    #
    # Test break pattern
    #
    # Times represent the beginning of the avail.
    #
    # Length is the available commercial time.
    #

    breaks = {

        "06:15:00": 180,
        "06:30:00": 180,
        "06:45:00": 180,

        "07:15:00": 120,
        "07:30:00": 180,
        "07:45:00": 120,

        "08:15:00": 180,
        "08:30:00": 180,
        "08:45:00": 180,

        "09:15:00": 120,
        "09:30:00": 180,
        "09:45:00": 120,

        "10:15:00": 180,
        "10:45:00": 180,

        "12:15:00": 180,
        "12:45:00": 180,

        "15:15:00": 180,
        "15:45:00": 180,

        "18:15:00": 180,
        "18:45:00": 180,

        "21:15:00": 120,
        "21:45:00": 120,
    }



    for start_time, length_seconds in breaks.items():


        avail_id = add_avail(
            station_id,
            seed_date,
            start_time,
            length_seconds
        )


        avails.append(
            avail_id
        )



    print(
        f"Created {len(avails)} avails."
    )


    return avails



def main():

    parser = argparse.ArgumentParser(
        description="Seed test avails"
    )


    parser.add_argument(
        "--date",
        help="Air date YYYY-MM-DD (default: today)"
    )


    args = parser.parse_args()



    if args.date:

        seed_date = args.date

    else:

        seed_date = date.today().isoformat()



    print(
        "Checking prerequisites..."
    )


    check_prerequisites(
        [
            "stations",
            "categories",
            "customers",
            "commercials"
        ]
    )


    print(
        "Prerequisites OK."
    )



    station_id = get_first_station_id()


    if station_id is None:

        raise RuntimeError(
            "No station found."
        )



    seed_avails(
        station_id,
        seed_date
    )



    print(
        "Avail seed complete."
    )



if __name__ == "__main__":

    main()
