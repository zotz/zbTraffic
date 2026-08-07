#!/usr/bin/env python3

# File: commands/export_rivendell_log.py

import argparse
import os

from traffic.rivendell import (
    export_rivendell_log
)


def main():

    parser = argparse.ArgumentParser(
        description="Export scheduled spots to a Rivendell traffic log"
    )


    parser.add_argument(
        "date",
        help="Air date YYYY-MM-DD"
    )


    parser.add_argument(
        "--output",
        "-o",
        help="Output filename"
    )


    args = parser.parse_args()


    if args.output:

        filename = args.output

    else:

        os.makedirs(
            "logs",
            exist_ok=True
        )

        filename = os.path.join(
            "logs",
            f"zbt_{args.date.replace('-', '')}.log"
        )


    count = export_rivendell_log(
        args.date,
        filename
    )


    print(
        f"Exported {count} spot(s)"
    )


    print(
        f"File: {filename}"
    )


if __name__ == "__main__":

    main()
