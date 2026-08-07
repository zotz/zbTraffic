# File: commands/contract_item_list.py

import sys

from traffic.contract_items import list_contract_items



def main():

    active_only = True

    contract_id = None


    #
    # Command line arguments
    #

    args = sys.argv[1:]


    if "--all" in args:

        active_only = False

        args.remove("--all")


    if len(args) > 0:

        contract_id = int(args[0])



    contract_items = list_contract_items(

        contract_id=contract_id,

        active_only=active_only

    )


    if not contract_items:

        print("\nNo contract items found.\n")

        return



    print("\nContract Items")
    print("--------------\n")


    print(
        f"{'ID':<5}"
        f"{'Contract':<10}"
        f"{'Commercial':<12}"
        f"{'Title':<35}"
        f"{'Qty':<8}"
        f"{'Length':<10}"
        f"{'Status':<10}"
    )


    print("-" * 90)



    for item in contract_items:


        if item["commercial_id"] is None:

            commercial_display = "-"

        else:

            commercial_display = str(
                item["commercial_id"]
            )


        if item["active"]:

            status = "Active"

        else:

            status = "Inactive"



        print(

            f"{item['id']:<5}"

            f"{item['contract_id']:<10}"

            f"{commercial_display:<12}"

            f"{item['commercial_title']:<35}"

            f"{item['quantity']:<8}"

            f"{str(item['spot_length_seconds']) + ' sec':<10}"

            f"{status:<10}"

        )



if __name__ == "__main__":

    main()
