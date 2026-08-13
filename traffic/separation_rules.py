# File: traffic/separation_rules.py

from datetime import datetime

from traffic.database import get_connection

from traffic.utilities import (
    current_timestamp,
    normalize_time
)


def get_separation_rule(
    category1_id,
    category2_id
):
    """
    Return the separation rule between two categories.

    Rules are treated as symmetric.
    """

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *

        FROM separation_rules

        WHERE active = 1

        AND (
            (
                category1_id = ?
                AND category2_id = ?
            )

            OR

            (
                category1_id = ?
                AND category2_id = ?
            )
        )

        ORDER BY minimum_minutes DESC

        LIMIT 1
        """,
        (
            category1_id,
            category2_id,

            category2_id,
            category1_id
        )
    )


    rule = cursor.fetchone()


    connection.close()


    return rule



def get_separation_minutes(
    category1_id,
    category2_id
):
    """
    Return required separation time in minutes.

    Returns 0 if no rule exists.
    """


    rule = get_separation_rule(
        category1_id,
        category2_id
    )


    if rule is None:

        return 0


    return rule["minimum_minutes"]



def check_separation(
    previous_category_id,
    new_category_id,
    minutes_apart
):
    """
    Determine if two categories may run together.

    Returns True if allowed.
    Returns False if separation rule is violated.
    """


    required_minutes = get_separation_minutes(
        previous_category_id,
        new_category_id
    )


    if required_minutes == 0:

        return True


    return minutes_apart >= required_minutes


def passes_separation_rules(
    avail_id,
    commercial_id
):
    """
    Determine whether a commercial may be scheduled
    at the start time of an avail.

    Checks scheduled spots before and after the
    proposed time on the same station.

    Returns:
        True if all separation rules pass.
        False if any rule is violated.
    """

    connection = get_connection()
    cursor = connection.cursor()


    #
    # Get the proposed avail.
    #

    cursor.execute(
        """
        SELECT
            station_id,
            air_date,
            start_time

        FROM avails

        WHERE id = ?
        """,
        (
            avail_id,
        )
    )


    avail = cursor.fetchone()


    if avail is None:

        connection.close()

        return False


    #
    # Get the proposed commercial category.
    #

    cursor.execute(
        """
        SELECT
            category_id

        FROM commercials

        WHERE id = ?
        """,
        (
            commercial_id,
        )
    )


    commercial = cursor.fetchone()


    if commercial is None:

        connection.close()

        return False


    new_category_id = commercial[
        "category_id"
    ]


    #
    # No category means there can be
    # no category separation rule.
    #

    if new_category_id is None:

        connection.close()

        return True


    #
    # Get scheduled spots on this station.
    #

    cursor.execute(
        """
        SELECT
            spots.id,
            spots.air_date,
            spots.air_time,
            spots.commercial_id,
            commercials.category_id

        FROM spots

        JOIN commercials
            ON spots.commercial_id = commercials.id

        WHERE spots.station_id = ?

        AND spots.status = 'Scheduled'

        AND spots.air_date IS NOT NULL

        AND spots.air_time IS NOT NULL
        """,
        (
            avail["station_id"],
        )
    )


    scheduled_spots = cursor.fetchall()


    connection.close()


    #
    # Convert proposed date/time to a datetime.
    #

    proposed_datetime = datetime.strptime(
        (
            f"{avail['air_date']} "
            f"{normalize_time(avail['start_time'])}"
        ),
        "%Y-%m-%d %H:%M:%S"
    )


    #
    # Check every scheduled spot.
    #

    for existing in scheduled_spots:

        if existing["category_id"] is None:

            continue


        #
        # Don't compare a spot with itself
        # if this function is ever called on
        # an already-assigned spot.
        #

        if (
            existing["commercial_id"]
            == commercial_id
            and
            existing["air_date"]
            == avail["air_date"]
            and
            normalize_time(
                existing["air_time"]
            )
            == normalize_time(
                avail["start_time"]
            )
        ):

            continue


        existing_datetime = datetime.strptime(
            (
                f"{existing['air_date']} "
                f"{normalize_time(existing['air_time'])}"
            ),
            "%Y-%m-%d %H:%M:%S"
        )


        minutes_apart = abs(
            (
                proposed_datetime
                - existing_datetime
            ).total_seconds()
        ) / 60


        if not check_separation(
            existing["category_id"],
            new_category_id,
            minutes_apart
        ):

            return False


    return True

def add_separation_rule(
    category1_id,
    category2_id,
    minimum_minutes=0,
    notes=None
):
    """
    Add a separation rule between two categories.

    Rules are treated as symmetric.
    """

    errors = []

    if category1_id is None:
        errors.append(
            "Category 1 is required."
        )

    if category2_id is None:
        errors.append(
            "Category 2 is required."
        )

    if not isinstance(
        minimum_minutes,
        int
    ):
        errors.append(
            "Minimum minutes must be an integer."
        )

    elif minimum_minutes < 0:
        errors.append(
            "Minimum minutes cannot be negative."
        )

    if errors:
        return None, errors

    connection = get_connection()
    cursor = connection.cursor()

    #
    # Make sure both categories exist.
    #

    cursor.execute(
        """
        SELECT id
        FROM categories
        WHERE id = ?
        """,
        (category1_id,)
    )

    if cursor.fetchone() is None:

        connection.close()

        return None, [
            "Category 1 not found."
        ]

    cursor.execute(
        """
        SELECT id
        FROM categories
        WHERE id = ?
        """,
        (category2_id,)
    )

    if cursor.fetchone() is None:

        connection.close()

        return None, [
            "Category 2 not found."
        ]

    #
    # Because rules are symmetric, don't allow
    # the same pair to be added twice.
    #

    cursor.execute(
        """
        SELECT id
        FROM separation_rules
        WHERE
            (
                category1_id = ?
                AND category2_id = ?
            )
            OR
            (
                category1_id = ?
                AND category2_id = ?
            )
        """,
        (
            category1_id,
            category2_id,
            category2_id,
            category1_id
        )
    )

    existing = cursor.fetchone()

    if existing:

        connection.close()

        return None, [
            "Separation rule already exists."
        ]

    now = current_timestamp()

    cursor.execute(
        """
        INSERT INTO separation_rules
        (
            category1_id,
            category2_id,
            minimum_minutes,
            active,
            notes,
            created_date,
            modified_date
        )
        VALUES
        (
            ?,
            ?,
            ?,
            1,
            ?,
            ?,
            ?
        )
        """,
        (
            category1_id,
            category2_id,
            minimum_minutes,
            notes,
            now,
            now
        )
    )

    connection.commit()

    rule_id = cursor.lastrowid

    connection.close()

    return rule_id, []

