#!/usr/bin/env python3

# File: database/import_tax_rates.py

import csv
import os
import sys
from datetime import datetime

from traffic.database import get_connection


REQUIRED_COLUMNS = {"name", "rate", "effective_date"}


def parse_integer(value, field_name):
    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} is required")

    try:
        return int(value)
    except ValueError:
        raise ValueError(f"{field_name} must be an integer")


def parse_date(value, field_name):
    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} is required")

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"{field_name} must be in YYYY-MM-DD format"
        )

    return value


def import_tax_rates_csv(csv_path):
    conn = get_connection()
    cursor = conn.cursor()

    imported = 0
    errors = 0

    try:
        with open(
            csv_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                raise ValueError("CSV file has no header row")

            missing = REQUIRED_COLUMNS - set(reader.fieldnames)

            if missing:
                raise ValueError(
                    "Missing required columns: "
                    + ", ".join(sorted(missing))
                )

            for row_number, row in enumerate(reader, start=2):
                try:
                    name = row["name"].strip()

                    if not name:
                        raise ValueError("name is required")

                    rate = parse_integer(row["rate"], "rate")

                    if rate < 0:
                        raise ValueError("rate must be >= 0")

                    effective_date = parse_date(
                        row["effective_date"],
                        "effective_date"
                    )

                    cursor.execute(
                        """
                        INSERT INTO tax_rates (
                            name,
                            rate,
                            effective_date
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            name,
                            rate,
                            effective_date,
                        )
                    )

                    imported += 1

                except Exception as e:
                    errors += 1
                    print(
                        f"ERROR row {row_number}: {e}"
                    )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    print(f"Imported: {imported}")
    print(f"Errors:   {errors}")

    return imported, errors


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python3 -m database.import_tax_rates_csv "
            "<csv_file>"
        )
        sys.exit(1)

    csv_path = sys.argv[1]

    if not os.path.isfile(csv_path):
        print(f"ERROR: File not found: {csv_path}")
        sys.exit(1)

    print(f"Importing tax rates from: {csv_path}")

    try:
        imported, errors = import_tax_rates_csv(csv_path)

        if errors:
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()