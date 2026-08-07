# File: traffic/assignment.py

from traffic.database import (
    get_connection
)

from traffic.avails import (
    get_avail,
    get_remaining_seconds,
    update_avail_status
)

from traffic.utilities import (
    current_timestamp,
    normalize_time
)


def assign_spot_to_avail(
    spot_id,
    avail_id
):

    connection = get_connection()

    cursor = connection.cursor()


    #
    # Get the spot
    #

    cursor.execute(
        """
        SELECT
            id,
            commercial_id,
            status,
            avail_id

        FROM spots

        WHERE id = ?
        """,
        (
            spot_id,
        )
    )


    spot = cursor.fetchone()


    if spot is None:

        connection.close()

        return False, [
            "Spot not found."
        ]



    #
    # Get the avail
    #

    avail = get_avail(
        avail_id
    )


    if avail is None:

        connection.close()

        return False, [
            "Avail not found."
        ]



    #
    # Get commercial length
    #

    cursor.execute(
        """
        SELECT
            length_seconds

        FROM commercials

        WHERE id = ?
        """,
        (
            spot["commercial_id"],
        )
    )


    commercial = cursor.fetchone()


    if commercial is None:

        connection.close()

        return False, [
            "Commercial not found."
        ]



    #
    # Check available time
    #

    remaining_seconds = get_remaining_seconds(
        avail_id
    )


    if commercial["length_seconds"] > remaining_seconds:

        connection.close()

        return False, [
            "Commercial will not fit in avail."
        ]



    #
    # Assign spot
    #

    now = current_timestamp()


    cursor.execute(
        """
        UPDATE spots

        SET
            avail_id = ?,
            air_date = ?,
            air_time = ?,
            status = 'Scheduled',
            modified_date = ?

        WHERE id = ?
        """,
        (
            avail_id,
            avail["air_date"],
            normalize_time(
                avail["start_time"]
            ),
            now,
            spot_id
        )
    )


    connection.commit()

    update_avail_status(
        avail_id
    )

    connection.close()



    return True, None


def remove_spot_from_avail(spot_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            avail_id,
            status

        FROM spots

        WHERE id = ?
        """,
        (
            spot_id,
        )
    )

    spot = cursor.fetchone()


    if spot is None:

        connection.close()

        return False, [
            "Spot not found."
        ]


    if spot["avail_id"] is None:

        connection.close()

        return False, [
            "Spot is not assigned to an avail."
        ]


    avail_id = spot["avail_id"]


    now = current_timestamp()


    cursor.execute(
        """
        UPDATE spots

        SET
            avail_id = NULL,
            air_date = NULL,
            air_time = NULL,
            status = 'Pending',
            modified_date = ?

        WHERE id = ?
        """,
        (
            now,
            spot_id
        )
    )


    connection.commit()


    update_avail_status(
        avail_id
    )


    connection.close()


    return True, None



