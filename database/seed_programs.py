#!/usr/bin/env python3

# File: database/seed_programs.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp


def seed_programs():

    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()


    station_id = 1


    programs = [

        (
            station_id,
            "Morning Show",
            "Morning programming block",
            "06:00",
            "10:00"
        ),

        (
            station_id,
            "Midday Show",
            "Midday programming block",
            "10:00",
            "15:00"
        ),

        (
            station_id,
            "Afternoon Drive",
            "Afternoon programming block",
            "15:00",
            "19:00"
        )

    ]


    for program in programs:

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
                program[0],
                program[1],
                program[2],
                program[3],
                program[4],
                now,
                now
            )
        )


    connection.commit()

    connection.close()


    print(
        "Programs seeded successfully."
    )



if __name__ == "__main__":

    seed_programs()
