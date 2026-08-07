#!/usr/bin/env python3

# File: commands/program_add.py

from traffic.programs import add_program


def main():

    print()
    print(
        "Add Program"
    )
    print(
        "==========="
    )
    print()


    try:

        station_id = int(
            input("Station ID: ")
        )

    except ValueError:

        print(
            "Station ID must be a number."
        )

        return



    name = input(
        "Program Name: "
    ).strip()


    if not name:

        print(
            "Program name is required."
        )

        return



    description = input(
        "Description (optional): "
    ).strip()


    start_time = input(
        "Start Time (HH:MM, optional): "
    ).strip()


    end_time = input(
        "End Time (HH:MM, optional): "
    ).strip()



    program_id = add_program(
        station_id,
        name,
        description if description else None,
        start_time if start_time else None,
        end_time if end_time else None
    )


    print()

    print(
        f"Program added successfully. ID: {program_id}"
    )



if __name__ == "__main__":

    main()
