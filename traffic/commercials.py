#!/usr/bin/env python3

# File: traffic/commercials.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp

def customer_exists(customer_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id

        FROM customers

        WHERE id = ?
        """,
        (customer_id,)
    )

    customer = cursor.fetchone()

    connection.close()

    return customer is not None



def category_exists(category_id):

    if category_id is None:

        return True


    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id

        FROM categories

        WHERE id = ?
        """,
        (category_id,)
    )

    category = cursor.fetchone()

    connection.close()

    return category is not None

def validate_commercial(
    customer_id,
    title,
    length_seconds,
    filename=None,
    cart_number=None,
    category_id=None
):
    """
    Validate commercial data before saving.
    """

    errors = []


    # customer_id is required
    if customer_id is None:

        errors.append(
            "Customer ID is required."
        )


    # title is required
    if not title or not title.strip():

        errors.append(
            "Title cannot be blank."
        )


    # Remove extra spaces
    if title:

        title = title.strip()


    if filename:

        filename = filename.strip()


    if cart_number:

        cart_number = cart_number.strip()


    # length_seconds must be a positive integer
    if not isinstance(length_seconds, int):

        errors.append(
            "Length must be an integer number of seconds."
        )

    elif length_seconds <= 0:

        errors.append(
            "Length must be greater than zero."
        )


    return {

        "valid": len(errors) == 0,

        "errors": errors,

        "customer_id": customer_id,

        "title": title,

        "length_seconds": length_seconds,

        "filename": filename,

        "cart_number": cart_number,

        "category_id": category_id

    }


def add_commercial(
    customer_id,
    title,
    length_seconds,
    filename=None,
    cart_number=None,
    category_id=None
):

    validation = validate_commercial(
        customer_id,
        title,
        length_seconds,
        filename,
        cart_number,
        category_id
    )


    if not validation["valid"]:

        return None, validation["errors"]

    if not customer_exists(
        validation["customer_id"]
    ):

        return None, [
            "Customer not found."
        ]


    if not category_exists(
        validation["category_id"]
    ):

        return None, [
            "Category not found."
        ]

    now = current_timestamp()


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO commercials
        (
            customer_id,
            title,
            length_seconds,
            filename,
            cart_number,
            category_id,
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
            ?,
            1,
            ?,
            ?
        )
        """,
        (
            validation["customer_id"],
            validation["title"],
            validation["length_seconds"],
            validation["filename"],
            validation["cart_number"],
            validation["category_id"],
            now,
            now,
        )
    )


    connection.commit()

    commercial_id = cursor.lastrowid

    connection.close()


    return commercial_id, []


def list_commercials(
    status="active"
):

    connection = get_connection()

    cursor = connection.cursor()


    if status == "active":

        where_clause = """
            WHERE commercials.active = 1
        """


    elif status == "inactive":

        where_clause = """
            WHERE commercials.active = 0
        """


    elif status == "all":

        where_clause = ""


    else:

        connection.close()

        raise ValueError(
            "Invalid commercial status. Use active, inactive, or all."
        )


    cursor.execute(
        f"""
        SELECT
            commercials.id,
            commercials.customer_id,

            customers.company_name,

            commercials.title,
            commercials.length_seconds,
            commercials.filename,
            commercials.cart_number,
            commercials.category_id,

            commercials.active,
            commercials.created_date,
            commercials.modified_date

        FROM commercials

        JOIN customers
        ON commercials.customer_id = customers.id

        {where_clause}

        ORDER BY
            customers.company_name,
            commercials.title
        """
    )


    commercials = cursor.fetchall()

    connection.close()

    return commercials

def format_commercial(commercial):

    output = []

    output.append(
        f"ID: {commercial['id']}"
    )

    output.append(
        f"Customer: {commercial['company_name']} ({commercial['customer_id']})"
    )

    output.append(
        f"Title: {commercial['title']}"
    )

    output.append(
        f"Length: {commercial['length_seconds']} seconds"
    )

    output.append(
        f"Filename: {commercial['filename']}"
    )

    output.append(
        f"Cart Number: {commercial['cart_number']}"
    )

    output.append(
        f"Category ID: {commercial['category_id']}"
    )


    if commercial["active"]:

        status = "Active"

    else:

        status = "Inactive"


    output.append(
        f"Status: {status}"
    )

    output.append(
        f"Created: {commercial['created_date']}"
    )

    output.append(
        f"Modified: {commercial['modified_date']}"
    )

    return "\n".join(output)

def format_commercial_summary(
    commercial
):

    output = []

    output.append(
        f"ID: {commercial['id']}"
    )

    output.append(
        f"Customer: {commercial['company_name']} ({commercial['customer_id']})"
    )

    output.append(
        f"Title: {commercial['title']}"
    )

    output.append(
        f"Length: {commercial['length_seconds']} seconds"
    )

    output.append(
        f"Cart Number: {commercial['cart_number']}"
    )


    if commercial["active"]:

        status = "Active"

    else:

        status = "Inactive"


    output.append(
        f"Status: {status}"
    )


    return "\n".join(output)


def get_commercial(commercial_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            commercials.id,
            commercials.customer_id,
            customers.company_name,
            commercials.title,
            commercials.length_seconds,
            commercials.filename,
            commercials.cart_number,
            commercials.category_id,
            commercials.active,
            commercials.created_date,
            commercials.modified_date

        FROM commercials

        JOIN customers
        ON commercials.customer_id = customers.id

        WHERE commercials.id = ?
        """,
        (commercial_id,)
    )

    commercial = cursor.fetchone()

    connection.close()

    return commercial

def update_title(commercial_id, title):

    errors = []


    if not title or not title.strip():

        errors.append(
            "Title cannot be blank."
        )


    if errors:

        return False, errors


    title = title.strip()


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE commercials

        SET
            title = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            title,
            current_timestamp(),
            commercial_id
        )
    )


    affected = cursor.rowcount


    connection.commit()

    connection.close()


    if affected == 0:

        return False, [
            "Commercial not found."
        ]


    return True, []

def update_length(commercial_id, length_seconds):

    errors = []


    try:

        length_seconds = int(length_seconds)

    except ValueError:

        errors.append(
            "Length must be an integer number of seconds."
        )


    if not errors:

        if length_seconds <= 0:

            errors.append(
                "Length must be greater than zero."
            )


    if errors:

        return False, errors


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE commercials

        SET
            length_seconds = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            length_seconds,
            current_timestamp(),
            commercial_id
        )
    )


    affected = cursor.rowcount


    connection.commit()

    connection.close()


    if affected == 0:

        return False, [
            "Commercial not found."
        ]


    return True, []

def update_filename(commercial_id, filename):

    if filename:

        filename = filename.strip()


    else:

        filename = None


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE commercials

        SET
            filename = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            filename,
            current_timestamp(),
            commercial_id
        )
    )


    affected = cursor.rowcount


    connection.commit()

    connection.close()


    if affected == 0:

        return False, [
            "Commercial not found."
        ]


    return True, []

def update_cart_number(commercial_id, cart_number):

    if cart_number:

        cart_number = cart_number.strip()


    else:

        cart_number = None


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE commercials

        SET
            cart_number = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            cart_number,
            current_timestamp(),
            commercial_id
        )
    )


    affected = cursor.rowcount


    connection.commit()

    connection.close()


    if affected == 0:

        return False, [
            "Commercial not found."
        ]


    return True, []

def deactivate_commercial(commercial_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE commercials

        SET
            active = 0,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            commercial_id
        )
    )


    affected = cursor.rowcount


    connection.commit()

    connection.close()


    if affected == 0:

        return False, [
            "Commercial not found."
        ]


    return True, []

def activate_commercial(commercial_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE commercials

        SET
            active = 1,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            commercial_id
        )
    )


    affected = cursor.rowcount


    connection.commit()

    connection.close()


    if affected == 0:

        return False, [
            "Commercial not found."
        ]


    return True, []

def update_category(
        commercial_id,
        category_id
):

    if category_id is None:

        return False, [
            "Category ID is required."
        ]


    connection = get_connection()

    cursor = connection.cursor()


    #
    # Does the commercial exist?
    #

    cursor.execute(
        """
        SELECT id

        FROM commercials

        WHERE id = ?
        """,
        (commercial_id,)
    )

    commercial = cursor.fetchone()


    if commercial is None:

        connection.close()

        return False, [
            "Commercial not found."
        ]


    #
    # Does the category exist?
    #

    cursor.execute(
        """
        SELECT id

        FROM categories

        WHERE id = ?
        """,
        (category_id,)
    )

    category = cursor.fetchone()


    if category is None:

        connection.close()

        return False, [
            "Category not found."
        ]


    #
    # Perform the update.
    #

    cursor.execute(
        """
        UPDATE commercials

        SET
            category_id = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            category_id,
            current_timestamp(),
            commercial_id
        )
    )


    connection.commit()

    connection.close()


    return True, []


