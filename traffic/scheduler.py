# File: traffic/scheduler.py

import random

from datetime import datetime

from traffic.database import get_connection

from traffic.assignment import (
    assign_spot_to_avail
)

from traffic.spots import (
    add_spot,
    count_spots_for_contract_item
)

from traffic.contract_items import (
    get_contract_item
)

from traffic.contracts import (
    get_contract
)

from traffic.separation_rules import (
    passes_separation_rules
)


from traffic.contract_item_rules import (
    list_contract_item_rules
)



def get_day_name(
    air_date
):
    """
    Return abbreviated weekday name.

    Example:
        2026-08-06 -> Thu
    """

    date = datetime.strptime(
        air_date,
        "%Y-%m-%d"
    )

    return date.strftime(
        "%a"
    )

def get_contract_item_flight_dates(
    contract_item_id
):
    """
    Return the effective flight dates for a contract item.

    Contract item dates override contract dates.
    Contract dates are used as fallback.
    """

    contract_item = get_contract_item(
        contract_item_id
    )


    if contract_item is None:

        raise ValueError(
            "Contract item not found."
        )


    contract = get_contract(
        contract_item["contract_id"]
    )


    if contract is None:

        raise ValueError(
            "Contract not found."
        )


    start_date = contract_item["start_date"]

    end_date = contract_item["end_date"]


    if start_date is None:

        start_date = contract["start_date"]


    if end_date is None:

        end_date = contract["end_date"]


    if start_date is None or end_date is None:

        raise ValueError(
            "No flight dates available."
        )


    return {
        "start_date": start_date,
        "end_date": end_date
    }



def time_in_range(
    check_time,
    start_time,
    end_time
):
    """
    Check whether a time falls within a rule window.

    Empty start/end times mean no restriction.
    """


    if not start_time or not end_time:

        return True


    return (
        start_time
        <= check_time
        <= end_time
    )



def find_candidate_avails(
    contract_item_id,
    air_date
):
    """
    Find possible avails for a contract item.

    This function is read-only.

    It does not:
        - create spots
        - assign avails
        - check separation
        - modify inventory

    It only identifies possible inventory.
    """


    rules = list_contract_item_rules(
        contract_item_id
    )


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT

            avails.id,

            avails.station_id,

            avails.stopset_id,

            avails.air_date,

            avails.start_time,

            avails.length_seconds,

            avails.status,


            stopsets.name AS stopset_name,

            programs.id AS program_id,

            programs.name AS program_name


        FROM avails


        LEFT JOIN stopsets

            ON avails.stopset_id = stopsets.id


        LEFT JOIN programs

            ON stopsets.program_id = programs.id


        WHERE avails.air_date = ?

        AND avails.status = 'Open'


        ORDER BY

            avails.start_time

        """,
        (
            air_date,
        )
    )


    avails = cursor.fetchall()


    connection.close()



    #
    # No rules means any open avail is acceptable
    #

    if not rules:

        return avails



    day_name = get_day_name(
        air_date
    )


    candidates = []



    for avail in avails:


        for rule in rules:


            #
            # Day of week
            #

            if rule["days_of_week"]:

                allowed_days = [

                    day.strip()

                    for day in rule["days_of_week"].split(",")

                ]


                if day_name not in allowed_days:

                    continue



            #
            # Time window
            #

            if not time_in_range(

                avail["start_time"],

                rule["start_time"],

                rule["end_time"]

            ):

                continue



            #
            # Preferred program
            #

            if rule["preferred_program_id"] is not None:


                if avail["program_id"] != rule["preferred_program_id"]:

                    continue



            #
            # Preferred stopset
            #

            if rule["preferred_stopset_id"] is not None:


                if avail["stopset_id"] != rule["preferred_stopset_id"]:

                    continue



            candidates.append(
                avail
            )


            #
            # One matching rule is enough
            #

            break



    return candidates

def choose_best_avail(
    candidate_avails
):
    """
    Select the best avail from a list of candidates.

    Current implementation:
        Returns the first candidate.

    Future implementations may consider:

        * remaining inventory
        * preferred stopsets
        * load balancing
        * separation scoring
        * priority
    """

    if not candidate_avails:

        return None

    return candidate_avails[0]

def schedule_contract_item(
    contract_item_id,
    air_date
):
    """
    Create one scheduled spot
    from a contract item.

    Returns:
        spot_id

    or raises ValueError.
    """


    contract_item = get_contract_item(
        contract_item_id
    )


    if contract_item is None:

        raise ValueError(
            "Contract item not found."
        )


    if contract_item["active"] != 1:

        raise ValueError(
            "Contract item is inactive."
        )


    if contract_item["commercial_id"] is None:

        raise ValueError(
            "Contract item has no commercial assigned."
        )


    contract = get_contract(
        contract_item["contract_id"]
    )


    if contract is None:

        raise ValueError(
            "Contract not found."
        )


    if contract["active"] != 1:

        raise ValueError(
            "Contract is inactive."
        )


    candidates = find_candidate_avails(
        contract_item_id,
        air_date
    )


    if not candidates:

        raise ValueError(
            "No suitable avails found."
        )


    #avail = candidates[0]
    # changed above to random for now to avoid starting early and moving down the day.
    # looking at results, this seems to be hour by hour while I currently want it at least day by day.
    avail = random.choice(candidates)


    spot_id = add_spot(
        station_id=contract["station_id"],
        commercial_id=contract_item["commercial_id"],
        air_date=None,
        air_time=None,
        status="Pending",
        contract_item_id=contract_item_id
    )


    success, errors = assign_spot_to_avail(
        spot_id,
        avail["id"]
    )


    if not success:

        raise RuntimeError(
            errors
        )


    return spot_id


