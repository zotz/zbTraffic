# commands/contract_item_add.py

from traffic.contract_items import add_contract_item


def main():

    print("\nAdd New Contract Item")
    print("---------------------\n")


    try:

        contract_id = int(
            input("Contract ID: ")
        )


        commercial_id_input = input(
            "Commercial ID (optional): "
        ).strip()


        if commercial_id_input == "":
            commercial_id = None

        else:
            commercial_id = int(
                commercial_id_input
            )


        commercial_title = input(
            "Commercial Title (optional): "
        ).strip()


        spot_length_input = input(
            "Spot Length Seconds: "
        ).strip()


        if spot_length_input == "":

            spot_length_seconds = None

        else:

            spot_length_seconds = int(
                spot_length_input
            )


        description = input(
            "Description (optional): "
        ).strip()


        quantity = int(
            input("Quantity: ")
        )


        start_date = input(
            "Start Date (YYYY-MM-DD, optional): "
        ).strip()


        if start_date == "":
            start_date = None


        end_date = input(
            "End Date (YYYY-MM-DD, optional): "
        ).strip()


        if end_date == "":
            end_date = None


        priority_input = input(
            "Priority [1]: "
        ).strip()


        if priority_input == "":

            priority = 1

        else:

            priority = int(
                priority_input
            )


        rotation_group = input(
            "Rotation Group (optional): "
        ).strip()


        notes = input(
            "Notes (optional): "
        ).strip()



        contract_item_id = add_contract_item(

            contract_id,

            commercial_id,

            commercial_title,

            description,

            quantity,

            spot_length_seconds,

            start_date,

            end_date,

            priority,

            rotation_group,

            notes

        )


        print(
            f"\nContract item added successfully. ID: {contract_item_id}"
        )


    except ValueError as e:

        print(
            f"\nError: {e}"
        )


    except Exception as e:

        print(
            f"\nUnexpected error: {e}"
        )



if __name__ == "__main__":
    main()
