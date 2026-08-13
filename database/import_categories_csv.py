#!/usr/bin/env python3

#
# File: database/import_categories_csv.py
#
# Import categories from a CSV file.
#
# Required CSV columns:
#     name
#

import csv
import sys

from traffic.categories import add_category


def import_categories_csv(filename):

    imported = 0

    with open(
        filename,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        required_columns = {
            "name",
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

            name = (
                row.get("name") or ""
            ).strip()

            if not name:

                raise ValueError(
                    f"Line {line_number}: "
                    "name is required."
                )

            category_id, errors = add_category(
                name
            )

            if category_id is None:

                raise ValueError(
                    f"Line {line_number}: "
                    f"Could not add category "
                    f"'{name}': "
                    + "; ".join(errors)
                )

            imported += 1

            print(
                f"  Added category "
                f"{category_id}: "
                f"{name}"
            )

    return imported


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: "
            "python3 -m database.import_categories_csv "
            "<csv_file>"
        )

        sys.exit(1)

    filename = sys.argv[1]

    print()
    print(
        "Importing categories from:"
    )
    print(
        f"  {filename}"
    )
    print()

    try:

        count = import_categories_csv(
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
        f"Imported {count} categories."
    )


if __name__ == "__main__":
    main()
