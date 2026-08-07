#!/usr/bin/env python3

# File: commands/spot_add.py

from traffic.spots import add_scheduled_spot
from traffic.database import get_connection


def commercial_exists(commercial_id):

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

    result = cursor.fetchone()

    connection.close()

    return result is not None



def main():

    print("Add Spot")
    print("------------------")


    station_id = input(
        "Station ID: "
    ).strip()


    commercial_id = input(
        "Commercial ID: "
    ).strip()


    if not commercial_id.isdigit():

        print(
            "Commercial ID must be a number."
        )

        return


    commercial_id = int(
        commercial_id
    )


    if not commercial_exists(commercial_id):

        print(
            f"Commercial {commercial_id} does not exist."
        )

        return



    air_date = input(
        "Air Date (YYYY-MM-DD): "
    ).strip()


    air_time = input(
        "Air Time (HH:MM:SS): "
    ).strip()


    notes = input(
        "Notes (optional): "
    ).strip()


    if notes == "":

        notes = None



    spot_id = add_spot(
        station_id,
        commercial_id,
        air_date,
        air_time,
        notes=notes
    )


    print()

    print(
        "Spot created:"
    )

    print(
        spot_id
    )



if __name__ == "__main__":

    main()
