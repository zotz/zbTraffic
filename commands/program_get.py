#!/usr/bin/env python3

# File: commands/program_get.py

import sys

from traffic.programs import get_program


def main():

    #
    # Command line mode
    #
    # Example:
    # python3 -m commands.program_get 5
    #

    if len(sys.argv) == 2:

        try:

            program_id = int(
                sys.argv[1]
            )

        except ValueError:

            print(
                "Program ID must be a number."
            )

            return


    #
    # Interactive mode
    #

    else:

        try:

            program_id = int(
                input("Program ID: ")
            )

        except ValueError:

            print(
                "Program ID must be a number."
            )

            return



    program = get_program(
        program_id
    )


    if program is None:

        print()

        print(
            "Program not found."
        )

        return



    print()

    print(
        "Program Details"
    )

    print(
        "==============="
    )

    print()

    print(
        f"ID: {program['id']}"
    )

    print(
        f"Station ID: {program['station_id']}"
    )

    print(
        f"Name: {program['name']}"
    )

    print(
        f"Description: {program['description'] or ''}"
    )

    print(
        f"Start Time: {program['start_time'] or ''}"
    )

    print(
        f"End Time: {program['end_time'] or ''}"
    )

    print(
        f"Active: {program['active']}"
    )

    print(
        f"Created: {program['created_date']}"
    )

    print(
        f"Modified: {program['modified_date']}"
    )



if __name__ == "__main__":

    main()
