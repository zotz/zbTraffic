#!/usr/bin/env python3

# File: commands/program_list.py

from traffic.programs import list_programs


def main():

    print()

    print(
        "Programs"
    )

    print(
        "========"
    )

    print()


    programs = list_programs()


    if not programs:

        print(
            "No programs found."
        )

        return



    print(
        f"{'ID':<5} {'Station':<8} {'Name':<25} {'Start':<8} {'End':<8} {'Active'}"
    )

    print(
        "-" * 75
    )


    for program in programs:

        print(
            f"{program['id']:<5} "
            f"{program['station_id']:<8} "
            f"{program['name']:<25} "
            f"{program['start_time'] or '':<8} "
            f"{program['end_time'] or '':<8} "
            f"{program['active']}"
        )



if __name__ == "__main__":

    main()
