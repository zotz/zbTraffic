# File: commands/contract_item_rule_add.py

import argparse

from traffic.contract_item_rules import (
    add_contract_item_rule
)



def get_input(
    prompt,
    default=None
):

    if default is not None:

        value = input(
            f"{prompt} [{default}]: "
        )

        if value == "":

            return default

        return value


    return input(
        f"{prompt}: "
    )



def main():


    parser = argparse.ArgumentParser(
        description="Add a contract item rule"
    )


    parser.add_argument(
        "--contract-item",
        type=int
    )

    parser.add_argument(
        "--days"
    )

    parser.add_argument(
        "--start"
    )

    parser.add_argument(
        "--end"
    )

    parser.add_argument(
        "--program",
        type=int
    )

    parser.add_argument(
        "--stopset",
        type=int
    )

    parser.add_argument(
        "--min-spots-per-day",
        type=int
    )

    parser.add_argument(
        "--max-spots-per-day",
        type=int
    )

    parser.add_argument(
        "--min-spots-per-week",
        type=int
    )

    parser.add_argument(
        "--max-spots-per-week",
        type=int
    )

    parser.add_argument(
        "--allow-news",
        type=int
    )

    parser.add_argument(
        "--allow-special-events",
        type=int
    )

    parser.add_argument(
        "--notes"
    )


    args = parser.parse_args()


    interactive = (
        args.contract_item is None
    )


    if interactive:

        print()
        print(
            "Add New Contract Item Rule"
        )
        print(
            "-------------------------"
        )
        print()


        contract_item_id = int(
            get_input(
                "Contract Item ID"
            )
        )


        days_of_week = get_input(
            "Days of Week"
        )


        start_time = get_input(
            "Start Time"
        )


        end_time = get_input(
            "End Time"
        )


        preferred_program_id = get_input(
            "Preferred Program ID"
        )

        if preferred_program_id == "":

            preferred_program_id = None

        else:

            preferred_program_id = int(
                preferred_program_id
            )


        preferred_stopset_id = get_input(
            "Preferred Stopset ID"
        )

        if preferred_stopset_id == "":

            preferred_stopset_id = None

        else:

            preferred_stopset_id = int(
                preferred_stopset_id
            )


        min_spots_per_day = get_input(
            "Min Spots Per Day"
        )

        if min_spots_per_day == "":
            min_spots_per_day = None
        else:
            min_spots_per_day = int(
                min_spots_per_day
            )


        max_spots_per_day = get_input(
            "Max Spots Per Day"
        )

        if max_spots_per_day == "":
            max_spots_per_day = None
        else:
            max_spots_per_day = int(
                max_spots_per_day
            )


        min_spots_per_week = get_input(
            "Min Spots Per Week"
        )

        if min_spots_per_week == "":
            min_spots_per_week = None
        else:
            min_spots_per_week = int(
                min_spots_per_week
            )


        max_spots_per_week = get_input(
            "Max Spots Per Week"
        )

        if max_spots_per_week == "":
            max_spots_per_week = None
        else:
            max_spots_per_week = int(
                max_spots_per_week
            )


        allow_news = int(
            get_input(
                "Allow News",
                1
            )
        )


        allow_special_events = int(
            get_input(
                "Allow Special Events",
                1
            )
        )


        notes = get_input(
            "Notes"
        )


    else:

        contract_item_id = args.contract_item

        days_of_week = args.days or ""

        start_time = args.start

        end_time = args.end

        preferred_program_id = args.program

        preferred_stopset_id = args.stopset

        min_spots_per_day = args.min_spots_per_day

        max_spots_per_day = args.max_spots_per_day

        min_spots_per_week = args.min_spots_per_week

        max_spots_per_week = args.max_spots_per_week

        allow_news = (
            args.allow_news
            if args.allow_news is not None
            else 1
        )

        allow_special_events = (
            args.allow_special_events
            if args.allow_special_events is not None
            else 1
        )

        notes = args.notes or ""



    try:

        rule_id = add_contract_item_rule(
            contract_item_id,

            days_of_week,

            start_time,

            end_time,

            preferred_program_id,

            preferred_stopset_id,

            min_spots_per_day,

            max_spots_per_day,

            min_spots_per_week,

            max_spots_per_week,

            allow_news,

            allow_special_events,

            notes
        )


        print()

        print(
            f"Contract item rule added successfully. ID: {rule_id}"
        )

        print()


    except ValueError as e:

        print()

        print(
            f"Error: {e}"
        )

        print()



if __name__ == "__main__":

    main()
