# traffic/contracts.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp


def validate_contract(
    customer_id,
    salesperson_id,
    station_id
):
    """
    Validate foreign keys before adding a contract.
    """

    connection = get_connection()
    cursor = connection.cursor()


    # Validate customer

    cursor.execute(
        """
        SELECT id
        FROM customers
        WHERE id = ?
        """,
        (
            customer_id,
        )
    )

    if cursor.fetchone() is None:
        connection.close()
        raise ValueError(
            f"Customer ID {customer_id} does not exist"
        )


    # Validate salesperson

    cursor.execute(
        """
        SELECT id
        FROM salespeople
        WHERE id = ?
        """,
        (
            salesperson_id,
        )
    )

    if cursor.fetchone() is None:
        connection.close()
        raise ValueError(
            f"Salesperson ID {salesperson_id} does not exist"
        )


    # Validate station

    cursor.execute(
        """
        SELECT id
        FROM stations
        WHERE id = ?
        """,
        (
            station_id,
        )
    )

    if cursor.fetchone() is None:
        connection.close()
        raise ValueError(
            f"Station ID {station_id} does not exist"
        )


    connection.close()


def add_contract(
    customer_id,
    salesperson_id,
    station_id,
    contract_number="",
    description="",
    start_date=None,
    end_date=None,
    status="Draft",
    notes=""
):
    """
    Add a new contract.
    """

    validate_contract(
        customer_id,
        salesperson_id,
        station_id
    )


    connection = get_connection()
    cursor = connection.cursor()


    timestamp = current_timestamp()


    cursor.execute(
        """
        INSERT INTO contracts (

            customer_id,
            salesperson_id,
            station_id,

            contract_number,
            description,

            start_date,
            end_date,

            status,

            notes,

            active,

            created_date,
            modified_date

        )

        VALUES (

            ?, ?, ?,

            ?, ?,

            ?, ?,

            ?,

            ?,

            1,

            ?, ?

        )
        """,
        (
            customer_id,
            salesperson_id,
            station_id,

            contract_number,
            description,

            start_date,
            end_date,

            status,

            notes,

            timestamp,
            timestamp
        )
    )


    contract_id = cursor.lastrowid


    connection.commit()
    connection.close()


    return contract_id


def get_contract(contract_id):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM contracts
        WHERE id = ?
        """,
        (
            contract_id,
        )
    )


    contract = cursor.fetchone()


    connection.close()


    return contract


def get_contract_with_details(
    contract_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT

            contracts.*,

            customers.company_name,

            stations.name AS station_name

        FROM contracts


        JOIN customers
            ON contracts.customer_id = customers.id


        JOIN stations
            ON contracts.station_id = stations.id


        WHERE contracts.id = ?

        """,
        (
            contract_id,
        )
    )


    contract = cursor.fetchone()


    connection.close()


    return contract


def list_contracts(active_only=True):

    connection = get_connection()
    cursor = connection.cursor()


    if active_only:

        cursor.execute(
            """
            SELECT *
            FROM contracts
            WHERE active = 1
            ORDER BY id
            """
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM contracts
            ORDER BY id
            """
        )


    contracts = cursor.fetchall()


    connection.close()


    return contracts


def update_contract_description(
    contract_id,
    description
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contracts

        SET
            description = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            description,
            current_timestamp(),
            contract_id
        )
    )


    connection.commit()
    connection.close()



def update_contract_number(
    contract_id,
    contract_number
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contracts

        SET
            contract_number = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            contract_number,
            current_timestamp(),
            contract_id
        )
    )


    connection.commit()
    connection.close()



def update_contract_dates(
    contract_id,
    start_date,
    end_date
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contracts

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
            contract_id
        )
    )


    connection.commit()
    connection.close()



def update_contract_status(
    contract_id,
    status
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contracts

        SET
            status = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            status,
            current_timestamp(),
            contract_id
        )
    )


    connection.commit()
    connection.close()



def update_contract_notes(
    contract_id,
    notes
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contracts

        SET
            notes = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            notes,
            current_timestamp(),
            contract_id
        )
    )


    connection.commit()
    connection.close()



def deactivate_contract(
    contract_id
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contracts

        SET
            active = 0,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            contract_id
        )
    )


    connection.commit()
    connection.close()



def activate_contract(
    contract_id
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contracts

        SET
            active = 1,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            contract_id
        )
    )


    connection.commit()
    connection.close()




