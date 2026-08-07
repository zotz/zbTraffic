#!/usr/bin/env python3

# File: traffic/contacts.py

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



def validate_contact(
    customer_id,
    first_name,
    last_name,
    job_title=None,
    telephone=None,
    email=None
):

    errors = []


    if not customer_id:

        errors.append(
            "Customer ID is required."
        )


    if not first_name or not first_name.strip():

        errors.append(
            "First name cannot be blank."
        )


    if not last_name or not last_name.strip():

        errors.append(
            "Last name cannot be blank."
        )


    if email:

        email = email.strip()

        if "@" not in email:

            errors.append(
                "Email address does not appear valid."
            )


    if first_name:

        first_name = first_name.strip()


    if last_name:

        last_name = last_name.strip()


    if job_title:

        job_title = job_title.strip()


    if telephone:

        telephone = telephone.strip()


    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "customer_id": customer_id,
        "first_name": first_name,
        "last_name": last_name,
        "job_title": job_title,
        "telephone": telephone,
        "email": email
    }



def add_contact(
    customer_id,
    first_name,
    last_name,
    job_title=None,
    telephone=None,
    email=None
):

    validation = validate_contact(
        customer_id,
        first_name,
        last_name,
        job_title,
        telephone,
        email
    )


    if not validation["valid"]:

        return None, validation["errors"]


    if not customer_exists(
        validation["customer_id"]
    ):

        return None, [
            "Customer not found."
        ]


    now = current_timestamp()


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO contacts
        (
            customer_id,
            first_name,
            last_name,
            job_title,
            telephone,
            email,
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
            validation["first_name"],
            validation["last_name"],
            validation["job_title"],
            validation["telephone"],
            validation["email"],
            now,
            now
        )
    )


    connection.commit()

    contact_id = cursor.lastrowid

    connection.close()


    return contact_id, []



def list_contacts(customer_id=None, status="active"):

    connection = get_connection()

    cursor = connection.cursor()


    query = """
        SELECT
            c.id,
            c.customer_id,
            cu.company_name,
            c.first_name,
            c.last_name,
            c.job_title,
            c.telephone,
            c.email,
            c.active

        FROM contacts c

        JOIN customers cu
            ON c.customer_id = cu.id
    """


    conditions = []

    parameters = []


    if customer_id:

        conditions.append(
            "c.customer_id = ?"
        )

        parameters.append(
            customer_id
        )


    if status == "active":

        conditions.append(
            "c.active = 1"
        )


    elif status == "inactive":

        conditions.append(
            "c.active = 0"
        )


    elif status != "all":

        connection.close()

        raise ValueError(
            "Invalid contact status."
        )


    if conditions:

        query += " WHERE "

        query += " AND ".join(
            conditions
        )


    query += """
        ORDER BY
            c.last_name,
            c.first_name
    """


    cursor.execute(
        query,
        parameters
    )


    contacts = cursor.fetchall()

    connection.close()


    return contacts



def get_contact(contact_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            c.id,
            c.customer_id,
            cu.company_name,
            c.first_name,
            c.last_name,
            c.job_title,
            c.telephone,
            c.email,
            c.active,
            c.created_date,
            c.modified_date

        FROM contacts c

        JOIN customers cu
            ON c.customer_id = cu.id

        WHERE c.id = ?
        """,
        (contact_id,)
    )


    contact = cursor.fetchone()

    connection.close()


    return contact



def update_first_name(contact_id, first_name):

    if not first_name or not first_name.strip():

        return False, [
            "First name cannot be blank."
        ]


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contacts

        SET
            first_name = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            first_name.strip(),
            current_timestamp(),
            contact_id
        )
    )


    connection.commit()

    affected = cursor.rowcount

    connection.close()


    if affected == 0:

        return False, [
            "Contact not found."
        ]


    return True, []



def update_last_name(contact_id, last_name):

    if not last_name or not last_name.strip():

        return False, [
            "Last name cannot be blank."
        ]


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contacts

        SET
            last_name = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            last_name.strip(),
            current_timestamp(),
            contact_id
        )
    )


    connection.commit()

    affected = cursor.rowcount

    connection.close()


    if affected == 0:

        return False, [
            "Contact not found."
        ]


    return True, []



def update_job_title(contact_id, job_title):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contacts

        SET
            job_title = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            job_title.strip() if job_title else None,
            current_timestamp(),
            contact_id
        )
    )


    connection.commit()

    connection.close()


    return True, []



def update_telephone(contact_id, telephone):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contacts

        SET
            telephone = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            telephone.strip() if telephone else None,
            current_timestamp(),
            contact_id
        )
    )


    connection.commit()

    connection.close()


    return True, []



def update_email(contact_id, email):

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
        UPDATE contacts

        SET
            email = ?,
            modified_date = ?

        WHERE id = ?
        """,
        (
            email,
            current_timestamp(),
            contact_id
        )
    )


    connection.commit()

    connection.close()


    return True, []



def deactivate_contact(contact_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contacts

        SET
            active = 0,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            contact_id
        )
    )


    connection.commit()

    affected = cursor.rowcount

    connection.close()


    if affected == 0:

        return False, [
            "Contact not found."
        ]


    return True, []



def activate_contact(contact_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE contacts

        SET
            active = 1,
            modified_date = ?

        WHERE id = ?
        """,
        (
            current_timestamp(),
            contact_id
        )
    )


    connection.commit()

    affected = cursor.rowcount

    connection.close()


    if affected == 0:

        return False, [
            "Contact not found."
        ]


    return True, []



def format_contact(contact, include_status=False):

    output = []


    output.append(
        f"ID: {contact['id']}"
    )

    output.append(
        f"Customer: {contact['company_name']}"
    )

    output.append(
        f"Name: {contact['first_name']} {contact['last_name']}"
    )


    if contact["job_title"]:

        output.append(
            f"Title: {contact['job_title']}"
        )


    output.append(
        f"Telephone: {contact['telephone']}"
    )

    output.append(
        f"Email: {contact['email']}"
    )


    if include_status:

        status = (
            "Active"
            if contact["active"]
            else "Inactive"
        )

        output.append(
            f"Status: {status}"
        )


    return "\n".join(output)
