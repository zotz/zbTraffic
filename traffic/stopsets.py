# File: traffic/stopsets.py

from traffic.database import get_connection

from traffic.utilities import (
    current_timestamp
)


def add_stopset(
    program_id,
    name,
    start_time,
    end_time,
    maximum_seconds
):

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    cursor.execute(
        """
        INSERT INTO stopsets
        (
            program_id,
            name,
            start_time,
            end_time,
            maximum_seconds,
            active,
            created_date,
            modified_date
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            1,
            ?,
            ?
        )
        """,
        (
            program_id,
            name,
            start_time,
            end_time,
            maximum_seconds,
            now,
            now
        )
    )


    connection.commit()

    stopset_id = cursor.lastrowid

    connection.close()


    return stopset_id



def get_stopset(
    stopset_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            *

        FROM stopsets

        WHERE id = ?
        """,
        (
            stopset_id,
        )
    )


    stopset = cursor.fetchone()

    connection.close()


    return stopset



def list_stopsets(
    program_id=None,
    include_inactive=False
):

    connection = get_connection()

    cursor = connection.cursor()


    sql = """
        SELECT
            *

        FROM stopsets

        WHERE 1=1
    """


    params = []


    if program_id is not None:

        sql += """
            AND program_id = ?
        """

        params.append(
            program_id
        )


    if not include_inactive:

        sql += """
            AND active = 1
        """


    sql += """
        ORDER BY start_time
    """


    cursor.execute(
        sql,
        params
    )


    stopsets = cursor.fetchall()

    connection.close()


    return stopsets


def list_stopsets_for_program(
    program_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            *

        FROM stopsets

        WHERE program_id = ?

        AND active = 1

        ORDER BY start_time
        """,
        (
            program_id,
        )
    )


    stopsets = cursor.fetchall()

    connection.close()


    return stopsets


def update_stopset(
    stopset_id,
    name=None,
    start_time=None,
    end_time=None,
    maximum_seconds=None
):

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    cursor.execute(
        """
        UPDATE stopsets

        SET
            name = COALESCE(?, name),
            start_time = COALESCE(?, start_time),
            end_time = COALESCE(?, end_time),
            maximum_seconds = COALESCE(?, maximum_seconds),
            modified_date = ?

        WHERE id = ?
        """,
        (
            name,
            start_time,
            end_time,
            maximum_seconds,
            now,
            stopset_id
        )
    )


    connection.commit()

    changed = cursor.rowcount

    connection.close()


    return changed > 0



def activate_stopset(
    stopset_id
):

    return _set_stopset_active(
        stopset_id,
        1
    )



def deactivate_stopset(
    stopset_id
):

    return _set_stopset_active(
        stopset_id,
        0
    )



def _set_stopset_active(
    stopset_id,
    active
):

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    cursor.execute(
        """
        UPDATE stopsets

        SET
            active = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            active,
            now,
            stopset_id
        )
    )


    connection.commit()

    changed = cursor.rowcount

    connection.close()


    return changed > 0
