#!/usr/bin/env python3

# File: traffic/commercials.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp

def validate_customer(company_name, telephone=None, email=None):
    """
    Validate customer data before saving.
    """

    errors = []


    # Company name is required
    if not company_name or not company_name.strip():

        errors.append(
            "Company name cannot be blank."
        )


    # Remove extra spaces
    if company_name:

        company_name = company_name.strip()


    if telephone:

        telephone = telephone.strip()


    if email:

        email = email.strip()


        # Basic email check
        if "@" not in email:

            errors.append(
                "Email address does not appear valid."
            )


    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "company_name": company_name,
        "telephone": telephone,
        "email": email
    }

def add_customer(company_name, telephone=None, email=None):

    validation = validate_customer(
        company_name,
        telephone,
        email
    )


    if not validation["valid"]:

        return None, validation["errors"]


    company_name = validation["company_name"]
    telephone = validation["telephone"]
    email = validation["email"]


    connection = get_connection()

    cursor = connection.cursor()

    now = current_timestamp()

    cursor.execute(
        """
        INSERT INTO customers
        (
            company_name,
            telephone,
            email,
            created_date,
            modified_date
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            company_name,
            telephone,
            email,
            now,
            now,
        )
    )

    connection.commit()

    customer_id = cursor.lastrowid

    connection.close()

    return customer_id, []

def list_customers(
    status="active"
):

    connection = get_connection()

    cursor = connection.cursor()


    if status == "active":

        where_clause = """
            WHERE active = 1
        """


    elif status == "inactive":

        where_clause = """
            WHERE active = 0
        """


    elif status == "all":

        where_clause = ""


    else:

        connection.close()

        raise ValueError(
            "Invalid customer status. Use active, inactive, or all."
        )


    cursor.execute(
        f"""
        SELECT
            id,
            company_name,
            telephone,
            email,
            active

        FROM customers

        {where_clause}

        ORDER BY company_name
        """
    )


    customers = cursor.fetchall()

    connection.close()

    return customers

def get_customer(customer_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            company_name,
            telephone,
            email

        FROM customers

        WHERE id = ?
        """,
        (customer_id,)
    )

    customer = cursor.fetchone()

    connection.close()

    return customer

def update_company_name(customer_id, company_name):

    validation = validate_customer(
        company_name
    )


    if not validation["valid"]:

        return False, validation["errors"]


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE customers

        SET company_name = ?,
        modified_date = ?

        WHERE id = ?
        """,
        (
            validation["company_name"],
            current_timestamp(),
            customer_id,
        )
    )


    connection.commit()

    connection.close()


    return True, []

def update_telephone(customer_id, telephone):

    if telephone:

        telephone = telephone.strip()


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE customers

        SET telephone = ?,
        modified_date = ?

        WHERE id = ?
        """,
        (
            telephone,
            current_timestamp(),
            customer_id,
        )
    )


    connection.commit()

    connection.close()


    return True, []

def update_email(customer_id, email):

    if email:

        email = email.strip()


        if "@" not in email:

            return False, [
                "Email address does not appear valid."
            ]


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE customers

        SET email = ?,
        modified_date = ?

        WHERE id = ?
        """,
        (
            email,
            current_timestamp(),
            customer_id,
        )
    )


    connection.commit()

    connection.close()


    return True, []

def deactivate_customer(customer_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE customers

        SET
            active = 0,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            customer_id,
        )
    )

    connection.commit()

    affected = cursor.rowcount

    connection.close()

    if affected == 0:

        return False, [
            "Customer not found."
        ]

    return True, []

def activate_customer(customer_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE customers

        SET
            active = 1,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            customer_id,
        )
    )

    connection.commit()

    affected = cursor.rowcount

    connection.close()

    if affected == 0:

        return False, [
            "Customer not found."
        ]

    return True, []


def format_customer(customer, include_status=False):

    output = []

    output.append(
        f"ID: {customer[0]}"
    )

    output.append(
        f"Company: {customer[1]}"
    )

    output.append(
        f"Telephone: {customer[2]}"
    )

    output.append(
        f"Email: {customer[3]}"
    )


    if include_status:

        if customer[4]:

            status = "Active"

        else:

            status = "Inactive"


        output.append(
            f"Status: {status}"
        )


    return "\n".join(output)

