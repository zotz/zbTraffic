#!/usr/bin/env python3

# File: database/create_database.py

import sqlite3
import os


# Find the project directory
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

# create db tables in this order:
# 01. categories
# 02. stations
# 03. programs
# 04. stopsets
# 05. customers
# 06. contacts
# 07. salespeople
# 08. commercials
# 09. contracts
# 10. contract_items
# 11. contract_item_rules
# 12. avails
# 13. spots
# 14. separation_rules
# 15. users
#

def create_database():

    # Make sure data directory exists
    database_directory = os.path.dirname(DATABASE_NAME)

    os.makedirs(
        database_directory,
        exist_ok=True
    )


    conn = sqlite3.connect(DATABASE_NAME)

    # Enable foreign key enforcement in SQLite
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    cursor = conn.cursor()


    tables = [

    """
    CREATE TABLE IF NOT EXISTS categories (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,
        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS stations (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        call_letters TEXT,
        frequency TEXT,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS programs (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        station_id INTEGER NOT NULL,

        name TEXT NOT NULL,

        description TEXT,

        start_time TEXT,
        end_time TEXT,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(station_id)
            REFERENCES stations(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS stopsets (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        program_id INTEGER NOT NULL,

        name TEXT,

        start_time TEXT,
        end_time TEXT,

        maximum_seconds INTEGER,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(program_id)
            REFERENCES programs(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS customers (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        company_name TEXT NOT NULL,

        address_line1 TEXT,
        address_line2 TEXT,

        locality TEXT,
        administrative_area TEXT,
        postal_code TEXT,
        country_code TEXT,

        telephone TEXT,
        email TEXT,

        category_id INTEGER,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,

        FOREIGN KEY(category_id)
            REFERENCES categories(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS contacts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER NOT NULL,

        first_name TEXT,
        last_name TEXT,

        job_title TEXT,

        telephone TEXT,
        email TEXT,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(customer_id)
            REFERENCES customers(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS salespeople (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        first_name TEXT,
        last_name TEXT,

        telephone TEXT,
        email TEXT,

        commission_rate REAL DEFAULT 0,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS commercials (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER NOT NULL,

        title TEXT NOT NULL,

        length_seconds INTEGER,

        filename TEXT,

        cart_number TEXT,

        category_id INTEGER,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(customer_id)
            REFERENCES customers(id),


        FOREIGN KEY(category_id)
            REFERENCES categories(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS contracts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER NOT NULL,

        salesperson_id INTEGER NOT NULL,

        station_id INTEGER NOT NULL,

        contract_number TEXT NOT NULL DEFAULT '',

        description TEXT NOT NULL DEFAULT '',

        start_date TEXT,
        end_date TEXT,

        status TEXT NOT NULL DEFAULT 'Draft',

        notes TEXT NOT NULL DEFAULT '',

        active INTEGER NOT NULL DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(customer_id)
            REFERENCES customers(id),


        FOREIGN KEY(salesperson_id)
            REFERENCES salespeople(id),


        FOREIGN KEY(station_id)
            REFERENCES stations(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS contract_items (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        contract_id INTEGER NOT NULL,

        commercial_id INTEGER,
        
        commercial_title TEXT NOT NULL DEFAULT '',

        description TEXT NOT NULL DEFAULT '',

        quantity INTEGER NOT NULL DEFAULT 0,

        spot_length_seconds INTEGER NOT NULL DEFAULT 0,

        start_date TEXT,
        end_date TEXT,

        priority INTEGER NOT NULL DEFAULT 1,

        rotation_group TEXT NOT NULL DEFAULT '',

        notes TEXT NOT NULL DEFAULT '',

        active INTEGER NOT NULL DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(contract_id)
            REFERENCES contracts(id),


        FOREIGN KEY(commercial_id)
            REFERENCES commercials(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS contract_item_rules (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        contract_item_id INTEGER NOT NULL,

        days_of_week TEXT,

        start_time TEXT,
        end_time TEXT,

        preferred_program_id INTEGER,

        preferred_stopset_id INTEGER,

        spots_per_day INTEGER DEFAULT 0,

        spots_per_week INTEGER DEFAULT 0,

        allow_news INTEGER DEFAULT 1,

        allow_special_events INTEGER DEFAULT 1,

        active INTEGER DEFAULT 1,

        notes TEXT,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(contract_item_id)
            REFERENCES contract_items(id),


        FOREIGN KEY(preferred_program_id)
            REFERENCES programs(id),


        FOREIGN KEY(preferred_stopset_id)
            REFERENCES stopsets(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS avails
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        station_id INTEGER NOT NULL,
        
        stopset_id INTEGER,

        air_date TEXT NOT NULL,

        start_time TEXT NOT NULL,

        length_seconds INTEGER NOT NULL,

        status TEXT DEFAULT 'Open',

        notes TEXT,

        created_date TEXT,

        modified_date TEXT,

        FOREIGN KEY(station_id)
            REFERENCES stations(id),

        FOREIGN KEY(stopset_id)
            REFERENCES stopsets(id)

    )
    """,


    """
    CREATE TABLE IF NOT EXISTS spots (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        station_id INTEGER NOT NULL,


        -- Optional until contract workflow is implemented.
        contract_item_id INTEGER,


        commercial_id INTEGER,


        -- NULL means the spot has not yet been assigned
        -- to a commercial avail.
        avail_id INTEGER,


        air_date TEXT,

        air_time TEXT,


        -- Lifecycle:
        -- Pending
        -- Scheduled
        -- Exported
        -- Completed
        -- Cancelled

        status TEXT DEFAULT 'Pending',


        actual_air_time TEXT,


        notes TEXT,


        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(station_id)
            REFERENCES stations(id),


        FOREIGN KEY(contract_item_id)
            REFERENCES contract_items(id),


        FOREIGN KEY(commercial_id)
            REFERENCES commercials(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS separation_rules (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        category1_id INTEGER NOT NULL,

        category2_id INTEGER NOT NULL,


        minimum_minutes INTEGER DEFAULT 0,

        active INTEGER DEFAULT 1,

        notes TEXT,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(category1_id)
            REFERENCES categories(id),


        FOREIGN KEY(category2_id)
            REFERENCES categories(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        password_hash TEXT NOT NULL,

        role TEXT,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT
    )
    """

    ]


    for table in tables:
        cursor.execute(table)

    #insert_default_data(
    #    cursor
    #)

    conn.commit()
    conn.close()



if __name__ == "__main__":

    create_database()

    print("Traffic database created:")
    print(DATABASE_NAME)
