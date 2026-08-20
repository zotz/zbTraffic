# File: database/create_initial_records.py
# was...
# File: database/initialize_records.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp



def create_initial_records(cursor):

    now = current_timestamp()


    #
    # Default category
    #

    cursor.execute(
        """
        INSERT OR IGNORE INTO categories
        (
            id,
            name,
            active,
            created_date,
            modified_date
        )
        VALUES
        (
            1,
            'Uncategorized',
            1,
            ?,
            ?
        )
        """,
        (
            now,
            now
        )
    )


    #
    # Default station
    #

    cursor.execute(
        """
        INSERT OR IGNORE INTO stations
        (
            id,
            name,
            call_letters,
            active,
            created_date,
            modified_date
        )
        VALUES
        (
            1,
            'Default Station',
            '',
            1,
            ?,
            ?
        )
        """,
        (
            now,
            now
        )
    )


    #
    # Default program
    #

    cursor.execute(
        """
        INSERT OR IGNORE INTO programs
        (
            id,
            station_id,
            name,
            description,
            active,
            created_date,
            modified_date
        )
        VALUES
        (
            1,
            1,
            'Default Program',
            'Default scheduling program',
            1,
            ?,
            ?
        )
        """,
        (
            now,
            now
        )
    )


    #
    # Default stopset
    #

    cursor.execute(
        """
        INSERT OR IGNORE INTO stopsets
        (
            id,
            program_id,
            name,
            active,
            created_date,
            modified_date
        )
        VALUES
        (
            1,
            1,
            'Default Stopset',
            1,
            ?,
            ?
        )
        """,
        (
            now,
            now
        )
    )


    #
    # Default salesperson
    #

    cursor.execute(
        """
        INSERT OR IGNORE INTO salespeople
        (
            id,
            first_name,
            last_name,
            commission_rate,
            active,
            created_date,
            modified_date
        )
        VALUES
        (
            1,
            'House',
            '',
            0,
            1,
            ?,
            ?
        )
        """,
        (
            now,
            now
        )
    )



def main():

    connection = get_connection()

    cursor = connection.cursor()


    create_initial_records(
        cursor
    )


    connection.commit()

    connection.close()


    print(
        "Initial records created."
    )



if __name__ == "__main__":

    main()
