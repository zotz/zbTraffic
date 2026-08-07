#!/usr/bin/env python3

# File: commands/spot_duplicates.py

from traffic.spots import (
    find_duplicate_spots
)


def main():

    duplicates = find_duplicate_spots()


    if not duplicates:

        print(
            "No duplicate spots found."
        )

        return


    print(
        "Duplicate spots found:"
    )

    print()


    for duplicate in duplicates:

        print(
            f"Station {duplicate['station_id']} "
            f"Commercial {duplicate['commercial_id']} "
            f"{duplicate['air_date']} "
            f"{duplicate['air_time']} "
            f"({duplicate['duplicate_count']} records)"
        )


if __name__ == "__main__":

    main()
