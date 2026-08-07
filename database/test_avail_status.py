#!/usr/bin/env python3

from traffic.avails import (
    update_avail_status,
    get_avail
)


def main():

    avail_id = 6


    print("Before update:")

    avail = get_avail(
        avail_id
    )

    if avail:

        print(
            f"Avail {avail_id} status: {avail['status']}"
        )


    print()

    print("Updating status...")


    result = update_avail_status(
        avail_id
    )


    print(
        f"New status: {result}"
    )


    print()

    print("After update:")


    avail = get_avail(
        avail_id
    )


    if avail:

        print(
            f"Avail {avail_id} status: {avail['status']}"
        )



if __name__ == "__main__":

    main()
