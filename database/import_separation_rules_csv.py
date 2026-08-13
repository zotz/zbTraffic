#!/usr/bin/env python3

#
# database/import_separation_rules_csv.py
#
# Import separation rules from a CSV file.
#
# Categories are identified by name rather than database ID.
#
# Required CSV columns:
#
#     category1
#     category2
#     minimum_minutes
#
# Optional CSV column:
#
#     notes
#

import csv
import sys

from traffic.database import get_connection
from traffic.separation_rules import add_separation_rule


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

    return row["id"] if hasattr(
        row,
        "keys"
    ) else row[0]


def import_separation_rules_csv(filename):

    imported = 0

    with open(
        filename,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        required_columns = {
            "category1",
            "category2",
            "minimum_minutes",
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

            category1_name = (
                row.get("category1") or ""
            ).strip()

            category2_name = (
                row.get("category2") or ""
            ).strip()

            minutes_text = (
                row.get("minimum_minutes") or ""
            ).strip()

            notes = (
                row.get("notes") or ""
            ).strip() or None

            if not category1_name:

                raise ValueError(
                    f"Line {line_number}: "
                    "category1 is required."
                )

            if not category2_name:

                raise ValueError(
                    f"Line {line_number}: "
                    "category2 is required."
                )

            if not minutes_text:

                raise ValueError(
                    f"Line {line_number}: "
                    "minimum_minutes is required."
                )

            try:

                minimum_minutes = int(
                    minutes_text
                )

            except ValueError:

                raise ValueError(
                    f"Line {line_number}: "
                    "minimum_minutes must be "
                    "a whole number."
                )

            if minimum_minutes < 0:

                raise ValueError(
                    f"Line {line_number}: "
                    "minimum_minutes cannot "
                    "be negative."
                )

            category1_id = get_category_id(
                category1_name
            )

            if category1_id is None:

                raise ValueError(
                    f"Line {line_number}: "
                    f"Unknown category "
                    f"'{category1_name}'."
                )

            category2_id = get_category_id(
                category2_name
            )

            if category2_id is None:

                raise ValueError(
                    f"Line {line_number}: "
                    f"Unknown category "
                    f"'{category2_name}'."
                )

            rule_id, errors = add_separation_rule(
                category1_id,
                category2_id,
                minimum_minutes,
                notes
            )

            if rule_id is None:

                raise ValueError(
                    f"Line {line_number}: "
                    f"Could not add separation "
                    f"rule between "
                    f"'{category1_name}' and "
                    f"'{category2_name}': "
                    + "; ".join(errors)
                )

            imported += 1

            print(
                f"  Added separation rule "
                f"{rule_id}: "
                f"{category1_name} / "
                f"{category2_name} = "
                f"{minimum_minutes} minutes"
            )

    return imported


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: "
            "python3 -m "
            "database.import_separation_rules_csv "
            "<csv_file>"
        )

        sys.exit(1)

    filename = sys.argv[1]

    print()
    print(
        "Importing separation rules from:"
    )
    print(
        f"  {filename}"
    )
    print()

    try:

        count = import_separation_rules_csv(
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
        f"Imported {count} separation rules."
    )


if __name__ == "__main__":
    main()
