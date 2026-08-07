# File: traffic/programs.py

from traffic.database import get_connection

from traffic.utilities import (
    current_timestamp
)


def add_program(
    station_id,
    name,
    description=None,
    start_time=None,
    end_time=None
):

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    cursor.execute(
        """
        INSERT INTO programs
        (
            station_id,
            name,
            description,
            start_time,
            end_time,
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
            station_id,
            name,
            description,
            start_time,
            end_time,
            now,
            now
        )
    )


    connection.commit()

    program_id = cursor.lastrowid

    connection.close()


    return program_id



def get_program(
    program_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            *

        FROM programs

        WHERE id = ?
        """,
        (
            program_id,
        )
    )


    program = cursor.fetchone()

    connection.close()


    return program



def list_programs(
    station_id=None,
    include_inactive=False
):

    connection = get_connection()

    cursor = connection.cursor()


    sql = """
        SELECT
            *

        FROM programs

        WHERE 1=1
    """


    params = []


    if station_id is not None:

        sql += """
            AND station_id = ?
        """

        params.append(
            station_id
        )


    if not include_inactive:

        sql += """
            AND active = 1
        """


    sql += """
        ORDER BY name
    """


    cursor.execute(
        sql,
        params
    )


    programs = cursor.fetchall()

    connection.close()


    return programs


def list_programs_for_station(
    station_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            *

        FROM programs

        WHERE station_id = ?

        AND active = 1

        ORDER BY start_time
        """,
        (
            station_id,
        )
    )


    programs = cursor.fetchall()

    connection.close()


    return programs


def update_program(
    program_id,
    name=None,
    description=None,
    start_time=None,
    end_time=None
):

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    cursor.execute(
        """
        UPDATE programs

        SET
            name = COALESCE(?, name),
            description = COALESCE(?, description),
            start_time = COALESCE(?, start_time),
            end_time = COALESCE(?, end_time),
            modified_date = ?

        WHERE id = ?
        """,
        (
            name,
            description,
            start_time,
            end_time,
            now,
            program_id
        )
    )


    connection.commit()

    changed = cursor.rowcount

    connection.close()


    return changed > 0



def activate_program(
    program_id
):

    return _set_program_active(
        program_id,
        1
    )



def deactivate_program(
    program_id
):

    return _set_program_active(
        program_id,
        0
    )



def _set_program_active(
    program_id,
    active
):

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    cursor.execute(
        """
        UPDATE programs

        SET
            active = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            active,
            now,
            program_id
        )
    )


    connection.commit()

    changed = cursor.rowcount

    connection.close()


    return changed > 0
