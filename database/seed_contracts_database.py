# File: database/seed_contracts_database.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp


def seed_contracts():

    connection = get_connection()
    cursor = connection.cursor()


    timestamp = current_timestamp()


    contracts = [

        (
            1,                  # customer_id
            1,                  # salesperson_id (House)
            1,                  # station_id
            "2026-001",         # contract_number
            "Summer Boat Campaign",
            "2026-08-08",
            "2026-08-31",
            "Active",
            "Customer prefers morning drive",
            1,
            timestamp,
            timestamp
        ),

        (
            2,                  # customer_id
            1,                  # salesperson_id (House)
            1,                  # station_id
            "12345",         # contract_number
            "Customer 2 summer",
            "2026-08-08",
            "2026-09-30",
            "Active",
            "Customer prefers Midday",
            1,
            timestamp,
            timestamp
        ),


        (
            3,                  # customer_id
            1,                  # salesperson_id (House)
            1,                  # station_id
            "FX123",         # contract_number
            "Customer 3 summer",
            "2026-08-08",
            "2026-09-30",
            "Active",
            "Customer prefers Afternoon",
            1,
            timestamp,
            timestamp
        )



    ]


    for contract in contracts:

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

                ?, ?, ?, ?, ?,

                ?, ?, ?, ?,

                ?, ?, ?

            )
            """,
            contract
        )


    connection.commit()
    connection.close()


    print(
        "Contracts seeded successfully."
    )



if __name__ == "__main__":

    seed_contracts()
