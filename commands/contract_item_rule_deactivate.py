# File: commands/contract_item_rule_deactivate.py

import sys

from traffic.contract_item_rules import (
    deactivate_contract_item_rule
)



def main():

    if len(sys.argv) < 2:

        print(
            "\nUsage: python -m commands.contract_item_rule_deactivate <rule_id>\n"
        )

        return


    rule_id = int(
        sys.argv[1]
    )


    try:

        deactivate_contract_item_rule(
            rule_id
        )


        print()

        print(
            f"Contract item rule {rule_id} deactivated successfully."
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
