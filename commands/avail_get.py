#!/usr/bin/env python3

# File: commands/avail_get.py

import argparse

from traffic.avails import (
    get_avail,
    format_avail
)



def main():

    parser = argparse.ArgumentParser(
        description="Get an avail"
    )


    parser.add_argument(
        "avail_id",
        type=int,
        help="Avail ID"
    )


    args = parser.parse_args()



    avail = get_avail(
        args.avail_id
    )


    if not avail:

        print(
            "Avail not found."
        )

        return



    print(
        format_avail(
            avail
        )
    )



if __name__ == "__main__":

    main()
