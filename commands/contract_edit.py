# File: commands/contract_edit.py

import sys

from traffic.contracts import (
    get_contract,
    update_contract_number,
    update_contract_description,
    update_contract_dates,
    update_contract_status,
    update_contract_notes
)



def display_contract(
    contract
):

    print("\nCurrent Contract")
    print("----------------\n")

    print(f"ID: {contract['id']}")
    print(f"Customer ID: {contract['customer_id']}")
    print(f"Salesperson ID: {contract['salesperson_id']}")
    print(f"Station ID: {contract['station_id']}")
    print(f"Contract Number: {contract['contract_number']}")
    print(f"Description: {contract['description']}")
    print(f"Start Date: {contract['start_date']}")
    print(f"End Date: {contract['end_date']}")
    print(f"Status: {contract['status']}")
    print(f"Notes: {contract['notes']}")
    print(f"Active: {contract['active']}")
    print()



def main():

    if len(sys.argv) < 2:

        print(
            "\nUsage: python -m commands.contract_edit <contract_id>\n"
        )

        return


    contract_id = int(
        sys.argv[1]
    )


    contract = get_contract(
        contract_id
    )


    if contract is None:

        print(
            f"\nContract ID {contract_id} not found.\n"
        )

        return



    while True:

        contract = get_contract(
            contract_id
        )


        display_contract(
            contract
        )


        print("Edit Options")
        print("-------------")

        print("1. Contract Number")
        print("2. Description")
        print("3. Start/End Dates")
        print("4. Status")
        print("5. Notes")
        print("0. Exit")


        choice = input(
            "\nSelect option: "
        ).strip()



        try:

            if choice == "1":

                value = input(
                    "Contract Number: "
                )

                update_contract_number(
                    contract_id,
                    value
                )



            elif choice == "2":

                value = input(
                    "Description: "
                )

                update_contract_description(
                    contract_id,
                    value
                )



            elif choice == "3":

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


                update_contract_dates(
                    contract_id,
                    start_date,
                    end_date
                )



            elif choice == "4":

                value = input(
                    "Status: "
                )

                update_contract_status(
                    contract_id,
                    value
                )



            elif choice == "5":

                value = input(
                    "Notes: "
                )

                update_contract_notes(
                    contract_id,
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
