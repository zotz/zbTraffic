#!/usr/bin/env python3

#
# database/import_commercials_csv.py
#
# Import commercials from a CSV file.
#
# The CSV identifies customers by company name rather than
# database ID.  Customer IDs are looked up during import.
#
# Category is also optional in the CSV.  If supplied, it must
# match the customer's category.
#

import csv
import sys

from traffic.database import get_connection
from traffic.commercials import add_commercial


def get_customer(customer_name):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            category_id
        FROM customers
        WHERE company_name = ?
        """,
        (
            customer_name,
        )
    )

    row = cursor.fetchone()

    connection.close()

    return row


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


def import_commercials_csv(filename):

    imported = 0

    with open(
        filename,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        required_columns = {
            "customer",
            "title",
            "length_seconds",
            "cart_number",
        }

        missing_columns = (
            required_columns
            - set(reader.fieldnames or [])
        )

        if missing_columns:

            raise ValueError(
                "Missing required CSV columns: "
                + ", ".join(
                    sorted(missing_columns)
                )
            )

        for line_number, row in enumerate(
            reader,
            start=2
        ):

            customer_name = (
                row.get("customer") or ""
            ).strip()

            title = (
                row.get("title") or ""
            ).strip()

            length_text = (
                row.get("length_seconds") or ""
            ).strip()

            cart_number = (
                row.get("cart_number") or ""
            ).strip()

            filename_value = (
                row.get("filename") or ""
            ).strip() or None

            category_name = (
                row.get("category") or ""
            ).strip()

            if not customer_name:

                raise ValueError(
                    f"Line {line_number}: "
                    "customer is required."
                )

            if not title:

                raise ValueError(
                    f"Line {line_number}: "
                    "title is required."
                )

            if not length_text:

                raise ValueError(
                    f"Line {line_number}: "
                    "length_seconds is required."
                )

            try:

                length_seconds = int(
                    length_text
                )

            except ValueError:

                raise ValueError(
                    f"Line {line_number}: "
                    "length_seconds must be "
                    "a whole number."
                )

            if length_seconds <= 0:

                raise ValueError(
                    f"Line {line_number}: "
                    "length_seconds must be "
                    "greater than zero."
                )

            if not cart_number:

                raise ValueError(
                    f"Line {line_number}: "
                    "cart_number is required."
                )

            customer = get_customer(
                customer_name
            )

            if customer is None:

                raise ValueError(
                    f"Line {line_number}: "
                    f"Unknown customer "
                    f"'{customer_name}'."
                )

            if hasattr(customer, "keys"):

                customer_id = customer["id"]
                customer_category_id = (
                    customer["category_id"]
                )

            else:

                customer_id = customer[0]
                customer_category_id = (
                    customer[1]
                )

            category_id = (
                customer_category_id
            )

            if category_name:

                csv_category_id = (
                    get_category_id(
                        category_name
                    )
                )

                if csv_category_id is None:

                    raise ValueError(
                        f"Line {line_number}: "
                        f"Unknown category "
                        f"'{category_name}'."
                    )

                if (
                    customer_category_id is not None
                    and csv_category_id
                    != customer_category_id
                ):

                    raise ValueError(
                        f"Line {line_number}: "
                        f"Category '{category_name}' "
                        f"does not match customer "
                        f"'{customer_name}'."
                    )

                category_id = csv_category_id


            commercial_id, errors = add_commercial(
                customer_id,
                title,
                length_seconds,
                filename_value,
                cart_number,
                category_id
            )

            if commercial_id is None:

                raise ValueError(
                    f"Line {line_number}: "
                    f"Could not add commercial "
                    f"'{title}': "
                    + "; ".join(errors)
                )

            imported += 1

            print(
                f"  Added commercial "
                f"{commercial_id}: "
                f"{title} "
                f"({customer_name})"
            )

    return imported


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: "
            "python3 -m database.import_commercials_csv "
            "<csv_file>"
        )

        sys.exit(1)

    filename = sys.argv[1]

    print()
    print(
        "Importing commercials from:"
    )
    print(
        f"  {filename}"
    )
    print()

    try:

        count = import_commercials_csv(
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
        f"Imported {count} commercials."
    )


if __name__ == "__main__":
    main()

