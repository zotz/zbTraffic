#!/usr/bin/env python3

import argparse

from traffic.commercials import (
    get_commercial,
    format_commercial
)


def main():

    parser = argparse.ArgumentParser(
        description="Get commercial details"
    )

    parser.add_argument(
        "commercial_id",
        type=int,
        help="Commercial ID"
    )


    args = parser.parse_args()


    commercial = get_commercial(
        args.commercial_id
    )


    if commercial is None:

        print()
        print(
            "Commercial not found."
        )
        return


    print()

    print(
        format_commercial(
            commercial
        )
    )


if __name__ == "__main__":

    main()
