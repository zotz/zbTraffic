# File: commands/contract_item_rule_edit.py

import argparse

from traffic.contract_item_rules import (
    get_contract_item_rule,
    update_contract_item_rule
)



def prompt_value(
    label,
    current
):

    value = input(
        f"{label} [{current}]: "
    )


    if value == "":

        return current


    return value



def main():

    parser = argparse.ArgumentParser(
        description="Edit a contract item rule"
    )


    parser.add_argument(
        "rule_id",
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
        "--spots-per-day",
        type=int
    )

    parser.add_argument(
        "--spots-per-week",
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


    rule = get_contract_item_rule(
        args.rule_id
    )


    if rule is None:

        print()

        print(
            f"No contract item rule found with ID {args.rule_id}"
        )

        print()

        return



    interactive = all(
        value is None
        for key, value in vars(args).items()
        if key != "rule_id"
    )



    if interactive:

        print()

        print(
            "Edit Contract Item Rule"
        )

        print(
            "----------------------"
        )

        print()


        days_of_week = prompt_value(
            "Days of Week",
            rule["days_of_week"] or ""
        )


        start_time = prompt_value(
            "Start Time",
            rule["start_time"] or ""
        )


        end_time = prompt_value(
            "End Time",
            rule["end_time"] or ""
        )


        preferred_program_id = prompt_value(
            "Preferred Program ID",
            rule["preferred_program_id"] or ""
        )


        if preferred_program_id == "":

            preferred_program_id = None

        else:

            preferred_program_id = int(
                preferred_program_id
            )



        preferred_stopset_id = prompt_value(
            "Preferred Stopset ID",
            rule["preferred_stopset_id"] or ""
        )


        if preferred_stopset_id == "":

            preferred_stopset_id = None

        else:

            preferred_stopset_id = int(
                preferred_stopset_id
            )



        max_spots_per_day = int(
            prompt_value(
                "Spots Per Day",
                rule["max_spots_per_day"]
            )
        )


        max_spots_per_week = int(
            prompt_value(
                "Spots Per Week",
                rule["max_spots_per_week"]
            )
        )


        allow_news = int(
            prompt_value(
                "Allow News",
                rule["allow_news"]
            )
        )


        allow_special_events = int(
            prompt_value(
                "Allow Special Events",
                rule["allow_special_events"]
            )
        )


        notes = prompt_value(
            "Notes",
            rule["notes"] or ""
        )



    else:

        days_of_week = (
            args.days
            if args.days is not None
            else rule["days_of_week"]
        )


        start_time = (
            args.start
            if args.start is not None
            else rule["start_time"]
        )


        end_time = (
            args.end
            if args.end is not None
            else rule["end_time"]
        )


        preferred_program_id = (
            args.program
            if args.program is not None
            else rule["preferred_program_id"]
        )


        preferred_stopset_id = (
            args.stopset
            if args.stopset is not None
            else rule["preferred_stopset_id"]
        )


        max_spots_per_day = (
            args.max_spots_per_day
            if args.max_spots_per_day is not None
            else rule["max_spots_per_day"]
        )


        max_spots_per_week = (
            args.max_spots_per_week
            if args.max_spots_per_week is not None
            else rule["max_spots_per_week"]
        )


        allow_news = (
            args.allow_news
            if args.allow_news is not None
            else rule["allow_news"]
        )


        allow_special_events = (
            args.allow_special_events
            if args.allow_special_events is not None
            else rule["allow_special_events"]
        )


        notes = (
            args.notes
            if args.notes is not None
            else rule["notes"]
        )



    try:

        update_contract_item_rule(
            args.rule_id,

            days_of_week,

            start_time,

            end_time,

            preferred_program_id,

            preferred_stopset_id,

            max_spots_per_day,

            max_spots_per_week,

            allow_news,

            allow_special_events,

            notes
        )


        print()

        print(
            f"Contract item rule {args.rule_id} updated successfully."
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
