# File: commands/contract_item_get.py

import sys

from traffic.contract_items import get_contract_item



def main():

    if len(sys.argv) < 2:

        print(
            "\nUsage: python -m commands.contract_item_get <contract_item_id>\n"
        )

        return


    contract_item_id = int(
        sys.argv[1]
    )


    contract_item = get_contract_item(
        contract_item_id
    )


    if contract_item is None:

        print(
            f"\nContract item ID {contract_item_id} not found.\n"
        )

        return



    print("\nContract Item")
    print("-------------\n")


    print(
        f"ID: {contract_item['id']}"
    )

    print(
        f"Contract ID: {contract_item['contract_id']}"
    )

    print(
        f"Commercial ID: {contract_item['commercial_id']}"
    )

    print(
        f"Commercial Title: {contract_item['commercial_title']}"
    )

    print(
        f"Description: {contract_item['description']}"
    )

    print(
        f"Quantity: {contract_item['quantity']}"
    )

    print(
        f"Spot Length: {contract_item['spot_length_seconds']} seconds"
    )

    print(
        f"Start Date: {contract_item['start_date']}"
    )

    print(
        f"End Date: {contract_item['end_date']}"
    )

    print(
        f"Priority: {contract_item['priority']}"
    )

    print(
        f"Rotation Group: {contract_item['rotation_group']}"
    )

    print(
        f"Notes: {contract_item['notes']}"
    )

    print(
        f"Active: {contract_item['active']}"
    )

    print(
        f"Created Date: {contract_item['created_date']}"
    )

    print(
        f"Modified Date: {contract_item['modified_date']}"
    )



if __name__ == "__main__":

    main()
