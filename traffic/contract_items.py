# File: traffic/contract_items.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp


def validate_contract_item(
    contract_id,
    commercial_id
):
    """
    Validate contract and commercial references.
    """

    connection = get_connection()
    cursor = connection.cursor()


    #
    # Validate contract
    #

    cursor.execute(
        """
        SELECT id
        FROM contracts
        WHERE id = ?
        """,
        (
            contract_id,
        )
    )

    if cursor.fetchone() is None:

        connection.close()

        raise ValueError(
            f"Contract ID {contract_id} does not exist"
        )


    #
    # Validate commercial only if supplied
    #

    if commercial_id is not None:

        cursor.execute(
            """
            SELECT id
            FROM commercials
            WHERE id = ?
            """,
            (
                commercial_id,
            )
        )

        if cursor.fetchone() is None:

            connection.close()

            raise ValueError(
                f"Commercial ID {commercial_id} does not exist"
            )


    connection.close()


def add_contract_item(
    contract_id,
    commercial_id=None,
    commercial_title="",
    description="",
    quantity=0,
    spot_length_seconds=None,
    start_date=None,
    end_date=None,
    priority=1,
    rotation_group="",
    notes=""
):
    """
    Add a contract item.
    """


    validate_contract_item(
        contract_id,
        commercial_id=None
    )


    connection = get_connection()
    cursor = connection.cursor()


    #
    # If spot length was not supplied,
    # try to copy it from the commercial
    #

    if spot_length_seconds is None:

        if commercial_id is not None:

            cursor.execute(
                """
                SELECT
                    length_seconds,
                    title
                FROM commercials
                WHERE id = ?
                """,
                (
                    commercial_id,
                )
            )

            commercial = cursor.fetchone()


            if commercial is not None:

                spot_length_seconds = commercial["length_seconds"]
                
                if commercial_title == "":
                
                    commercial_title = commercial["title"]



    #
    # A contract item must have a spot length
    #

    if spot_length_seconds is None:

        connection.close()

        raise ValueError(
            "Spot length is required for a contract item"
        )



    timestamp = current_timestamp()


    cursor.execute(
        """
        INSERT INTO contract_items (

            contract_id,

            commercial_id,
            
            commercial_title,

            description,

            quantity,

            spot_length_seconds,

            start_date,
            end_date,

            priority,

            rotation_group,

            notes,

            active,

            created_date,
            modified_date

        )


        VALUES (

            ?, ?, ?,

            ?, ?,

            ?,

            ?, ?,

            ?,

            ?,

            ?,

            1,

            ?, ?

        )
        """,
        (

            contract_id,

            commercial_id,
            
            commercial_title,

            description,

            quantity,

            spot_length_seconds,

            start_date,
            end_date,

            priority,

            rotation_group,

            notes,

            timestamp,
            timestamp

        )
    )


    contract_item_id = cursor.lastrowid


    connection.commit()
    connection.close()


    return contract_item_id



def get_contract_item(
    contract_item_id
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *

        FROM contract_items

        WHERE id = ?

        """,
        (
            contract_item_id,
        )
    )


    contract_item = cursor.fetchone()


    connection.close()


    return contract_item



def list_contract_items(
    contract_id=None,
    active_only=True
):

    connection = get_connection()
    cursor = connection.cursor()


    if contract_id is not None:

        if active_only:

            cursor.execute(
                """
                SELECT *

                FROM contract_items

                WHERE contract_id = ?
                AND active = 1

                ORDER BY id

                """,
                (
                    contract_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT *

                FROM contract_items

                WHERE contract_id = ?

                ORDER BY id

                """,
                (
                    contract_id,
                )
            )


    else:

        if active_only:

            cursor.execute(
                """
                SELECT *

                FROM contract_items

                WHERE active = 1

                ORDER BY id

                """
            )

        else:

            cursor.execute(
                """
                SELECT *

                FROM contract_items

                ORDER BY id

                """
            )


    contract_items = cursor.fetchall()


    connection.close()


    return contract_items



def update_description(
    contract_item_id,
    description
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE contract_items

        SET
            description = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            description,
            current_timestamp(),
            contract_item_id
        )
    )

    connection.commit()
    connection.close()



def update_quantity(
    contract_item_id,
    quantity
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE contract_items

        SET
            quantity = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            quantity,
            current_timestamp(),
            contract_item_id
        )
    )

    connection.commit()
    connection.close()



def update_spot_length_seconds(
    contract_item_id,
    spot_length_seconds
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE contract_items

        SET
            spot_length_seconds = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            spot_length_seconds,
            current_timestamp(),
            contract_item_id
        )
    )

    connection.commit()
    connection.close()



def update_dates(
    contract_item_id,
    start_date,
    end_date
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE contract_items

        SET
            start_date = ?,
            end_date = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            start_date,
            end_date,
            current_timestamp(),
            contract_item_id
        )
    )

    connection.commit()
    connection.close()



def update_priority(
    contract_item_id,
    priority
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE contract_items

        SET
            priority = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            priority,
            current_timestamp(),
            contract_item_id
        )
    )

    connection.commit()
    connection.close()



def update_rotation_group(
    contract_item_id,
    rotation_group
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE contract_items

        SET
            rotation_group = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            rotation_group,
            current_timestamp(),
            contract_item_id
        )
    )

    connection.commit()
    connection.close()



def update_notes(
    contract_item_id,
    notes
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE contract_items

        SET
            notes = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            notes,
            current_timestamp(),
            contract_item_id
        )
    )

    connection.commit()
    connection.close()

def update_commercial_id(
    contract_item_id,
    commercial_id
):

    #
    # Allow removing a commercial assignment
    #

    if commercial_id is not None:

        connection = get_connection()
        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT id
            FROM commercials
            WHERE id = ?
            """,
            (
                commercial_id,
            )
        )


        if cursor.fetchone() is None:

            connection.close()

            raise ValueError(
                f"Commercial ID {commercial_id} does not exist"
            )


        connection.close()



    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contract_items

        SET
            commercial_id = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            commercial_id,
            current_timestamp(),
            contract_item_id
        )
    )


    connection.commit()
    connection.close()



def update_commercial_title(
    contract_item_id,
    commercial_title
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contract_items

        SET
            commercial_title = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            commercial_title,
            current_timestamp(),
            contract_item_id
        )
    )


    connection.commit()
    connection.close()

def deactivate_contract_item(
    contract_item_id
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contract_items

        SET
            active = 0,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            contract_item_id
        )
    )


    connection.commit()
    connection.close()



def activate_contract_item(
    contract_item_id
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contract_items

        SET
            active = 1,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            contract_item_id
        )
    )


    connection.commit()
    connection.close()


