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


def unschedule_contract_item(
    contract_item_id
):
    """
    Unschedule an entire contract item.

    This is deliberately strict.

    The operation succeeds only when:

    - The contract item exists.
    - The number of non-cancelled spots for the CI equals
      the CI quantity.
    - Every spot for the CI is Pending or Scheduled.
    - No spot is linked to an invoice item.

    If all checks pass, all spots for the CI are deleted
    in a single database transaction.

    Returns:

        {
            "status": "success",
            "contract_item_id": ...,
            "quantity": ...,
            "spots_found": ...,
            "scheduled_deleted": ...,
            "pending_deleted": ...,
            "total_deleted": ...
        }

    Or:

        {
            "status": "not_found",
            ...
        }

        {
            "status": "not_allowed",
            "reason": "...",
            ...
        }

        {
            "status": "error",
            "reason": "..."
        }
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        #
        # Lock the database for the duration of the
        # validation and delete operation.
        #

        connection.execute(
            "BEGIN IMMEDIATE"
        )


        #
        # 1. Find the contract item and its quantity.
        #

        cursor.execute(
            """
            SELECT
                id,
                quantity
            FROM contract_items
            WHERE id = ?
            """,
            (
                contract_item_id,
            )
        )

        contract_item = cursor.fetchone()


        if contract_item is None:

            connection.rollback()

            return {
                "status": "not_found",
                "contract_item_id": contract_item_id
            }


        quantity = contract_item["quantity"]


        #
        # 2. Find ALL spots belonging to the CI.
        #
        # Deliberately do not exclude Cancelled here.
        # The strict operation needs to know about every
        # spot associated with the CI.
        #

        cursor.execute(
            """
            SELECT
                id,
                status
            FROM spots
            WHERE contract_item_id = ?
            ORDER BY id
            """,
            (
                contract_item_id,
            )
        )

        spots = cursor.fetchall()


        spots_found = len(spots)


        #
        # 3. Spot count must exactly match CI quantity.
        #

        if spots_found != quantity:

            connection.rollback()

            return {
                "status": "not_allowed",
                "reason": "spot_count_mismatch",
                "contract_item_id": contract_item_id,
                "quantity": quantity,
                "spots_found": spots_found
            }


        #
        # 4. Every spot must be Pending or Scheduled.
        #

        invalid_spots = [
            spot
            for spot in spots
            if spot["status"] not in (
                "Pending",
                "Scheduled"
            )
        ]


        if invalid_spots:

            connection.rollback()

            return {
                "status": "not_allowed",
                "reason": "spot_status_not_reversible",
                "contract_item_id": contract_item_id,
                "quantity": quantity,
                "spots_found": spots_found,
                "invalid_spot_ids": [
                    spot["id"]
                    for spot in invalid_spots
                ],
                "invalid_statuses": [
                    spot["status"]
                    for spot in invalid_spots
                ]
            }


        #
        # 5. Make sure none of the spots is associated
        # with an invoice item.
        #

        cursor.execute(
            """
            SELECT
                iis.spot_id
            FROM invoice_item_spots iis
            JOIN spots s
                ON s.id = iis.spot_id
            WHERE s.contract_item_id = ?
            """,
            (
                contract_item_id,
            )
        )

        invoice_links = cursor.fetchall()


        if invoice_links:

            connection.rollback()

            return {
                "status": "not_allowed",
                "reason": "spot_linked_to_invoice",
                "contract_item_id": contract_item_id,
                "quantity": quantity,
                "spots_found": spots_found,
                "invoice_linked_spot_ids": [
                    row["spot_id"]
                    for row in invoice_links
                ]
            }


        #
        # Everything has passed validation.
        #

        scheduled_count = sum(
            1
            for spot in spots
            if spot["status"] == "Scheduled"
        )

        pending_count = sum(
            1
            for spot in spots
            if spot["status"] == "Pending"
        )


        #
        # 6. Delete the spots.
        #

        cursor.execute(
            """
            DELETE FROM spots
            WHERE contract_item_id = ?
            """,
            (
                contract_item_id,
            )
        )

        deleted_count = cursor.rowcount


        #
        # 7. Verify the expected number was actually deleted.
        #

        if deleted_count != spots_found:

            connection.rollback()

            return {
                "status": "error",
                "reason": "delete_count_mismatch",
                "contract_item_id": contract_item_id,
                "quantity": quantity,
                "spots_found": spots_found,
                "deleted_count": deleted_count
            }


        #
        # 8. Commit.
        #

        connection.commit()


        return {
            "status": "success",
            "contract_item_id": contract_item_id,
            "quantity": quantity,
            "spots_found": spots_found,
            "scheduled_deleted": scheduled_count,
            "pending_deleted": pending_count,
            "total_deleted": deleted_count
        }


    except Exception as error:

        connection.rollback()

        return {
            "status": "error",
            "reason": str(error),
            "contract_item_id": contract_item_id
        }


    finally:

        connection.close()



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

