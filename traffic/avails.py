#!/usr/bin/env python3

# File: traffic/avails.py

from traffic.database import (
    get_connection
)

from traffic.programs import (
    list_programs_for_station
)

from traffic.stopsets import (
    list_stopsets_for_program
)

from traffic.utilities import (
    current_timestamp
)



def add_avail(
    station_id,
    air_date,
    start_time,
    length_seconds,
    status=None,
    notes=None
):

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    if status is None:

        cursor.execute(
            """
            INSERT INTO avails
            (
                station_id,
                air_date,
                start_time,
                length_seconds,
                notes,
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
                ?,
                ?
            )
            """,
            (
                station_id,
                air_date,
                start_time,
                length_seconds,
                notes,
                now,
                now
            )
        )

    else:

        cursor.execute(
            """
            INSERT INTO avails
            (
                station_id,
                air_date,
                start_time,
                length_seconds,
                status,
                notes,
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
                ?,
                ?,
                ?
            )
            """,
            (
                station_id,
                air_date,
                start_time,
                length_seconds,
                status,
                notes,
                now,
                now
            )
        )


    connection.commit()


    avail_id = cursor.lastrowid


    connection.close()


    return avail_id



def get_avail(
    avail_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            id,
            station_id,
            air_date,
            start_time,
            length_seconds,
            status,
            notes,
            created_date,
            modified_date

        FROM avails

        WHERE id = ?
        """,
        (
            avail_id,
        )
    )


    avail = cursor.fetchone()


    connection.close()


    return avail

def get_used_seconds(
    avail_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(commercials.length_seconds),
                0
            ) AS used_seconds

        FROM spots

        JOIN commercials
            ON spots.commercial_id = commercials.id

        WHERE
            spots.avail_id = ?

        AND
            spots.status = 'Scheduled'
        """,
        (
            avail_id,
        )
    )


    row = cursor.fetchone()

    connection.close()


    return row["used_seconds"]

def get_remaining_seconds(
    avail_id
):

    avail = get_avail(
        avail_id
    )


    if avail is None:

        return None


    used_seconds = get_used_seconds(
        avail_id
    )


    remaining_seconds = (
        avail["length_seconds"]
        - used_seconds
    )


    return remaining_seconds

# generate_avails_for_date(station_id, air_date) goes here
def generate_avails_for_date(
    station_id,
    air_date
):

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()

    created = 0


    #
    # Get active programs
    #

    programs = list_programs_for_station(
        station_id
    )


    for program in programs:


        #
        # Get stopsets for this program
        #

        stopsets = list_stopsets_for_program(
            program["id"]
        )


        for stopset in stopsets:


            #
            # Skip incomplete stopsets
            #

            if (
                not stopset["start_time"]
                or
                not stopset["maximum_seconds"]
            ):

                continue


            #
            # Avoid duplicate avails
            #

            cursor.execute(
                """
                SELECT
                    id

                FROM avails

                WHERE station_id = ?

                  AND air_date = ?

                  AND start_time = ?

                  AND length_seconds = ?
                """,
                (
                    station_id,
                    air_date,
                    stopset["start_time"],
                    stopset["maximum_seconds"]
                )
            )


            if cursor.fetchone():

                continue


            #
            # Create avail
            #

            cursor.execute(
                """
                INSERT INTO avails
                (
                    station_id,
                    stopset_id,
                    air_date,
                    start_time,
                    length_seconds,
                    status,
                    notes,
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
                    'Open',
                    ?,
                    ?,
                    ?
                )
                """,
                (
                    station_id,
                    stopset["id"],
                    air_date,
                    stopset["start_time"],
                    stopset["maximum_seconds"],
                    (
                        "Generated from "
                        f"{program['name']} / "
                        f"{stopset['name']}"
                    ),
                    now,
                    now
                )
            )


            created += 1


    connection.commit()

    connection.close()


    return created    



def update_avail_status(
    avail_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            length_seconds

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



    used_seconds = get_used_seconds(
        avail_id
    )


    length_seconds = avail["length_seconds"]


    if used_seconds <= 0:

        status = "Open"


    elif used_seconds < length_seconds:

        status = "Partial"


    else:

        status = "Filled"



    now = current_timestamp()


    cursor.execute(
        """
        UPDATE avails

        SET
            status = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            status,
            now,
            avail_id
        )
    )


    connection.commit()

    connection.close()


    return status


def list_avails(
    station_id=None,
    air_date=None,
    status="all"
):

    connection = get_connection()

    cursor = connection.cursor()


    query = """
        SELECT
            id,
            station_id,
            air_date,
            start_time,
            length_seconds,
            status,
            notes,
            created_date,
            modified_date

        FROM avails
    """


    conditions = []

    parameters = []


    if station_id:

        conditions.append(
            "station_id = ?"
        )

        parameters.append(
            station_id
        )


    if air_date:

        conditions.append(
            "air_date = ?"
        )

        parameters.append(
            air_date
        )


    if status != "all":

        conditions.append(
            "status = ?"
        )

        parameters.append(
            status
        )


    if conditions:

        query += (
            " WHERE "
            + " AND ".join(conditions)
        )


    query += """
        ORDER BY
            air_date,
            start_time
    """


    cursor.execute(
        query,
        parameters
    )


    avails = cursor.fetchall()


    connection.close()


    return avails



def format_avail(
    avail
):

    output = []


    output.append(
        f"ID: {avail['id']}"
    )


    output.append(
        f"Station ID: {avail['station_id']}"
    )


    output.append(
        f"Date: {avail['air_date']}"
    )


    output.append(
        f"Start Time: {avail['start_time']}"
    )


    output.append(
        f"Length: {avail['length_seconds']} seconds"
    )


    if avail["status"]:

        output.append(
            f"Status: {avail['status']}"
        )


    if avail["notes"]:

        output.append(
            f"Notes: {avail['notes']}"
        )


    output.append(
        f"Created: {avail['created_date']}"
    )


    output.append(
        f"Modified: {avail['modified_date']}"
    )


    return "\n".join(output)
