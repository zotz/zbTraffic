#!/usr/bin/env python3

# File: 
#
# Development/test database seed.
#
# Requires:
#   seed_database.py has already been run.
#
# Uses:
#   seed_common.py

import argparse
from datetime import date

from database.seed_common import (
    check_prerequisites,
    get_first_station_id,
    get_seed_rotation,
)


def seed_pending_spots(
    station_id,
    seed_date,
    spot_status
):

    from traffic.spots import (
        add_spot
    )


    print(
        "Creating pending spots..."
    )


    spots = []


    rotation = get_seed_rotation()


    for hour in range(
        6,
        23
    ):

        for minute in (
            15,
            30,
            45
        ):

            current_seconds = (
                hour * 3600
                + minute * 60
            )


            for commercial in rotation:

                air_hour = current_seconds // 3600

                air_minute = (
                    current_seconds % 3600
                ) // 60

                air_second = (
                    current_seconds % 60
                )


                air_time = (
                    f"{air_hour:02d}:"
                    f"{air_minute:02d}:"
                    f"{air_second:02d}"
                )


                spot_id = add_spot(
                    station_id,
                    commercial["id"],
                    None,
                    None,
                    status=spot_status
                )


                spots.append(
                    spot_id
                )


                current_seconds += (
                    commercial["length_seconds"]
                )


    print(
        f"Created {len(spots)} pending spots."
    )


    return spots



def seed_sched_spots(
    station_id,
    seed_date,
    spot_status
):

    from traffic.spots import (
        add_spot
    )


    print(
        "Creating scheduled spots..."
    )


    spots = []


    rotation = get_seed_rotation()


    for hour in range(
        6,
        23
    ):

        for minute in (
            15,
            30,
            45
        ):

            current_seconds = (
                hour * 3600
                + minute * 60
            )


            for commercial in rotation:

                air_hour = current_seconds // 3600

                air_minute = (
                    current_seconds % 3600
                ) // 60

                air_second = (
                    current_seconds % 60
                )


                air_time = (
                    f"{air_hour:02d}:"
                    f"{air_minute:02d}:"
                    f"{air_second:02d}"
                )


                spot_id = add_spot(
                    station_id,
                    commercial["id"],
                    seed_date,
                    air_time,
                    status=spot_status
                )


                spots.append(
                    spot_id
                )


                current_seconds += (
                    commercial["length_seconds"]
                )


    print(
        f"Created {len(spots)} scheduled spots."
    )


    return spots





def main():

    parser = argparse.ArgumentParser(
        description="Seed zbTraffic test database"
    )

    parser.add_argument(
        "--date",
        help="Air date YYYY-MM-DD (default: today)"
    )


    parser.add_argument(
        "--spot-status",
        choices=[
            "Pending",
            "Scheduled"
        ],
        default="Scheduled",
        help="Initial status for seeded spots"
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

    if args.spot_status == "Pending":

        pending_spots = seed_pending_spots(
            station_id,
            seed_date,
            args.spot_status
        )
    else:

        spots = seed_sched_spots(
            station_id,
            seed_date,
            args.spot_status
        )





    print(
        "Seed spots database complete."
    )


if __name__ == "__main__":

    main()
