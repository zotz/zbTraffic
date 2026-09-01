# File: commands/contract_item_rule_get.py

import sys

from traffic.contract_item_rules import (
    get_contract_item_rule
)



def main():

    if len(sys.argv) < 2:

        print(
            "\nUsage: python -m commands.contract_item_rule_get <rule_id>\n"
        )

        return


    rule_id = int(
        sys.argv[1]
    )


    rule = get_contract_item_rule(
        rule_id
    )


    if rule is None:

        print()

        print(
            f"No contract item rule found with ID {rule_id}."
        )

        print()

        return


    print()

    print(
        "Contract Item Rule"
    )

    print(
        "------------------"
    )

    print()

    print(
        f"ID: {rule['id']}"
    )

    print(
        f"Contract Item ID: {rule['contract_item_id']}"
    )

    print(
        f"Days of Week: {rule['days_of_week']}"
    )

    print(
        f"Start Time: {rule['start_time']}"
    )

    print(
        f"End Time: {rule['end_time']}"
    )

    print(
        f"Preferred Program ID: {rule['preferred_program_id']}"
    )

    print(
        f"Preferred Stopset ID: {rule['preferred_stopset_id']}"
    )

    print(
        f"Spots Per Day: {rule['max_spots_per_day']}"
    )

    print(
        f"Spots Per Week: {rule['max_spots_per_week']}"
    )

    print(
        f"Allow News: {rule['allow_news']}"
    )

    print(
        f"Allow Special Events: {rule['allow_special_events']}"
    )

    print(
        f"Active: {rule['active']}"
    )

    print(
        f"Notes: {rule['notes']}"
    )

    print(
        f"Created Date: {rule['created_date']}"
    )

    print(
        f"Modified Date: {rule['modified_date']}"
    )

    print()



if __name__ == "__main__":

    main()
