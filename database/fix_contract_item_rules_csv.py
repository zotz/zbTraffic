# database/fix_contract_item_rules_csv.py

"""
Automatically fix contract item rule CSV problems reported by
check_contract_item_rules_csv.py.

The checker performs the rule analysis and writes:

    <csv filename>.problems.json

For example:

    contract_item_rules_big.csv
    contract_item_rules_big.csv.problems.json

This fixer reads that report and uses the information in it to
identify the rows requiring correction.

For preferred-stopset problems, the fixer selects the eligible
stopset whose start time is closest to the originally preferred
stopset.

The original CSV is never modified.

Usage:

    python3 -m database.fix_contract_item_rules_csv \
        database/data/contract_item_rules_big.csv \
        --auto

Output:

    database/data/fixed_contract_item_rules_big.csv
"""

import argparse
import csv
import json
import os
import sys

from traffic.database import get_connection


def parse_arguments():

    parser = argparse.ArgumentParser(
        description=(
            "Automatically fix contract item rule CSV problems "
            "reported by the checker."
        )
    )

    parser.add_argument(
        "csv_file",
        help="Contract item rules CSV file"
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically fix supported problems"
    )

    parser.add_argument(
        "--report",
        default=None,
        help=(
            "Checker report file. "
            "Defaults to <csv_file>.problems.json"
        )
    )

    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Output CSV filename. "
            "Defaults to fixed_<original filename>"
        )
    )

    return parser.parse_args()


def default_report_filename(csv_file):

    return csv_file + ".problems.json"


def default_output_filename(csv_file):

    directory = os.path.dirname(csv_file)
    filename = os.path.basename(csv_file)

    return os.path.join(
        directory,
        "fixed_" + filename
    )


def load_report(report_file):

    try:

        with open(
            report_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except FileNotFoundError:

        raise ValueError(
            f"Checker report does not exist: {report_file}"
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Checker report is not valid JSON: {error}"
        )


def time_to_seconds(value):

    """
    Convert HH:MM or HH:MM:SS to seconds since midnight.
    """

    parts = value.split(":")

    if len(parts) == 2:

        hours, minutes = parts

        seconds = 0

    elif len(parts) == 3:

        hours, minutes, seconds = parts

    else:

        raise ValueError(
            f"Invalid time value: {value}"
        )

    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
    )


def find_closest_stopset(
    cursor,
    problem
):

    """
    Find an eligible stopset inside the valid preference window.

    The checker has already determined:

        valid_start_time
        valid_end_time
        stopset_id

    The fixer therefore does not repeat the program/rule
    compatibility analysis.

    It looks for stopsets belonging to the preferred program
    whose complete stopset interval falls within the valid
    preference window.

    The closest stopset is selected based on the distance between
    its start time and the originally preferred stopset start time.
    """

    program_id = problem["program_id"]
    original_stopset_id = problem["stopset_id"]

    valid_start = time_to_seconds(
        problem["valid_start_time"]
    )

    valid_end = time_to_seconds(
        problem["valid_end_time"]
    )

    original_start = time_to_seconds(
        problem["stopset_start_time"]
    )


    cursor.execute(
        """
        SELECT
            id,
            name,
            start_time,
            end_time

        FROM stopsets

        WHERE program_id = ?
          AND active = 1

        ORDER BY start_time, id
        """,
        (
            program_id,
        )
    )

    stopsets = cursor.fetchall()


    candidates = []


    for stopset in stopsets:

        if not stopset["start_time"]:
            continue

        if not stopset["end_time"]:
            continue


        stopset_start = time_to_seconds(
            stopset["start_time"]
        )

        stopset_end = time_to_seconds(
            stopset["end_time"]
        )


        #
        # The entire stopset must fit inside the valid
        # preference window.
        #

        if stopset_start < valid_start:
            continue

        if stopset_end > valid_end:
            continue


        #
        # Distance from the originally preferred stopset.
        #

        distance = abs(
            stopset_start - original_start
        )


        candidates.append(
            (
                distance,
                stopset_start,
                stopset["id"],
                stopset["name"],
                stopset["start_time"],
                stopset["end_time"]
            )
        )


    if not candidates:

        return None


    #
    # Sort by:
    #
    #   1. closest start time
    #   2. earliest start time
    #   3. lowest ID
    #

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2]
        )
    )


    return candidates[0]


def fix_csv(
    csv_file,
    report_file,
    output_file
):

    report = load_report(
        report_file
    )


    problems = report.get(
        "problems"
    )

    if problems is None:

        raise ValueError(
            "Checker report does not contain a 'problems' section"
        )


    #
    # Read the original CSV.
    #

    with open(
        csv_file,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:

            raise ValueError(
                "CSV file has no header row"
            )

        fieldnames = list(
            reader.fieldnames
        )

        rows = list(reader)


    #
    # Index the checker results by CSV row number.
    #

    problems_by_row = {}

    for problem in problems:

        csv_row = problem.get(
            "csv_row"
        )

        if csv_row is not None:

            problems_by_row[csv_row] = problem


    connection = get_connection()
    cursor = connection.cursor()


    changes = []
    unsupported = []


    try:

        for csv_row_number, row in enumerate(
            rows,
            start=2
        ):

            problem = problems_by_row.get(
                csv_row_number
            )

            if problem is None:

                continue


            problem_type = problem.get(
                "problem"
            )


            #
            # Currently we automatically support only
            # preferred-stopset problems.
            #

            if problem_type != (
                "preferred_stopset_outside_valid_window"
            ):

                unsupported.append(
                    (
                        csv_row_number,
                        problem_type
                    )
                )

                continue


            #
            # Make sure the CSV still contains the value
            # that the checker analyzed.
            #

            current_stopset = row[
                "preferred_stopset"
            ].strip()


            expected_stopset = problem[
                "preferred_stopset"
            ]


            if current_stopset != expected_stopset:

                raise ValueError(
                    f"CSV row {csv_row_number}: "
                    "preferred_stopset changed since "
                    "the checker ran "
                    f"(expected '{expected_stopset}', "
                    f"found '{current_stopset}')"
                )


            #
            # Find the closest valid stopset.
            #
            # This does NOT repeat the checker analysis.
            # The checker already supplied the valid window.
            #

            replacement = find_closest_stopset(
                cursor,
                problem
            )


            if replacement is None:

                unsupported.append(
                    (
                        csv_row_number,
                        "no eligible stopset "
                        "inside valid window"
                    )
                )

                continue


            (
                distance,
                stopset_start,
                new_stopset_id,
                new_stopset_name,
                new_stopset_start,
                new_stopset_end
            ) = replacement


            #
            # Do not replace a value with itself.
            #

            if new_stopset_name == current_stopset:

                continue


            row[
                "preferred_stopset"
            ] = new_stopset_name


            changes.append(
                {
                    "csv_row": csv_row_number,
                    "contract": problem["contract"],
                    "commercial": problem["commercial"],
                    "old_stopset": current_stopset,
                    "new_stopset": new_stopset_name,
                    "old_stopset_id": problem["stopset_id"],
                    "new_stopset_id": new_stopset_id,
                    "old_stopset_start": problem[
                        "stopset_start_time"
                    ],
                    "new_stopset_start": new_stopset_start,
                    "new_stopset_end": new_stopset_end,
                    "valid_start": problem[
                        "valid_start_time"
                    ],
                    "valid_end": problem[
                        "valid_end_time"
                    ]
                }
            )


    finally:

        connection.close()


    #
    # Write the corrected CSV.
    #

    with open(
        output_file,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(rows)


    return changes, unsupported


def main():

    args = parse_arguments()


    if not args.auto:

        print(
            "No changes made."
        )

        print()

        print(
            "Use --auto to create a corrected CSV."
        )

        return


    csv_file = args.csv_file


    if not os.path.exists(csv_file):

        print(
            f"ERROR: CSV file does not exist: {csv_file}",
            file=sys.stderr
        )

        sys.exit(1)


    report_file = (
        args.report
        if args.report is not None
        else default_report_filename(
            csv_file
        )
    )


    output_file = (
        args.output
        if args.output is not None
        else default_output_filename(
            csv_file
        )
    )


    print(
        "Fixing contract item rules from:"
    )

    print(
        f"  {csv_file}"
    )

    print()

    print(
        "Using checker report:"
    )

    print(
        f"  {report_file}"
    )

    print()

    print(
        "Writing corrected CSV to:"
    )

    print(
        f"  {output_file}"
    )

    print()


    try:

        changes, unsupported = fix_csv(
            csv_file,
            report_file,
            output_file
        )

    except ValueError as error:

        print(
            f"ERROR: {error}",
            file=sys.stderr
        )

        sys.exit(1)


    if changes:

        print(
            "Automatic fixes:"
        )

        print()


        for change in changes:

            print(
                f"CSV row {change['csv_row']}: "
                f"{change['contract']} / "
                f"{change['commercial']}"
            )

            print(
                f"  Preferred stopset:"
            )

            print(
                f"    {change['old_stopset']} "
                f"({change['old_stopset_start']})"
            )

            print(
                f"    -> "
                f"{change['new_stopset']} "
                f"({change['new_stopset_start']}-"
                f"{change['new_stopset_end']})"
            )

            print(
                f"  Valid window: "
                f"{change['valid_start']}-"
                f"{change['valid_end']}"
            )

            print()


    else:

        print(
            "No automatic fixes were made."
        )

        print()


    if unsupported:

        print(
            "Problems not automatically fixed:"
        )

        print()


        for row_number, problem_type in unsupported:

            print(
                f"  CSV row {row_number}: "
                f"{problem_type}"
            )

        print()


    print(
        f"Automatic fixes made: {len(changes)}"
    )

    print(
        f"Problems not fixed:     {len(unsupported)}"
    )

    print()

    print(
        "The original CSV was not modified."
    )

    print(
        "Review the corrected CSV before replacing the original."
    )


if __name__ == "__main__":

    main()
