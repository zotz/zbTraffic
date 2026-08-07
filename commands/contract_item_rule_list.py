# File: commands/contract_item_rule_list.py

import sys

from traffic.contract_item_rules import (
    list_contract_item_rules
)



def main():

    active_only = True

    contract_item_id = None


    args = sys.argv[1:]


    if "--all" in args:

        active_only = False

        args.remove(
            "--all"
        )


    if len(args) > 0:

        contract_item_id = int(
            args[0]
        )


    rules = list_contract_item_rules(
        contract_item_id,
        active_only
    )


    if not rules:

        print()

        print(
            "No contract item rules found."
        )

        print()

        return


    print()

    print(
        "Contract Item Rules"
    )

    print(
        "-------------------"
    )

    print()


    print(
        f"{'ID':<5}"
        f"{'Item':<8}"
        f"{'Days':<25}"
        f"{'Start':<8}"
        f"{'End':<8}"
        f"{'Prog':<7}"
        f"{'Stop':<7}"
        f"{'Per Day':<9}"
        f"{'Per Week':<10}"
        f"{'Status':<10}"
    )


    print(
        "-" * 97
    )


    for rule in rules:

        status = (
            "Active"
            if rule["active"] == 1
            else "Inactive"
        )


        print(

            f"{rule['id']:<5}"
            f"{rule['contract_item_id']:<8}"
            f"{(rule['days_of_week'] or '')[:24]:<25}"
            f"{(rule['start_time'] or ''):<8}"
            f"{(rule['end_time'] or ''):<8}"
            f"{str(rule['preferred_program_id'] or '-'): <7}"
            f"{str(rule['preferred_stopset_id'] or '-'): <7}"
            f"{rule['spots_per_day']:<9}"
            f"{rule['spots_per_week']:<10}"
            f"{status:<10}"

        )


    print()



if __name__ == "__main__":

    main()
