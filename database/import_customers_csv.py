#!/usr/bin/env python3

# File: database/import_customers_csv.py

import csv
import sys

from traffic.database import get_connection
from traffic.customers import add_customer

def get_category_id(connection, category_name):
    """Return the category id for a category name."""

    category_name = category_name.strip()

    if not category_name:
        return None

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM categories
        WHERE name = ?
        """,
        (category_name,),
    )

    row = cursor.fetchone()

    if row is None:
        raise ValueError(f"Unknown category: {category_name}")

    return row["id"]


def import_customers_csv(csv_file):
    """Import customers from a CSV file."""

    connection = get_connection()

    try:
        with open(csv_file, newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            for row in reader:
                category_id = get_category_id(
                    connection,
                    row.get("category", ""),
                )

                add_customer(
                    connection=connection,
                    company_name=row["company_name"],
                    address_line1=row["address_line1"],
                    address_line2=row["address_line2"],
                    locality=row["locality"],
                    administrative_area=row["administrative_area"],
                    postal_code=row["postal_code"],
                    country_code=row["country_code"],
                    telephone=row["telephone"],
                    email=row["email"],
                    category_id=category_id,
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
