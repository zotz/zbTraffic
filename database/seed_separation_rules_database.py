#!/usr/bin/env python3

# File: database/seed_separation_rules_database.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp


def seed_separation_rules():

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    separation_rules = [

        (
            2,
            4,
            20
        )

    ]


    for rule in separation_rules:

        cursor.execute(
            """
            INSERT INTO separation_rules
            (
                category1_id,
                category2_id,
                minimum_minutes,
                active,
                created_date,
                modified_date
            )
            VALUES
            (
                ?,
                ?,
                ?,
                1,
                ?,
                ?
            )
            """,
            (
                rule[0],
                rule[1],
                rule[2],
                now,
                now
            )
        )


    connection.commit()

    connection.close()


    print(
        "Separation rules seeded successfully."
    )


if __name__ == "__main__":

    seed_separation_rules()
