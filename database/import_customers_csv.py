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

            count = 0

            for row in reader:

                category_id = get_category_id(
                    connection,
                    row.get("category", ""),
                )

                customer_id, errors = add_customer(
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

                if errors:

                    print(
                        f"ERROR: {row['company_name']}: "
                        + "; ".join(errors)
                    )

                else:

                    count += 1

        connection.commit()

        return count

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()



def main():

    if len(sys.argv) != 2:

        print(
            "Usage: "
            "python3 -m database.import_customers_csv "
            "<csv_file>"
        )

        sys.exit(1)

    filename = sys.argv[1]

    print()
    print(
        "Importing customers from:"
    )
    print(
        f"  {filename}"
    )
    print()

    try:

        count = import_customers_csv(
            filename
        )

    except FileNotFoundError:

        print(
            f"ERROR: CSV file not found: "
            f"{filename}"
        )

        sys.exit(1)

    except (OSError, ValueError) as error:

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)

    print()
    print(
        f"Imported {count} customers."
    )


if __name__ == "__main__":
    main()
