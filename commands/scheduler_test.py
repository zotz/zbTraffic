# File: commands/scheduler_test.py

import sys

from traffic.database import get_connection

from traffic.scheduler import (
    find_candidate_avails
)



def get_contract_item(
    contract_item_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT

            contract_items.id,

            contract_items.commercial_title,

            contract_items.description,

            customers.company_name


        FROM contract_items


        JOIN contracts

            ON contract_items.contract_id = contracts.id


        JOIN customers

            ON contracts.customer_id = customers.id


        WHERE contract_items.id = ?

        """,
        (
            contract_item_id,
        )
    )


    item = cursor.fetchone()


    connection.close()


    return item



def main():

    if len(sys.argv) < 3:

        print()

        print(
            "Usage:"
        )

        print(
            "python3 -m commands.scheduler_test <contract_item_id> <air_date>"
        )

        print()

        return



    contract_item_id = int(
        sys.argv[1]
    )


    air_date = sys.argv[2]



    contract_item = get_contract_item(
        contract_item_id
    )


    if contract_item is None:

        print()

        print(
            f"Contract item {contract_item_id} not found."
        )

        print()

        return



    print()

    print(
        "Scheduler Test"
    )

    print(
        "=============="
    )

    print()

    print(
        f"Contract Item ID: {contract_item['id']}"
    )

    print(
        f"Customer: {contract_item['company_name']}"
    )

    print(
        f"Commercial: {contract_item['commercial_title']}"
    )

    print(
        f"Date: {air_date}"
    )

    print()



    avails = find_candidate_avails(
        contract_item_id,
        air_date
    )



    if not avails:

        print(
            "No candidate avails found."
        )

        print()

        return



    print(
        "Candidate Avails"
    )

    print(
        "----------------"
    )


    print()

    print(

        f"{'ID':<5}"
        f"{'Time':<8}"
        f"{'Program':<25}"
        f"{'Stopset':<25}"
        f"{'Length':<10}"

    )


    print(
        "-" * 75
    )



    for avail in avails:


        print(

            f"{avail['id']:<5}"
            f"{avail['start_time']:<8}"
            f"{(avail['program_name'] or '')[:24]:<25}"
            f"{(avail['stopset_name'] or '')[:24]:<25}"
            f"{avail['length_seconds']:<10}"

        )


    print()



if __name__ == "__main__":
    main()
