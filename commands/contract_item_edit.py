# File: commands/contract_item_edit.py

import sys

from traffic.contract_items import (
    get_contract_item,
    update_commercial_id,
    update_commercial_title,
    update_description,
    update_quantity,
    update_spot_length_seconds,
    update_dates,
    update_priority,
    update_rotation_group,
    update_notes
)



def display_contract_item(
    item
):

    print("\nCurrent Contract Item")
    print("---------------------\n")

    print(f"ID: {item['id']}")
    print(f"Contract ID: {item['contract_id']}")
    print(f"Commercial ID: {item['commercial_id']}")
    print(f"Commercial Title: {item['commercial_title']}")
    print(f"Description: {item['description']}")
    print(f"Quantity: {item['quantity']}")
    print(f"Spot Length: {item['spot_length_seconds']}")
    print(f"Start Date: {item['start_date']}")
    print(f"End Date: {item['end_date']}")
    print(f"Priority: {item['priority']}")
    print(f"Rotation Group: {item['rotation_group']}")
    print(f"Notes: {item['notes']}")
    print()



def main():

    if len(sys.argv) < 2:

        print(
            "\nUsage: python -m commands.contract_item_edit <contract_item_id>\n"
        )

        return


    contract_item_id = int(
        sys.argv[1]
    )


    item = get_contract_item(
        contract_item_id
    )


    if item is None:

        print(
            f"\nContract item ID {contract_item_id} not found.\n"
        )

        return



    while True:

        item = get_contract_item(
            contract_item_id
        )


        display_contract_item(
            item
        )


        print(
            "Edit Options"
        )
        print(
            "-------------"
        )

        print(
            "1. Commercial ID"
        )

        print(
            "2. Commercial Title"
        )

        print(
            "3. Description"
        )

        print(
            "4. Quantity"
        )

        print(
            "5. Spot Length Seconds"
        )

        print(
            "6. Start/End Dates"
        )

        print(
            "7. Priority"
        )

        print(
            "8. Rotation Group"
        )

        print(
            "9. Notes"
        )

        print(
            "0. Exit"
        )


        choice = input(
            "\nSelect option: "
        ).strip()



        try:

            if choice == "1":

                value = input(
                    "Commercial ID (blank removes assignment): "
                ).strip()


                if value == "":
                    value = None

                else:
                    value = int(value)


                update_commercial_id(
                    contract_item_id,
                    value
                )



            elif choice == "2":

                value = input(
                    "Commercial Title: "
                )

                update_commercial_title(
                    contract_item_id,
                    value
                )



            elif choice == "3":

                value = input(
                    "Description: "
                )

                update_description(
                    contract_item_id,
                    value
                )



            elif choice == "4":

                value = int(
                    input("Quantity: ")
                )

                update_quantity(
                    contract_item_id,
                    value
                )



            elif choice == "5":

                value = int(
                    input("Spot Length Seconds: ")
                )

                update_spot_length_seconds(
                    contract_item_id,
                    value
                )



            elif choice == "6":

                start_date = input(
                    "Start Date (blank for none): "
                ).strip()


                end_date = input(
                    "End Date (blank for none): "
                ).strip()


                if start_date == "":
                    start_date = None


                if end_date == "":
                    end_date = None


                update_dates(
                    contract_item_id,
                    start_date,
                    end_date
                )



            elif choice == "7":

                value = int(
                    input("Priority: ")
                )

                update_priority(
                    contract_item_id,
                    value
                )



            elif choice == "8":

                value = input(
                    "Rotation Group: "
                )

                update_rotation_group(
                    contract_item_id,
                    value
                )



            elif choice == "9":

                value = input(
                    "Notes: "
                )

                update_notes(
                    contract_item_id,
                    value
                )



            elif choice == "0":

                break


            else:

                print(
                    "\nInvalid option."
                )



        except ValueError as e:

            print(
                f"\nError: {e}"
            )



if __name__ == "__main__":

    main()
