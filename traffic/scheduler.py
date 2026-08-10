# File: traffic/scheduler.py

# refactored Aug 10 2026

import random

random.seed(12345)

from datetime import (
    datetime,
    timedelta
)

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

        AND avails.status IN ('Open', 'Partial')


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

    # change back to first to last scheduling
    #avail = candidates[0]
    # changed above to random for now to avoid starting early and moving down the day.
    # looking at results, this seems to be hour by hour while I currently want it at least day by day.
    #
    # Find a candidate avail that satisfies
    # separation rules.
    #

    random.shuffle(
        candidates
    )


    avail = None


    for candidate in candidates:

        if passes_separation_rules(
            candidate["id"],
            contract_item["commercial_id"]
        ):

            avail = candidate

            break


    if avail is None:

        raise RuntimeError(
            "No candidate avails satisfy "
            "separation rules."
        )


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



def get_week_start(
    air_date
):
    """
    Return the Monday date for the week
    containing air_date.
    """

    date = datetime.strptime(
        air_date,
        "%Y-%m-%d"
    )

    monday = (
        date
        - timedelta(
            days=date.weekday()
        )
    )

    return monday.strftime(
        "%Y-%m-%d"
    )

def count_scheduled_spots_for_contract_item_week(
    contract_item_id,
    week_start
):
    """
    Count scheduled spots for a contract item
    during the calendar week beginning on week_start.
    """

    date = datetime.strptime(
        week_start,
        "%Y-%m-%d"
    )

    week_end = (
        date
        + timedelta(days=6)
    ).strftime(
        "%Y-%m-%d"
    )


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            COUNT(*) AS spot_count

        FROM spots

        WHERE contract_item_id = ?

          AND status = 'Scheduled'

          AND air_date >= ?

          AND air_date <= ?
        """,
        (
            contract_item_id,
            week_start,
            week_end
        )
    )


    row = cursor.fetchone()


    connection.close()


    return row["spot_count"]


def count_scheduled_spots_for_contract_item_day(
    contract_item_id,
    air_date
):
    """
    Count scheduled spots for a contract item
    on a specific air date.
    """

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            COUNT(*) AS spot_count

        FROM spots

        WHERE contract_item_id = ?

          AND status = 'Scheduled'

          AND air_date = ?
        """,
        (
            contract_item_id,
            air_date
        )
    )


    row = cursor.fetchone()


    connection.close()


    return row["spot_count"]


def can_schedule_on_date(
    contract_item_id,
    air_date,
    spots_per_day,
    spots_per_week
):
    """
    Determine whether another spot may be scheduled
    for this contract item on this air date.

    Returns:
        True if scheduling is allowed.
        False if a daily or weekly limit has been reached.
    """

    #
    # Daily limit
    #

    if spots_per_day > 0:

        scheduled_today = (
            count_scheduled_spots_for_contract_item_day(
                contract_item_id,
                air_date
            )
        )

        if scheduled_today >= spots_per_day:

            return False


    #
    # Weekly limit
    #

    if spots_per_week > 0:

        week_start = get_week_start(
            air_date
        )

        scheduled_this_week = (
            count_scheduled_spots_for_contract_item_week(
                contract_item_id,
                week_start
            )
        )

        if scheduled_this_week >= spots_per_week:

            return False


    return True

def advance_date_index(
    date_index,
    dates_checked,
    eligible_dates
):
    """
    Advance to the next eligible date,
    wrapping to the beginning if necessary.
    """

    date_index += 1

    dates_checked += 1

    if date_index >= len(
        eligible_dates
    ):

        date_index = 0


    return (
        date_index,
        dates_checked
    )


def get_scheduling_limits(
    contract_item_id
):
    """
    Return the scheduling limits for a contract item.

    Returns:
        spots_per_day,
        spots_per_week
    """

    rules = list_contract_item_rules(
        contract_item_id
    )


    spots_per_day = 0

    spots_per_week = 0


    for rule in rules:

        if rule["spots_per_day"]:

            spots_per_day = rule["spots_per_day"]


        if rule["spots_per_week"]:

            spots_per_week = rule["spots_per_week"]


    return (
        spots_per_day,
        spots_per_week
    )

def get_eligible_dates(
    contract_item_id,
    start_date,
    end_date
):
    """
    Return dates within the flight that have
    at least one eligible avail.
    """

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT DISTINCT
            air_date

        FROM avails

        WHERE air_date >= ?
          AND air_date <= ?

        ORDER BY air_date
        """,
        (
            start_date,
            end_date
        )
    )


    date_rows = cursor.fetchall()

    connection.close()


    eligible_dates = []


    for row in date_rows:

        air_date = row["air_date"]


        candidates = find_candidate_avails(
            contract_item_id,
            air_date
        )


        if candidates:

            eligible_dates.append(
                air_date
            )


    return eligible_dates


def try_schedule_contract_item(
    contract_item_id,
    air_date
):
    """
    Try to schedule one spot for a contract item.

    Returns:
        spot_id if successful,
        None if scheduling fails.
    """

    try:

        return schedule_contract_item(
            contract_item_id,
            air_date
        )

    except (
        ValueError,
        RuntimeError
    ):

        return None


def schedule_contract_item_quantity(
    contract_item_id
):
    """
    Schedule the required quantity for a contract item.

    Spots are distributed across dates that have
    eligible avails.
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


    spots_per_day, spots_per_week = (
        get_scheduling_limits(
            contract_item_id
        )
    )



    quantity = contract_item["quantity"]


    if quantity <= 0:

        return []


    flight = get_contract_item_flight_dates(
        contract_item_id
    )


    start_date = flight["start_date"]

    end_date = flight["end_date"]


    eligible_dates = get_eligible_dates(
        contract_item_id,
        start_date,
        end_date
    )


    if not eligible_dates:

        raise ValueError(
            "No eligible avails found "
            "during the contract flight."
        )


    #
    # Distribute the quantity across
    # the eligible dates.
    #

    scheduled_spots = []


    date_index = 0
    
    dates_checked = 0


    while (
        len(scheduled_spots)
        < quantity
    ):


        air_date = eligible_dates[
            date_index
        ]


        if not can_schedule_on_date(
            contract_item_id,
            air_date,
            spots_per_day,
            spots_per_week
        ):


            date_index, dates_checked = (
                advance_date_index(
                    date_index,
                    dates_checked,
                    eligible_dates
                )
            )


            if dates_checked >= len(
                eligible_dates
            ):

                raise RuntimeError(
                    "Unable to schedule the remaining "
                    "spots because all eligible dates "
                    "have reached scheduling limits."
                )


            continue



        spot_id = try_schedule_contract_item(
            contract_item_id,
            air_date
        )


        if spot_id is not None:

            scheduled_spots.append(
                spot_id
            )

            dates_checked = 0



        #
        # Move to the next eligible date.
        #


        date_index += 1


        if date_index >= len(
            eligible_dates
        ):

            date_index = 0


        #
        # Safety check.
        #
        # If we have gone through every
        # eligible date without scheduling
        # anything, stop rather than looping
        # forever.
        #

        if (
            date_index == 0
            and
            len(scheduled_spots) == 0
        ):

            raise RuntimeError(
                "Unable to schedule any "
                "spots."
            )


    return scheduled_spots

