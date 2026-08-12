# database/import_contract_item_rules_csv.py

import csv
import os
import sys

from traffic.database import get_connection
from traffic.contract_item_rules import add_contract_item_rule


def find_contract_item(
    cursor,
    contract_number,
    commercial_title
):
    """
    Find a contract item by contract number
    and commercial title.
    """

    cursor.execute(
        """
        SELECT
            contract_items.id
        FROM contract_items

        JOIN contracts
            ON contract_items.contract_id = contracts.id

        WHERE contracts.contract_number = ?
        AND contract_items.commercial_title = ?
        """,
        (
            contract_number,
            commercial_title
        )
    )

    rows = cursor.fetchall()

    if len(rows) == 0:
        return None

    if len(rows) > 1:
        raise ValueError(
            f"Multiple contract items found for "
            f"contract '{contract_number}' and "
            f"commercial '{commercial_title}'"
        )

    return rows[0]["id"]


def parse_integer(
    value,
    field_name,
    default=0
):
    """
    Convert a CSV value to an integer.
    """

    value = value.strip()

    if value == "":
        return default

    try:
        return int(value)

    except ValueError:
        raise ValueError(
            f"Invalid {field_name}: '{value}'"
        )


def parse_boolean(
    value,
    field_name,
    default=1
):
    """
    Convert a CSV value to 0 or 1.

    Accepted values:

        1
        0
        yes
        no
        true
        false
        y
        n
        t
        f
    """

    value = value.strip().lower()

    if value == "":
        return default

    if value in (
        "1",
        "yes",
        "true",
        "y",
        "t"
    ):
        return 1

    if value in (
        "0",
        "no",
        "false",
        "n",
        "f"
    ):
        return 0

    raise ValueError(
        f"Invalid {field_name}: '{value}'"
    )


def import_contract_item_rules_csv(
    csv_file
):
    """
    Import contract item scheduling rules
    from a CSV file.
    """

    connection = get_connection()
    cursor = connection.cursor()

    imported = 0
    errors = 0

    try:

        with open(
            csv_file,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            required_columns = [
                "contract",
                "commercial",
                "days_of_week",
                "start_time",
                "end_time",
                "preferred_program",
                "preferred_stopset",
                "spots_per_day",
                "spots_per_week",
                "allow_news",
                "allow_special_events",
                "notes"
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
                    "Missing CSV columns: "
                    + ", ".join(missing_columns)
                )

            for row_number, row in enumerate(
                reader,
                start=2
            ):

                try:

                    contract_number = (
                        row["contract"].strip()
                    )

                    commercial_title = (
                        row["commercial"].strip()
                    )

                    days_of_week = (
                        row["days_of_week"].strip()
                    )

                    start_time = (
                        row["start_time"].strip()
                        or None
                    )

                    end_time = (
                        row["end_time"].strip()
                        or None
                    )

                    preferred_program = (
                        row["preferred_program"].strip()
                    )

                    preferred_stopset = (
                        row["preferred_stopset"].strip()
                    )

                    notes = (
                        row["notes"].strip()
                    )

                    if not contract_number:

                        raise ValueError(
                            "Contract number is empty"
                        )

                    if not commercial_title:

                        raise ValueError(
                            "Commercial title is empty"
                        )

                    #
                    # Find contract item
                    #

                    contract_item_id = (
                        find_contract_item(
                            cursor,
                            contract_number,
                            commercial_title
                        )
                    )

                    if contract_item_id is None:

                        raise ValueError(
                            f"Contract item not found: "
                            f"'{contract_number}' / "
                            f"'{commercial_title}'"
                        )

                    #
                    # Program
                    #

                    preferred_program_id = None

                    if preferred_program:

                        try:
                            preferred_program_id = int(
                                preferred_program
                            )

                        except ValueError:

                            cursor.execute(
                                """
                                SELECT id
                                FROM programs
                                WHERE name = ?
                                """,
                                (
                                    preferred_program,
                                )
                            )

                            program = cursor.fetchone()

                            if program is None:

                                raise ValueError(
                                    f"Program "
                                    f"'{preferred_program}' "
                                    f"does not exist"
                                )

                            preferred_program_id = (
                                program["id"]
                            )

                    #
                    # Stopset
                    #

                    preferred_stopset_id = None

                    if preferred_stopset:

                        try:
                            preferred_stopset_id = int(
                                preferred_stopset
                            )

                        except ValueError:

                            cursor.execute(
                                """
                                SELECT id
                                FROM stopsets
                                WHERE name = ?
                                """,
                                (
                                    preferred_stopset,
                                )
                            )

                            stopset = cursor.fetchone()

                            if stopset is None:

                                raise ValueError(
                                    f"Stopset "
                                    f"'{preferred_stopset}' "
                                    f"does not exist"
                                )

                            preferred_stopset_id = (
                                stopset["id"]
                            )

                    #
                    # Numeric fields
                    #

                    spots_per_day = parse_integer(
                        row["spots_per_day"],
                        "spots_per_day",
                        0
                    )

                    spots_per_week = parse_integer(
                        row["spots_per_week"],
                        "spots_per_week",
                        0
                    )

                    #
                    # Boolean fields
                    #

                    allow_news = parse_boolean(
                        row["allow_news"],
                        "allow_news",
                        1
                    )

                    allow_special_events = parse_boolean(
                        row["allow_special_events"],
                        "allow_special_events",
                        1
                    )

                    #
                    # Add rule
                    #

                    rule_id = add_contract_item_rule(
                        contract_item_id=contract_item_id,
                        days_of_week=days_of_week,
                        start_time=start_time,
                        end_time=end_time,
                        preferred_program_id=(
                            preferred_program_id
                        ),
                        preferred_stopset_id=(
                            preferred_stopset_id
                        ),
                        spots_per_day=spots_per_day,
                        spots_per_week=spots_per_week,
                        allow_news=allow_news,
                        allow_special_events=(
                            allow_special_events
                        ),
                        notes=notes
                    )

                    print(
                        f"  Added rule {rule_id}: "
                        f"{contract_number} / "
                        f"{commercial_title}"
                    )

                    imported += 1

                except Exception as error:

                    print(
                        f"  ERROR on CSV row "
                        f"{row_number}: "
                        f"{error}"
                    )

                    errors += 1

    finally:

        connection.close()

    return imported, errors


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: "
            "python3 -m database.import_contract_item_rules_csv "
            "<csv_file>"
        )

        sys.exit(1)

    csv_file = sys.argv[1]

    if not os.path.isfile(csv_file):

        print(
            f"CSV file not found: {csv_file}"
        )

        sys.exit(1)

    print()
    print(
        "Importing contract item rules from:"
    )
    print(
        f"  {csv_file}"
    )
    print()

    imported, errors = (
        import_contract_item_rules_csv(
            csv_file
        )
    )

    print()
    print(
        f"Imported {imported} contract item rules."
    )

    if errors:

        print(
            f"Encountered {errors} errors."
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
