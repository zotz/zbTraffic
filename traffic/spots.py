# File: traffic/spots.py

# Return values:
# success
# not_found
# not_allowed
# already_done
# error

from traffic.database import get_connection
from traffic.utilities import current_timestamp


def add_spot(
    station_id,
    commercial_id,
    air_date,
    air_time,
    status=None,
    contract_item_id=None,
    notes=None
):

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    cursor.execute(
        """
        INSERT INTO spots
        (
            station_id,
            commercial_id,
            contract_item_id,
            air_date,
            air_time,
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
            ?,
            ?
        )
        """,
        (
            station_id,
            commercial_id,
            contract_item_id,
            air_date,
            air_time,
            status,
            notes,
            now,
            now
        )
    )


    connection.commit()

    spot_id = cursor.lastrowid

    connection.close()


    return spot_id



def get_spot(
    spot_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT

            spots.*,

            commercials.cart_number,
            commercials.title,
            commercials.length_seconds,

            customers.company_name

        FROM spots

        JOIN commercials
            ON spots.commercial_id = commercials.id

        JOIN customers
            ON commercials.customer_id = customers.id

        WHERE spots.id = ?

        """,
        (
            spot_id,
        )
    )


    spot = cursor.fetchone()

    connection.close()


    return spot



def list_spots(
    status=None
):

    connection = get_connection()

    cursor = connection.cursor()


    if status:

        cursor.execute(
            """
            SELECT *
            FROM spots
            WHERE status = ?
            ORDER BY
                air_date,
                air_time
            """,
            (
                status,
            )
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM spots
            ORDER BY
                air_date,
                air_time
            """
        )


    spots = cursor.fetchall()

    connection.close()


    return spots

def list_spots_with_details(
    status=None
):

    connection = get_connection()

    cursor = connection.cursor()


    if status:

        cursor.execute(
            """
            SELECT
                spots.*,

                commercials.cart_number,
                commercials.title,
                commercials.length_seconds,

                customers.company_name

            FROM spots

            JOIN commercials
                ON spots.commercial_id = commercials.id

            JOIN customers
                ON commercials.customer_id = customers.id

            WHERE spots.status = ?

            ORDER BY
                spots.air_date,
                spots.air_time
            """,
            (
                status,
            )
        )

    else:

        cursor.execute(
            """
            SELECT
                spots.*,

                commercials.cart_number,
                commercials.title,
                commercials.length_seconds,

                customers.company_name

            FROM spots

            JOIN commercials
                ON spots.commercial_id = commercials.id

            JOIN customers
                ON commercials.customer_id = customers.id

            ORDER BY
                spots.air_date,
                spots.air_time
            """
        )


    spots = cursor.fetchall()

    connection.close()


    return spots

def update_spot(
    spot_id,
    commercial_id=None,
    air_date=None,
    air_time=None,
    status=None,
    notes=None
):

    connection = get_connection()

    cursor = connection.cursor()

    current_spot = get_spot(
        spot_id
    )


    if current_spot is None:

        connection.close()

        return 0

    if commercial_id is not None:

        if current_spot["status"] != "Scheduled":

            connection.close()

            raise ValueError(
                "Commercial cannot be changed after export"
            )

    now = current_timestamp()


    fields = []
    values = []


    if air_date is not None:

        fields.append(
            "air_date = ?"
        )

        values.append(
            air_date
        )


    if commercial_id is not None:

        fields.append(
            "commercial_id = ?"
        )

        values.append(
            commercial_id
        )


    if air_time is not None:

        fields.append(
            "air_time = ?"
        )

        values.append(
            air_time
        )


    if status is not None:

        fields.append(
            "status = ?"
        )

        values.append(
            status
        )


    if notes is not None:

        fields.append(
            "notes = ?"
        )

        values.append(
            notes
        )


    fields.append(
        "modified_date = ?"
    )

    values.append(
        now
    )


    values.append(
        spot_id
    )


    sql = f"""
        UPDATE spots
        SET
            {', '.join(fields)}
        WHERE id = ?
    """


    cursor.execute(
        sql,
        values
    )


    connection.commit()

    changed = cursor.rowcount

    connection.close()


    return changed



def cancel_spot(
    spot_id
):

    spot = get_spot(
        spot_id
    )


    if spot is None:

        return "not_found"


    if spot["status"] == "Cancelled":

        return "already_done"


    if spot["status"] == "Completed":

        return "not_allowed"


    result = update_spot(
        spot_id,
        status="Cancelled"
    )


    if result:

        return "success"


    return "error"




def complete_spot(
    spot_id,
    actual_air_time=None
):

    spot = get_spot(
        spot_id
    )


    if spot is None:

        return "not_found"


    if spot["status"] == "Completed":

        return "already_done"


    if spot["status"] == "Cancelled":

        return "not_allowed"


    if actual_air_time is None:

        actual_air_time = current_timestamp()


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE spots

        SET
            status = ?,
            actual_air_time = ?,
            modified_date = ?

        WHERE id = ?

        """,
        (
            "Completed",
            actual_air_time,
            current_timestamp(),
            spot_id
        )
    )


    connection.commit()

    changed = cursor.rowcount

    connection.close()


    if changed:

        return "success"


    return "error"



def delete_spot(
    spot_id
):

    spot = get_spot(
        spot_id
    )

    if spot is None:

        return "not_found"


    if spot["status"] != "Scheduled":

        return "not_allowed"


    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE
        FROM spots
        WHERE id = ?
        """,
        (
            spot_id,
        )
    )

    connection.commit()

    deleted = cursor.rowcount

    connection.close()


    if deleted:

        return "success"

    return "error"

def format_spot(
    spot
):

    return (
        f"ID: {spot['id']}\n"
        f"Date: {spot['air_date']}\n"
        f"Time: {spot['air_time']}\n"
        f"Customer: {spot['company_name']}\n"
        f"Cart: {spot['cart_number']}\n"
        f"Title: {spot['title']}\n"
        f"Length: {spot['length_seconds']} seconds\n"
        f"Status: {spot['status']}\n"
        f"Notes: {spot['notes']}"
    )

def export_spot(
    spot_id
):

    spot = get_spot(
        spot_id
    )


    if spot is None:

        return "not_found"


    if spot["status"] == "Exported":

        return "already_done"


    if spot["status"] in (
        "Cancelled",
        "Completed"
    ):

        return "not_allowed"


    result = update_spot(
        spot_id,
        status="Exported"
    )


    if result:

        return "success"


    return "error"

def list_spots_by_date(
    air_date
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT

            spots.*,

            commercials.cart_number,
            commercials.title,
            commercials.length_seconds,

            customers.company_name

        FROM spots


        LEFT JOIN commercials
            ON spots.commercial_id = commercials.id


        LEFT JOIN customers
            ON commercials.customer_id = customers.id


        WHERE spots.air_date = ?


        ORDER BY
            spots.air_time

        """,
        (
            air_date,
        )
    )


    spots = cursor.fetchall()

    connection.close()


    return spots

def count_spots_for_contract_item(
    contract_item_id
):
    """
    Return the number of spots already generated
    for a contract item.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS count

        FROM spots

        WHERE contract_item_id = ?

        AND status != 'Cancelled'
        """,
        (
            contract_item_id,
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result["count"]


def find_duplicate_spots():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT

            station_id,
            commercial_id,
            air_date,
            air_time,

            COUNT(*) AS duplicate_count


        FROM spots


        GROUP BY

            station_id,
            commercial_id,
            air_date,
            air_time


        HAVING COUNT(*) > 1


        ORDER BY

            air_date,
            air_time

        """
    )


    duplicates = cursor.fetchall()

    connection.close()


    return duplicates

