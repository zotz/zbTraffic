#!/usr/bin/env python3

# File: traffic/categories.py

from traffic.database import get_connection
from datetime import datetime


def current_timestamp():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def validate_category(name):

    errors = []


    if not name or not name.strip():

        errors.append(
            "Category name cannot be blank."
        )


    if name:

        name = name.strip()


    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "name": name
    }



def add_category(name):

    validation = validate_category(
        name
    )


    if not validation["valid"]:

        return None, validation["errors"]


    name = validation["name"]


    connection = get_connection()

    cursor = connection.cursor()


    #
    # Check for duplicate category name
    #

    cursor.execute(
        """
        SELECT id

        FROM categories

        WHERE name = ?
        """,
        (name,)
    )


    existing = cursor.fetchone()


    if existing:

        connection.close()

        return None, [
            "Category already exists."
        ]



    cursor.execute(
        """
        INSERT INTO categories
        (
            name,
            active,
            created_date,
            modified_date
        )

        VALUES
        (
            ?,
            1,
            ?,
            ?
        )
        """,
        (
            name,
            current_timestamp(),
            current_timestamp()
        )
    )


    connection.commit()


    category_id = cursor.lastrowid


    connection.close()


    return category_id, []



def list_categories(status="active"):

    connection = get_connection()

    cursor = connection.cursor()


    if status == "active":

        cursor.execute(
            """
            SELECT
                id,
                name,
                active,
                created_date,
                modified_date

            FROM categories

            WHERE active = 1

            ORDER BY name
            """
        )


    elif status == "inactive":

        cursor.execute(
            """
            SELECT
                id,
                name,
                active,
                created_date,
                modified_date

            FROM categories

            WHERE active = 0

            ORDER BY name
            """
        )


    elif status == "all":

        cursor.execute(
            """
            SELECT
                id,
                name,
                active,
                created_date,
                modified_date

            FROM categories

            ORDER BY name
            """
        )


    else:

        connection.close()

        raise ValueError(
            "Invalid category status. Use active, inactive, or all."
        )


    categories = cursor.fetchall()

    connection.close()


    return categories



def get_category(category_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            id,
            name,
            active,
            created_date,
            modified_date

        FROM categories

        WHERE id = ?
        """,
        (category_id,)
    )


    category = cursor.fetchone()


    connection.close()


    return category



def update_name(category_id, name):

    validation = validate_category(
        name
    )


    if not validation["valid"]:

        return False, validation["errors"]


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT id

        FROM categories

        WHERE name = ?
        AND id != ?
        """,
        (
            validation["name"],
            category_id
        )
    )


    existing = cursor.fetchone()


    if existing:

        connection.close()

        return False, [
            "Category already exists."
        ]



    cursor.execute(
        """
        UPDATE categories

        SET
            name = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            validation["name"],
            current_timestamp(),
            category_id
        )
    )


    affected = cursor.rowcount


    connection.commit()

    connection.close()


    if affected == 0:

        return False, [
            "Category not found."
        ]


    return True, []



def deactivate_category(category_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE categories

        SET
            active = 0,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            category_id
        )
    )


    affected = cursor.rowcount


    connection.commit()

    connection.close()


    if affected == 0:

        return False, [
            "Category not found."
        ]


    return True, []



def activate_category(category_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE categories

        SET
            active = 1,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            category_id
        )
    )


    affected = cursor.rowcount


    connection.commit()

    connection.close()


    if affected == 0:

        return False, [
            "Category not found."
        ]


    return True, []



def format_category(category):

    output = []

    output.append(
        f"ID: {category['id']}"
    )

    output.append(
        f"Name: {category['name']}"
    )


    if category["active"]:

        status = "Active"

    else:

        status = "Inactive"


    output.append(
        f"Status: {status}"
    )


    output.append(
        f"Created: {category['created_date']}"
    )

    output.append(
        f"Modified: {category['modified_date']}"
    )


    return "\n".join(output)
