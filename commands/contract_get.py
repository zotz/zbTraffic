# commands/contract_get.py

import sys

from traffic.database import get_connection


def main():

    if len(sys.argv) < 2:

        print(
            "\nUsage: python -m commands.contract_get <contract_id>\n"
        )

        return


    contract_id = sys.argv[1]


    if not contract_id.isdigit():

        print(
            "\nInvalid contract ID.\n"
        )

        return


    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT

            contracts.id,

            customers.company_name,

            contracts.contract_number,

            contracts.description,

            salespeople.first_name,
            salespeople.last_name,

            stations.name AS station_name,

            contracts.start_date,
            contracts.end_date,

            contracts.status,

            contracts.notes,

            contracts.active,

            contracts.created_date,
            contracts.modified_date


        FROM contracts


        JOIN customers
            ON contracts.customer_id = customers.id


        JOIN salespeople
            ON contracts.salesperson_id = salespeople.id


        JOIN stations
            ON contracts.station_id = stations.id


        WHERE contracts.id = ?

        """,
        (
            contract_id,
        )
    )


    contract = cursor.fetchone()


    connection.close()


    if contract is None:

        print(
            f"\nContract ID {contract_id} not found.\n"
        )
        return



    salesperson = (
        f"{contract['first_name']} {contract['last_name']}"
    ).strip()



    print()

    print("=" * 60)

    print(
        f"Contract ID: {contract['id']}"
    )

    print("=" * 60)


    print(
        f"\nCustomer:"
        f"\n  {contract['company_name']}"
    )


    print(
        f"\nContract Number:"
        f"\n  {contract['contract_number']}"
    )


    print(
        f"\nDescription:"
        f"\n  {contract['description']}"
    )


    print(
        f"\nSalesperson:"
        f"\n  {salesperson}"
    )


    print(
        f"\nStation:"
        f"\n  {contract['station_name']}"
    )


    print(
        f"\nDates:"
        f"\n  {contract['start_date']} "
        f"to "
        f"{contract['end_date']}"
    )


    print(
        f"\nStatus:"
        f"\n  {contract['status']}"
    )


    print(
        f"\nActive:"
        f"\n  {'Yes' if contract['active'] else 'No'}"
    )


    print(
        f"\nNotes:"
        f"\n  {contract['notes']}"
    )


    print("\nContract Items:")
    print("  (none yet)")


    print()




if __name__ == "__main__":
    main()
