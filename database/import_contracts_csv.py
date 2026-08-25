#!/usr/bin/env python3

#
# database/import_contracts_csv.py
#
# Import contracts from a CSV file.
#

import csv
import sys

from traffic.database import get_connection
from traffic.contracts import add_contract


def get_customer_id(cursor, company_name):

    cursor.execute(
        """
        SELECT id
        FROM customers
        WHERE company_name = ?
        """,
        (
            company_name,
        )
    )

    row = cursor.fetchone()

    if row is None:
        raise ValueError(
            f"Customer not found: {company_name}"
        )

    return row[0]


def get_salesperson_id(cursor, first_name):

    cursor.execute(
        """
        SELECT id
        FROM salespeople
        WHERE first_name = ?
        """,
        (
            first_name,
        )
    )

    row = cursor.fetchone()

    if row is None:
        raise ValueError(
            f"Salesperson not found: {first_name}"
        )

    return row[0]


def get_station_id(cursor, station_name):

    cursor.execute(
        """
        SELECT id
        FROM stations
        WHERE name = ?
        """,
        (
            station_name,
        )
    )

    row = cursor.fetchone()

    if row is None:
        raise ValueError(
            f"Station not found: {station_name}"
        )

    return row[0]


def import_contracts_csv(filename):

    print(
        f"Importing contracts from:\n"
        f"  {filename}\n"
    )

    connection = get_connection()
    cursor = connection.cursor()

    count = 0

    try:

        with open(
            filename,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as csvfile:

            reader = csv.DictReader(csvfile)

            required_columns = [
                "customer",
                "salesperson",
                "station",
                "contract_number",
                "description",
                "start_date",
                "end_date",
                "status",
                "notes",
                "payment_timing",
                "payment_terms_days",
            ]

            if reader.fieldnames is None:

                raise ValueError(
                    "CSV file has no header row"
                )

            missing_columns = [
                column
                for column in required_columns
                if column not in reader.fieldnames
            ]

            if missing_columns:

                raise ValueError(
                    "Missing required CSV columns: "
                    + ", ".join(missing_columns)
                )

            for row_number, row in enumerate(
                reader,
                start=2
            ):

                customer = row["customer"].strip()
                salesperson = row["salesperson"].strip()
                station = row["station"].strip()

                contract_number = (
                    row["contract_number"].strip()
                )

                description = (
                    row["description"].strip()
                )

                start_date = (
                    row["start_date"].strip()
                    or None
                )

                end_date = (
                    row["end_date"].strip()
                    or None
                )

                status = (
                    row["status"].strip()
                    or "Draft"
                )

                notes = (
                    row["notes"].strip()
                )

                payment_timing = row["payment_timing"].strip()
                try:
                    payment_terms_days = int(
                        row["payment_terms_days"].strip()
                    )
                except ValueError:
                    raise ValueError(
                        f"Row {row_number}: "
                        "payment_terms_days must be an integer"
                    )





                if not customer:

                    raise ValueError(
                        f"Row {row_number}: "
                        "customer is required"
                    )

                if not salesperson:

                    raise ValueError(
                        f"Row {row_number}: "
                        "salesperson is required"
                    )

                if not station:

                    raise ValueError(
                        f"Row {row_number}: "
                        "station is required"
                    )

                if not description:

                    raise ValueError(
                        f"Row {row_number}: "
                        "description is required"
                    )

                customer_id = get_customer_id(
                    cursor,
                    customer
                )

                salesperson_id = get_salesperson_id(
                    cursor,
                    salesperson
                )

                station_id = get_station_id(
                    cursor,
                    station
                )

                contract_id = add_contract(
                    customer_id,
                    salesperson_id,
                    station_id,
                    contract_number,
                    description,
                    start_date,
                    end_date,
                    status,
                    notes,
                    payment_timing=payment_timing,
                    payment_terms_days=payment_terms_days,
                )

                count += 1

                print(
                    f"  Added contract {contract_id}: "
                    f"{description}"
                )

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()

    print()
    print(
        f"Imported {count} contracts."
    )

    return count


def main():

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "  python3 -m "
            "database.import_contracts_csv "
            "<csv_file>"
        )

        sys.exit(1)

    filename = sys.argv[1]

    import_contracts_csv(
        filename
    )


if __name__ == "__main__":
    main()

