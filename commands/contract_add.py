from traffic.contracts import add_contract


def main():

    print("\nAdd New Contract")
    print("-----------------\n")


    try:

        customer_id = int(
            input("Customer ID: ")
        )


        salesperson_id = int(
            input("Salesperson ID: ")
        )


        station_id = int(
            input("Station ID: ")
        )


        contract_number = input(
            "Contract Number (optional): "
        ).strip()


        description = input(
            "Description: "
        ).strip()


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


        status = input(
            "Status [Draft]: "
        ).strip()


        if status == "":
            status = "Draft"


        notes = input(
            "Notes (optional): "
        ).strip()



        contract_id = add_contract(

            customer_id,
            salesperson_id,
            station_id,

            contract_number,
            description,

            start_date,
            end_date,

            status,

            notes

        )


        print(
            f"\nContract added successfully. ID: {contract_id}"
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
