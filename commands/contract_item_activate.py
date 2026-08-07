# File: commands/contract_item_activate.py

import sys

from traffic.contract_items import (
    activate_contract_item
)



def main():

    if len(sys.argv) < 2:

        print(
            "\nUsage: python -m commands.contract_item_activate <contract_item_id>\n"
        )

        return


    contract_item_id = int(
        sys.argv[1]
    )


    try:

        activate_contract_item(
            contract_item_id
        )


        print(
            f"\nContract item ID {contract_item_id} activated successfully.\n"
        )


    except ValueError as e:

        print(
            f"\nError: {e}\n"
        )



if __name__ == "__main__":

    main()
