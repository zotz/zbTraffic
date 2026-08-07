#!/usr/bin/env python3

import argparse

from traffic.commercials import (
    deactivate_commercial
)


def main():

    parser = argparse.ArgumentParser(
        description="Deactivate a commercial"
    )


    parser.add_argument(
        "commercial_id",
        type=int,
        help="Commercial ID"
    )


    args = parser.parse_args()


    success, errors = deactivate_commercial(
        args.commercial_id
    )


    if success:

        print()
        print(
            "Commercial deactivated successfully."
        )


    else:

        print()
        print(
            "Deactivation failed:"
        )

        for error in errors:

            print(
                "-",
                error
            )


if __name__ == "__main__":

    main()
