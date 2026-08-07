#!/usr/bin/env python3

# File: commands/stopset_get.py

import sys

from traffic.database import get_connection


def get_stopset_details(stopset_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT

            stopsets.id,
            stopsets.name,
            stopsets.start_time,
            stopsets.end_time,
            stopsets.maximum_seconds,
            stopsets.active,
            stopsets.created_date,
            stopsets.modified_date,

            programs.id AS program_id,
            programs.name AS program_name,
            programs.start_time AS program_start_time,
            programs.end_time AS program_end_time

        FROM stopsets

        JOIN programs
            ON stopsets.program_id = programs.id

        WHERE stopsets.id = ?

        """,
        (
            stopset_id,
        )
    )


    stopset = cursor.fetchone()

    connection.close()


    return stopset



def main():

    #
    # Command line mode
    #
    # Example:
    # python3 -m commands.stopset_get 2
    #

    if len(sys.argv) == 2:

        try:

            stopset_id = int(
                sys.argv[1]
            )

        except ValueError:

            print(
                "Stopset ID must be a number."
            )

            return



    #
    # Interactive mode
    #

    else:

        try:

            stopset_id = int(
                input("Stopset ID: ")
            )

        except ValueError:

            print(
                "Stopset ID must be a number."
            )

            return



    stopset = get_stopset_details(
        stopset_id
    )


    if stopset is None:

        print()

        print(
            "Stopset not found."
        )

        return



    print()

    print(
        "Stopset Details"
    )

    print(
        "==============="
    )

    print()


    print(
        f"ID: {stopset['id']}"
    )

    print(
        f"Program ID: {stopset['program_id']}"
    )

    print(
        f"Program Name: {stopset['program_name']}"
    )

    print(
        f"Program Time: "
        f"{stopset['program_start_time'] or ''}"
        f" - "
        f"{stopset['program_end_time'] or ''}"
    )

    print()

    print(
        f"Stopset Name: {stopset['name']}"
    )

    print(
        f"Start Time: {stopset['start_time'] or ''}"
    )

    print(
        f"End Time: {stopset['end_time'] or ''}"
    )

    print(
        f"Maximum Seconds: "
        f"{stopset['maximum_seconds'] or ''}"
    )

    print(
        f"Active: {stopset['active']}"
    )

    print()

    print(
        f"Created: {stopset['created_date']}"
    )

    print(
        f"Modified: {stopset['modified_date']}"
    )



if __name__ == "__main__":

    main()
