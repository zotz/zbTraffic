# File: commands/contract_item_schedule_test.py

import sys

from traffic.contract_items import (
    get_contract_item
)

from traffic.contracts import (
    get_contract
)

from traffic.scheduler import (
    find_candidate_avails,
    get_contract_item_flight_dates,
)

from traffic.spots import (
    count_spots_for_contract_item
)


def main():

    if len(sys.argv) < 3:

        print(
            "Usage:"
        )

        print(
            "python3 -m commands.contract_item_schedule_test <contract_item_id> <air_date>"
        )

        return


    contract_item_id = int(
        sys.argv[1]
    )

    air_date = sys.argv[2]


    contract_item = get_contract_item(
        contract_item_id
    )


    if contract_item is None:

        print(
            "Contract item not found."
        )

        return


    contract = get_contract(
        contract_item["contract_id"]
    )


    print()
    print("Contract Item Schedule Test")
    print("==========================")
    print()

    print(
        f"Contract Item: {contract_item_id}"
    )

    print(
        f"Commercial: {contract_item['commercial_title']}"
    )

    print(
        f"Quantity: {contract_item['quantity']}"
    )

    print(
        f"Already Generated: {count_spots_for_contract_item(contract_item_id)}"
    )

    print(
        f"Remaining: {contract_item['quantity'] - count_spots_for_contract_item(contract_item_id)}"
    )

    print()

    dates = get_contract_item_flight_dates(
        contract_item_id
    )

    print(
        f"Flight Dates: {dates['start_date']} -> {dates['end_date']}"
    )

    print()


    avails = find_candidate_avails(
        contract_item_id,
        air_date
    )


    print(
        f"Candidate avails on {air_date}: {len(avails)}"
    )

    print()


    for avail in avails[:10]:

        print(
            f"{avail['id']} "
            f"{avail['start_time']} "
            f"{avail['program_name']} "
            f"{avail['stopset_name']}"
        )


    print()


if __name__ == "__main__":

    main()
