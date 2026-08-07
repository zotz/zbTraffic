#!/usr/bin/env python3

# File: commands/avail_generate.py

import sys

from traffic.avails import (
    generate_avails_for_date
)


def generate(
    station_id,
    air_date
):

    created = generate_avails_for_date(
        station_id,
        air_date
    )


    print()

    print(
        f"Created {created} avail(s)."
    )


def main():

    #
    # Command line mode
    #
    # Example:
    # python3 -m commands.avail_generate 1 2026-08-05
    #

    if len(sys.argv) == 3:

        try:

            station_id = int(
                sys.argv[1]
            )

        except ValueError:

            print(
                "Station ID must be a number."
            )

            return


        air_date = sys.argv[2]

        generate(
            station_id,
            air_date
        )

        return


    #
    # Interactive mode
    #

    print()

    print(
        "Generate Avails"
    )

    print(
        "==============="
    )

    print()


    try:

        station_id = int(
            input("Station ID: ")
        )

    except ValueError:

        print(
            "Station ID must be a number."
        )

        return


    air_date = input(
        "Air Date (YYYY-MM-DD): "
    ).strip()


    generate(
        station_id,
        air_date
    )


if __name__ == "__main__":

    main()
