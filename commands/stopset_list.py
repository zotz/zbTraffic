#!/usr/bin/env python3

# File: commands/stopset_list.py

from traffic.stopsets import list_stopsets


def main():

    print()

    print(
        "Stopsets"
    )

    print(
        "========"
    )

    print()


    stopsets = list_stopsets()


    if not stopsets:

        print(
            "No stopsets found."
        )

        return



    print(
        f"{'ID':<5} "
        f"{'Program':<8} "
        f"{'Name':<25} "
        f"{'Start':<8} "
        f"{'End':<8} "
        f"{'Seconds':<10} "
        f"{'Active'}"
    )


    print(
        "-" * 85
    )


    for stopset in stopsets:

        start_time = stopset["start_time"] or ""

        end_time = stopset["end_time"] or ""

        maximum_seconds = stopset["maximum_seconds"] or ""


        print(
            f"{stopset['id']:<5} "
            f"{stopset['program_id']:<8} "
            f"{stopset['name']:<25} "
            f"{start_time:<8} "
            f"{end_time:<8} "
            f"{maximum_seconds:<10} "
            f"{stopset['active']}"
        )



if __name__ == "__main__":

    main()
