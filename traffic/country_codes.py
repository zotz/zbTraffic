# File: traffic/country_codes.py


"""
Country code data access.

Stores user-defined country codes and their corresponding country names.
"""

from traffic.database import get_connection
from traffic.utilities import current_timestamp


def get_country_name(country_code):
    """
    Return the country name for a country code.

    The lookup is case-insensitive.

    Returns:
        str | None
    """
    if not country_code:
        return None

    country_code = country_code.strip().upper()

    if not country_code:
        return None

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT country_name
            FROM country_codes
            WHERE country_code = ?
            """,
            (country_code,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return row["country_name"]

    finally:
        conn.close()


def get_country_code(country_id):
    """
    Return a country code record by ID.

    Returns:
        dict | None
    """
    if not country_id:
        return None

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                country_code,
                country_name,
                created_date,
                modified_date
            FROM country_codes
            WHERE id = ?
            """,
            (country_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        conn.close()


def list_country_codes():
    """
    Return all country codes ordered by country name.

    Returns:
        list[dict]
    """
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                country_code,
                country_name,
                created_date,
                modified_date
            FROM country_codes
            ORDER BY country_name
            """
        )

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def create_country_code(country_code, country_name):
    """
    Create a country code.

    Returns:
        (id, errors)

    On success:
        (new_id, [])

    On failure:
        (None, [error_message, ...])
    """
    errors = []

    if not country_code or not country_code.strip():
        errors.append("Country code is required.")

    if not country_name or not country_name.strip():
        errors.append("Country name is required.")

    if errors:
        return None, errors

    country_code = country_code.strip().upper()
    country_name = country_name.strip()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM country_codes
            WHERE country_code = ?
            """,
            (country_code,)
        )

        if cursor.fetchone() is not None:
            return None, [
                "Country code already exists."
            ]

        timestamp = current_timestamp()

        cursor.execute(
            """
            INSERT INTO country_codes (
                country_code,
                country_name,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                country_code,
                country_name,
                timestamp,
                timestamp
            )
        )

        conn.commit()

        return cursor.lastrowid, []

    except Exception as exc:
        conn.rollback()
        return None, [str(exc)]

    finally:
        conn.close()


def update_country_code(country_id, country_code, country_name):
    """
    Update a country code.

    Returns:
        (success, errors)
    """
    errors = []

    if not country_id:
        errors.append("Country ID is required.")

    if not country_code or not country_code.strip():
        errors.append("Country code is required.")

    if not country_name or not country_name.strip():
        errors.append("Country name is required.")

    if errors:
        return False, errors

    country_code = country_code.strip().upper()
    country_name = country_name.strip()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM country_codes
            WHERE id = ?
            """,
            (country_id,)
        )

        if cursor.fetchone() is None:
            return False, [
                "Country code does not exist."
            ]

        # Make sure another record is not already using this code.
        cursor.execute(
            """
            SELECT id
            FROM country_codes
            WHERE country_code = ?
              AND id != ?
            """,
            (
                country_code,
                country_id
            )
        )

        if cursor.fetchone() is not None:
            return False, [
                "Country code already exists."
            ]

        timestamp = current_timestamp()

        cursor.execute(
            """
            UPDATE country_codes
            SET
                country_code = ?,
                country_name = ?,
                modified_date = ?
            WHERE id = ?
            """,
            (
                country_code,
                country_name,
                timestamp,
                country_id
            )
        )

        conn.commit()

        return True, []

    except Exception as exc:
        conn.rollback()
        return False, [str(exc)]

    finally:
        conn.close()


def delete_country_code(country_id):
    """
    Delete a country code.

    Returns:
        (success, errors)
    """
    errors = []

    if not country_id:
        errors.append("Country ID is required.")

    if errors:
        return False, errors

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM country_codes
            WHERE id = ?
            """,
            (country_id,)
        )

        if cursor.fetchone() is None:
            return False, [
                "Country code does not exist."
            ]

        cursor.execute(
            """
            DELETE FROM country_codes
            WHERE id = ?
            """,
            (country_id,)
        )

        conn.commit()

        return True, []

    except Exception as exc:
        conn.rollback()
        return False, [str(exc)]

    finally:
        conn.close()