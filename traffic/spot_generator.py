# File: traffic/spot_generator.py

from datetime import datetime, timedelta

from traffic.contract_items import (
    get_contract_item
)

from traffic.scheduler import (
    schedule_contract_item,
    get_contract_item_flight_dates,
)

from traffic.spots import (
    count_spots_for_contract_item
)


def get_dates_between(
    start_date,
    end_date
):
    """
    Return all dates between two dates inclusive.
    """

    start = datetime.strptime(
        start_date,
        "%Y-%m-%d"
    )

    end = datetime.strptime(
        end_date,
        "%Y-%m-%d"
    )


    dates = []


    current = start


    while current <= end:

        dates.append(
            current.strftime("%Y-%m-%d")
        )

        current += timedelta(
            days=1
        )


    return dates



def generate_spots_for_contract_item(
    contract_item_id
):
    """
    Generate missing spots for a contract item.

    Current behavior:

    - Uses total quantity.
    - Spreads spots evenly over flight dates.
    - Uses scheduler to place each spot.

    Returns:

        list of generated spot IDs
    """


    contract_item = get_contract_item(
        contract_item_id
    )


    if contract_item is None:

        raise ValueError(
            "Contract item not found."
        )


    quantity = contract_item["quantity"]


    existing = count_spots_for_contract_item(
        contract_item_id
    )


    remaining = quantity - existing


    if remaining <= 0:

        return []



    flight_dates = get_contract_item_flight_dates(
        contract_item_id
    )


    if not flight_dates["start_date"] or not flight_dates["end_date"]:

        raise ValueError(
            "Contract item has no flight dates."
        )


    dates = get_dates_between(
        flight_dates["start_date"],
        flight_dates["end_date"]
    )


    if not dates:

        raise ValueError(
            "No valid flight dates."
        )



    generated = []


    #
    # Spread spots evenly
    #

    interval = len(dates) / remaining


    for number in range(
        remaining
    ):


        date_index = int(
            number * interval
        )


        air_date = dates[
            date_index
        ]

        print(f"Trying {air_date}")


        spot_id = schedule_contract_item(
            contract_item_id,
            air_date
        )
        


        generated.append(
            spot_id
        )


    return generated
