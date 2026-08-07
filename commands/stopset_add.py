#!/usr/bin/env python3

# File: commands/stopset_add.py

from traffic.stopsets import add_stopset


def main():

    print()

    print(
        "Add Stopset"
    )

    print(
        "==========="
    )

    print()


    try:

        program_id = int(
            input("Program ID: ")
        )

    except ValueError:

        print(
            "Program ID must be a number."
        )

        return



    name = input(
        "Stopset Name: "
    ).strip()


    if not name:

        print(
            "Stopset name is required."
        )

        return



    start_time = input(
        "Start Time (HH:MM): "
    ).strip()


    end_time = input(
        "End Time (HH:MM): "
    ).strip()



    try:

        maximum_seconds = int(
            input("Maximum Seconds: ")
        )

    except ValueError:

        print(
            "Maximum seconds must be a number."
        )

        return



    stopset_id = add_stopset(
        program_id,
        name,
        start_time,
        end_time,
        maximum_seconds
    )


    print()

    print(
        f"Stopset added successfully. ID: {stopset_id}"
    )



if __name__ == "__main__":

    main()
