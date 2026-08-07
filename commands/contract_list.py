# File: commands/contract_list.py

import sys

from traffic.database import get_connection



def main():

    active_only = True


    if "--all" in sys.argv:

        active_only = False



    connection = get_connection()
    cursor = connection.cursor()



    if active_only:

        cursor.execute(
            """
            SELECT

                contracts.id,

                customers.company_name,

                contracts.description,

                salespeople.first_name,
                salespeople.last_name,

                stations.name AS station_name,

                contracts.status,

                contracts.active,

                contracts.start_date,
                contracts.end_date


            FROM contracts


            JOIN customers
                ON contracts.customer_id = customers.id


            JOIN salespeople
                ON contracts.salesperson_id = salespeople.id


            JOIN stations
                ON contracts.station_id = stations.id


            WHERE contracts.active = 1


            ORDER BY contracts.id
            """
        )


    else:

        cursor.execute(
            """
            SELECT

                contracts.id,

                customers.company_name,

                contracts.description,

                salespeople.first_name,
                salespeople.last_name,

                stations.name AS station_name,

                contracts.status,

                contracts.active,

                contracts.start_date,
                contracts.end_date


            FROM contracts


            JOIN customers
                ON contracts.customer_id = customers.id


            JOIN salespeople
                ON contracts.salesperson_id = salespeople.id


            JOIN stations
                ON contracts.station_id = stations.id


            ORDER BY contracts.id
            """
        )



    contracts = cursor.fetchall()


    connection.close()



    if not contracts:

        if active_only:

            print("\nNo active contracts found.\n")

        else:

            print("\nNo contracts found.\n")

        return



    print()

    print(
        f"{'ID':<5}"
        f"{'Customer':<25}"
        f"{'Description':<35}"
        f"{'Salesperson':<20}"
        f"{'Station':<15}"
        f"{'Status':<12}"
        f"{'Active':<8}"
    )

    print("-" * 120)



    for contract in contracts:

        salesperson = (
            f"{contract['first_name']} {contract['last_name']}"
        ).strip()


        print(

            f"{contract['id']:<5}"
            f"{contract['company_name'][:24]:<25}"
            f"{contract['description'][:34]:<35}"
            f"{salesperson[:19]:<20}"
            f"{contract['station_name'][:14]:<15}"
            f"{contract['status']:<12}"
            f"{contract['active']:<8}"

        )


    print()



if __name__ == "__main__":

    main()
