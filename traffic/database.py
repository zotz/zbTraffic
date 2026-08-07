#!/usr/bin/env python3

# File: traffic/database.py

import sqlite3
import os


def get_database_path():

    # Find the project root directory
    project_root = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    database_path = os.path.join(
        project_root,
        "data",
        "traffic.db"
    )

    return database_path



def get_connection():

    database_path = get_database_path()

    connection = sqlite3.connect(database_path)

    # Allows us to access columns by name later
    connection.row_factory = sqlite3.Row

    # Enforce foreign key constraints in SQLite
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection



def test_connection():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )

    tables = cursor.fetchall()

    connection.close()

    return tables
