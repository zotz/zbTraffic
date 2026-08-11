#!/usr/bin/env python3

# File: database/import_customers_csv.py

import csv
import sys

from traffic.database import get_connection
from traffic.customers import add_customer


def get_category_id(category_name):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM categories
        WHERE name = ?
          AND active = 1
        """,
        (
            category_name,
        )
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return row["id"] if hasattr(row, "keys") else row[0]


def import_customers_csv(filename):

    imported = 0

    with open(
        filename,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        required_columns = {
            "company_name",
            "category",
        }

        missing_columns = required_columns - set(reader.fieldnames or [])

        if missing_columns:

            raise ValueError(
                "Missing required CSV columns: "
                + ", ".join(sorted(missing_columns))
            )

        for line_number, row in enumerate(reader, start=2):

            company_name = (
                row.get("company_name") or ""
            ).strip()

            category_name = (
                row.get("category") or ""
            ).strip()

            if not company_name:

                raise ValueError(
                    f"Line {line_number}: "
                    "company_name is required."
                )

            if not category_name:

                raise ValueError(
                    f"Line {line_number}: "
                    "category is required."
                )

            category_id = get_category_id(
                category_name
            )

            if category_id is None:

                raise ValueError(
                    f"Line {line_number}: "
                    f"Unknown category '{category_name}'."
                )

            data = {
                "company_name": company_name,
                "category_id": category_id,
                "address_line1": (
                    row.get("address1") or ""
                ).strip() or None,
                "address_line2": (
                    row.get("address2") or ""
                ).strip() or None,
                "locality": (
                    row.get("city") or ""
                ).strip() or None,
                "administrative_area": (
                    row.get("state") or ""
                ).strip() or None,
                "postal_code": (
                    row.get("postal_code") or ""
                ).strip() or None,
                "country_code": (
                    row.get("country_code") or ""
                ).strip() or None,
                "telephone": (
                    row.get("telephone") or ""
                ).strip() or None,
                "email": (
                    row.get("email") or ""
                ).strip() or None,
            }

            customer_id, errors = add_customer(
                data
            )

            if customer_id is None:

                raise ValueError(
                    f"Line {line_number}: "
                    f"Could not add '{company_name}': "
                    + "; ".join(errors)
                )

            imported += 1

            print(
                f"  Added customer "
                f"{customer_id}: {company_name}"
            )

    return imported


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

