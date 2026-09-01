# File: traffic/contract_item_rules.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp


def validate_contract_item_rule(
    contract_item_id,
    preferred_program_id=None,
    preferred_stopset_id=None
):
    """
    Validate foreign keys before adding a contract item rule.
    """

    connection = get_connection()
    cursor = connection.cursor()


    #
    # Validate contract item
    #

    cursor.execute(
        """
        SELECT id
        FROM contract_items
        WHERE id = ?
        """,
        (
            contract_item_id,
        )
    )

    if cursor.fetchone() is None:

        connection.close()

        raise ValueError(
            f"Contract Item ID {contract_item_id} does not exist"
        )


    #
    # Validate preferred program (if supplied)
    #

    if preferred_program_id is not None:

        cursor.execute(
            """
            SELECT id
            FROM programs
            WHERE id = ?
            """,
            (
                preferred_program_id,
            )
        )

        if cursor.fetchone() is None:

            connection.close()

            raise ValueError(
                f"Program ID {preferred_program_id} does not exist"
            )


    #
    # Validate preferred stopset (if supplied)
    #

    if preferred_stopset_id is not None:

        cursor.execute(
            """
            SELECT id
            FROM stopsets
            WHERE id = ?
            """,
            (
                preferred_stopset_id,
            )
        )

        if cursor.fetchone() is None:

            connection.close()

            raise ValueError(
                f"Stopset ID {preferred_stopset_id} does not exist"
            )


    connection.close()



def add_contract_item_rule(
    contract_item_id,
    days_of_week="",
    start_time=None,
    end_time=None,
    preferred_program_id=None,
    preferred_stopset_id=None,
    max_spots_per_day=0,
    max_spots_per_week=0,
    allow_news=1,
    allow_special_events=1,
    notes=""
):
    """
    Add a contract item scheduling rule.
    """

    validate_contract_item_rule(
        contract_item_id,
        preferred_program_id,
        preferred_stopset_id
    )


    connection = get_connection()
    cursor = connection.cursor()


    timestamp = current_timestamp()


    cursor.execute(
        """
        INSERT INTO contract_item_rules (

            contract_item_id,

            days_of_week,

            start_time,
            end_time,

            preferred_program_id,

            preferred_stopset_id,

            max_spots_per_day,

            max_spots_per_week,

            allow_news,

            allow_special_events,

            active,

            notes,

            created_date,
            modified_date

        )

        VALUES (

            ?,

            ?,

            ?, ?,

            ?,

            ?,

            ?,

            ?,

            ?,

            ?,

            1,

            ?,

            ?, ?

        )
        """,
        (
            contract_item_id,

            days_of_week,

            start_time,
            end_time,

            preferred_program_id,

            preferred_stopset_id,

            max_spots_per_day,

            max_spots_per_week,

            allow_news,

            allow_special_events,

            notes,

            timestamp,
            timestamp
        )
    )


    rule_id = cursor.lastrowid


    connection.commit()
    connection.close()


    return rule_id



def get_contract_item_rule(
    rule_id
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM contract_item_rules
        WHERE id = ?
        """,
        (
            rule_id,
        )
    )


    rule = cursor.fetchone()


    connection.close()


    return rule



def list_contract_item_rules(
    contract_item_id=None,
    active_only=True
):

    connection = get_connection()
    cursor = connection.cursor()


    sql = """
        SELECT *
        FROM contract_item_rules
    """

    params = []


    where = []


    if contract_item_id is not None:

        where.append(
            "contract_item_id = ?"
        )

        params.append(
            contract_item_id
        )


    if active_only:

        where.append(
            "active = 1"
        )


    if where:

        sql += "\nWHERE " + " AND ".join(where)


    sql += "\nORDER BY id"


    cursor.execute(
        sql,
        tuple(params)
    )


    rules = cursor.fetchall()


    connection.close()


    return rules


def update_contract_item_rule(
    rule_id,
    days_of_week="",
    start_time=None,
    end_time=None,
    preferred_program_id=None,
    preferred_stopset_id=None,
    max_spots_per_day=0,
    max_spots_per_week=0,
    allow_news=1,
    allow_special_events=1,
    notes=""
):
    """
    Update an existing contract item rule.
    """

    connection = get_connection()
    cursor = connection.cursor()


    #
    # Ensure the rule exists
    #

    cursor.execute(
        """
        SELECT
            contract_item_id
        FROM contract_item_rules
        WHERE id = ?
        """,
        (
            rule_id,
        )
    )


    rule = cursor.fetchone()


    if rule is None:

        connection.close()

        raise ValueError(
            f"Contract Item Rule ID {rule_id} does not exist"
        )


    #
    # Validate referenced records
    #

    validate_contract_item_rule(
        rule["contract_item_id"],
        preferred_program_id,
        preferred_stopset_id
    )


    timestamp = current_timestamp()


    cursor.execute(
        """
        UPDATE contract_item_rules

        SET

            days_of_week = ?,

            start_time = ?,
            end_time = ?,

            preferred_program_id = ?,

            preferred_stopset_id = ?,

            max_spots_per_day = ?,

            max_spots_per_week = ?,

            allow_news = ?,

            allow_special_events = ?,

            notes = ?,

            modified_date = ?

        WHERE id = ?
        """,
        (
            days_of_week,

            start_time,
            end_time,

            preferred_program_id,

            preferred_stopset_id,

            max_spots_per_day,

            max_spots_per_week,

            allow_news,

            allow_special_events,

            notes,

            timestamp,

            rule_id
        )
    )


    connection.commit()
    connection.close()



def activate_contract_item_rule(
    rule_id
):
    """
    Activate a contract item rule.
    """

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contract_item_rules

        SET

            active = 1,

            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            rule_id
        )
    )


    connection.commit()
    connection.close()



def deactivate_contract_item_rule(
    rule_id
):
    """
    Deactivate a contract item rule.
    """

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contract_item_rules

        SET

            active = 0,

            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            rule_id
        )
    )


    connection.commit()
    connection.close()
