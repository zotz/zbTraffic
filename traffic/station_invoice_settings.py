# File: traffic/station_invoice_settings.py

"""
Station invoice settings data access.

Stores invoice-specific presentation/configuration settings for each station.
"""

from traffic.database import get_connection
from traffic.utilities import current_timestamp


def get_station_invoice_settings(station_id):
    """
    Return invoice settings for a station as a dictionary.

    Returns:
        dict | None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                station_id,
                biller_block,
                corporate_logo,
                station_logo,
                payment_instructions,
                invoice_footer,
                created_date,
                modified_date
            FROM station_invoice_settings
            WHERE station_id = ?
            """,
            (station_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        conn.close()


def create_station_invoice_settings(
    station_id,
    biller_block="",
    corporate_logo=None,
    station_logo=None,
    payment_instructions=None,
    invoice_footer=None
):
    """
    Create invoice settings for a station.

    Returns:
        (id, errors)

    On success:
        (new_id, [])

    On failure:
        (None, [error_message, ...])
    """
    errors = []

    if not station_id:
        errors.append("Station ID is required.")

    if errors:
        return None, errors

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Make sure the station exists.
        cursor.execute(
            "SELECT id FROM stations WHERE id = ?",
            (station_id,)
        )

        if cursor.fetchone() is None:
            return None, ["Station does not exist."]

        # Only one settings record is allowed per station.
        cursor.execute(
            """
            SELECT id
            FROM station_invoice_settings
            WHERE station_id = ?
            """,
            (station_id,)
        )

        if cursor.fetchone() is not None:
            return None, [
                "Invoice settings already exist for this station."
            ]

        timestamp = current_timestamp()

        cursor.execute(
            """
            INSERT INTO station_invoice_settings (
                station_id,
                biller_block,
                corporate_logo,
                station_logo,
                payment_instructions,
                invoice_footer,
                created_date,
                modified_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                station_id,
                biller_block,
                corporate_logo,
                station_logo,
                payment_instructions,
                invoice_footer,
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


def update_station_invoice_settings(
    station_id,
    biller_block="",
    corporate_logo=None,
    station_logo=None,
    payment_instructions=None,
    invoice_footer=None
):
    """
    Update invoice settings for a station.

    Returns:
        (success, errors)
    """
    errors = []

    if not station_id:
        errors.append("Station ID is required.")

    if errors:
        return False, errors

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Make sure the settings record exists.
        cursor.execute(
            """
            SELECT id
            FROM station_invoice_settings
            WHERE station_id = ?
            """,
            (station_id,)
        )

        if cursor.fetchone() is None:
            return False, [
                "Invoice settings do not exist for this station."
            ]

        timestamp = current_timestamp()

        cursor.execute(
            """
            UPDATE station_invoice_settings
            SET
                biller_block = ?,
                corporate_logo = ?,
                station_logo = ?,
                payment_instructions = ?,
                invoice_footer = ?,
                modified_date = ?
            WHERE station_id = ?
            """,
            (
                biller_block,
                corporate_logo,
                station_logo,
                payment_instructions,
                invoice_footer,
                timestamp,
                station_id
            )
        )

        conn.commit()

        return True, []

    except Exception as exc:
        conn.rollback()
        return False, [str(exc)]

    finally:
        conn.close()
