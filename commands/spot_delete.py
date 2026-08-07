#!/usr/bin/env python3

# File: commands/spot_delete.py

import argparse

from traffic.spots import (
    delete_spot
)


def main():

    parser = argparse.ArgumentParser(
        description="Delete a spot"
    )

    parser.add_argument(
        "id",
        type=int,
        help="Spot ID"
    )

    args = parser.parse_args()


    result = delete_spot(
        args.id
    )


    if result == "success":

        print(
            "Spot deleted."
        )


    elif result == "not_found":

        print(
            "Spot does not exist."
        )


    elif result == "not_allowed":

        print(
            "Spot could not be deleted."
        )


    else:

        print(
            "Unexpected error deleting spot."
        )


if __name__ == "__main__":

    main()
