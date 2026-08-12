#!/usr/bin/env python3

# File: database/seed_database.py

import sqlite3
import os

from traffic.utilities import current_timestamp


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATABASE_NAME = os.path.join(
    BASE_DIR,
    "data",
    "traffic.db"
)


def seed_reference_data():

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    cursor = conn.cursor()

    now = current_timestamp()


    #
    # Categories
    #

    categories = [

        (2, "Automotive"),
        (3, "Restaurant"),
        (4, "Retail"),
        (5, "Political"),
        (6, "PSA"),
        (7, "Real Estate"),
        (8, "Bank/Finance"),
        (9, "Medical/Dental"),
        (10, "Tourism/Hotel"),
        (11, "Telecommunications"),
        (12, "Grocery"),
        (13, "Insurance"),
        (14, "Legal"),

    ]


    cursor.executemany(
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
            ?,
            ?,
            1,
            ?,
            ?
        )
        """,
        [
            (
                category_id,
                name,
                now,
                now
            )
            for category_id, name in categories
        ]
    )


    conn.commit()

    conn.close()


if __name__ == "__main__":

    seed_reference_data()

    print(
        "Reference data loaded:"
    )

    print(
        DATABASE_NAME
    )
