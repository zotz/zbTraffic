# File: traffic/separation_rules.py

from traffic.database import get_connection



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
    Determine whether a commercial may be added to an avail.

    Currently always returns True.

    Future versions will compare the commercial against
    commercials already assigned to the avail and enforce
    category separation rules.
    """

    return True



