#!/usr/bin/env python3

# File: database/seed_common.py
#
# Common database seeding functions.
#
# Used by:
#   seed2_database.py
#
# Future:
#   seed_database.py


from traffic.database import get_connection



def table_has_rows(
    table_name
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM {table_name}
        """
    )


    count = cursor.fetchone()[0]


    connection.close()


    return count > 0



def check_prerequisites(
    required_tables
):

    missing = []


    for table in required_tables:

        if not table_has_rows(table):

            missing.append(
                table
            )


    if missing:

        raise RuntimeError(
            "Missing seed data: "
            + ", ".join(missing)
            + ". Run seed_database.py first."
        )


    return True



def get_first_station_id():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT id
        FROM stations
        ORDER BY id
        LIMIT 1
        """
    )


    row = cursor.fetchone()


    connection.close()


    if row is None:

        return None


    return row["id"]



def get_category_id(
    name
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT id
        FROM categories
        WHERE name = ?
        """,
        (
            name,
        )
    )


    row = cursor.fetchone()


    connection.close()


    if row is None:

        return None


    return row["id"]



def get_id_by_name(
    table,
    name
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        f"""
        SELECT id
        FROM {table}
        WHERE name = ?
        """,
        (
            name,
        )
    )


    row = cursor.fetchone()


    connection.close()


    if row is None:

        return None


    return row["id"]



def get_customer_id_by_company_name(
    company_name
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT id
        FROM customers
        WHERE company_name = ?
        """,
        (
            company_name,
        )
    )


    row = cursor.fetchone()


    connection.close()


    if row is None:

        return None


    return row["id"]


def get_seed_rotation():

    """
    Returns the standard seed commercial rotation.

    Each item contains:
        id
        length_seconds

    Raises RuntimeError if any expected commercial
    cannot be found.
    """

    connection = get_connection()

    cursor = connection.cursor()

    rotation = []

    for cart_number in (
        "000002",
        "000003",
        "000004",
    ):

        cursor.execute(
            """
            SELECT
                id,
                length_seconds
            FROM commercials
            WHERE cart_number = ?
            """,
            (
                cart_number,
            )
        )

        commercial = cursor.fetchone()

        if commercial is None:

            connection.close()

            raise RuntimeError(
                f"Required seed commercial {cart_number} not found."
            )

        rotation.append(commercial)

    connection.close()

    return rotation
