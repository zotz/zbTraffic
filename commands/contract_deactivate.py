# File: commands/contract_deactivate.py

import sys

from traffic.contracts import (
    deactivate_contract
)



def main():

    if len(sys.argv) < 2:

        print(
            "\nUsage: python -m commands.contract_deactivate <contract_id>\n"
        )

        return


    contract_id = int(
        sys.argv[1]
    )


    try:

        deactivate_contract(
            contract_id
        )


        print(
            f"\nContract ID {contract_id} deactivated successfully.\n"
        )


    except ValueError as e:

        print(
            f"\nError: {e}\n"
        )



if __name__ == "__main__":

    main()
