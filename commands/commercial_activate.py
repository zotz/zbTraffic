#!/usr/bin/env python3

import argparse

from traffic.commercials import (
    activate_commercial
)


def main():

    parser = argparse.ArgumentParser(
        description="Activate a commercial"
    )


    parser.add_argument(
        "commercial_id",
        type=int,
        help="Commercial ID"
    )


    args = parser.parse_args()


    success, errors = activate_commercial(
        args.commercial_id
    )


    if success:

        print()
        print(
            "Commercial activated successfully."
        )


    else:

        print()
        print(
            "Activation failed:"
        )

        for error in errors:

            print(
                "-",
                error
            )


if __name__ == "__main__":

    main()
