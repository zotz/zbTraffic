# database/check_contract_item_rules_csv.py

"""
Check contract item scheduling rules in a CSV file.

The checker validates:

1. The preferred program exists.
2. The preferred stopset exists.
3. The preferred stopset belongs to the preferred program.
4. The rule time window overlaps the preferred program window.
5. The preferred stopset fits completely inside the intersection
   of the rule window and preferred program window.

A JSON report is also written containing the results of the
analysis.  The fixer utility can consume this report so that
the timing analysis does not have to be repeated.

Example:

    python3 -m database.check_contract_item_rules_csv \
        database/data/contract_item_rules_big.csv

Optional:

    --report database/data/contract_item_rules_big.problems.json
"""

import argparse
import csv
import json
import os

from traffic.database import get_connection


def time_to_seconds(value):
    """
    Convert HH:MM or HH:MM:SS to seconds after midnight.
    """

    if not value:
        return None

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


def seconds_to_time(value):
    """
    Convert seconds after midnight to HH:MM:SS.
    """

    hours = value // 3600
    minutes = (value % 3600) // 60
    seconds = value % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def get_intersection(
    start1,
    end1,
    start2,
    end2
):
    """
    Return the intersection of two time ranges.

    Returns:

        (start, end)

    or None when there is no overlap.
    """

    start = max(start1, start2)
    end = min(end1, end2)

    if start >= end:
        return None

    return start, end


def stopset_fits(
    stopset_start,
    stopset_end,
    window_start,
    window_end
):
    """
    Return True if the entire stopset lies inside
    the supplied window.
    """

    return (
        stopset_start >= window_start
        and stopset_end <= window_end
    )


def load_database_data(connection):
    """
    Load programs and stopsets needed by the checker.
    """

    cursor = connection.cursor()


    #
    # Programs
    #

    cursor.execute(
        """
        SELECT
            id,
            name,
            start_time,
            end_time
        FROM programs
        WHERE active = 1
        ORDER BY id
        """
    )

    programs_by_name = {}

    for row in cursor.fetchall():

        programs_by_name[row["name"]] = row


    #
    # Stopsets
    #

    cursor.execute(
        """
        SELECT
            id,
            program_id,
            name,
            start_time,
            end_time
        FROM stopsets
        WHERE active = 1
        ORDER BY id
        """
    )

    stopsets_by_name = {}

    for row in cursor.fetchall():

        stopsets_by_name[row["name"]] = row


    return (
        programs_by_name,
        stopsets_by_name
    )


def make_problem(
    row_number,
    row,
    problem,
    details=None
):
    """
    Create one machine-readable problem record.
    """

    result = {
        "csv_row": row_number,

        "contract": row["contract"].strip(),

        "commercial": row["commercial"].strip(),

        "preferred_program": (
            row["preferred_program"].strip()
        ),

        "preferred_stopset": (
            row["preferred_stopset"].strip()
        ),

        "problem": problem
    }


    if details:
        result.update(details)


    return result


def check_contract_item_rules_csv(
    csv_file,
    report_file
):
    """
    Check contract item scheduling rules.

    Returns True if all rows are valid.
    """

    print(
        "Checking contract item rules from:"
    )

    print(
        csv_file
    )

    print()


    connection = get_connection()

    (
        programs_by_name,
        stopsets_by_name
    ) = load_database_data(
        connection
    )

    connection.close()


    required_columns = [
        "contract",
        "commercial",
        "days_of_week",
        "start_time",
        "end_time",
        "preferred_program",
        "preferred_stopset",
        "min_spots_per_day",
        "max_spots_per_day",
        "min_spots_per_week",
        "max_spots_per_week",
        "allow_news",
        "allow_special_events",
        "notes"
    ]


    problems = []


    rows_checked = 0
    valid_rows = 0


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

            rows_checked += 1


            contract_number = (
                row["contract"].strip()
            )

            commercial_title = (
                row["commercial"].strip()
            )

            program_name = (
                row["preferred_program"].strip()
            )

            stopset_name = (
                row["preferred_stopset"].strip()
            )


            #
            # Find preferred program.
            #

            program = None

            if program_name:

                program = programs_by_name.get(
                    program_name
                )


                if program is None:

                    print(
                        f"ERROR: CSV row {row_number}: "
                        f"{contract_number} / "
                        f"{commercial_title}"
                    )

                    print(
                        f"- Preferred program "
                        f"'{program_name}' does not exist"
                    )

                    problems.append(
                        make_problem(
                            row_number,
                            row,
                            "preferred_program_not_found"
                        )
                    )

                    continue


            #
            # Find preferred stopset.
            #

            stopset = None

            if stopset_name:

                stopset = stopsets_by_name.get(
                    stopset_name
                )


                if stopset is None:

                    print(
                        f"ERROR: CSV row {row_number}: "
                        f"{contract_number} / "
                        f"{commercial_title}"
                    )

                    print(
                        f"- Preferred stopset "
                        f"'{stopset_name}' does not exist"
                    )

                    problems.append(
                        make_problem(
                            row_number,
                            row,
                            "preferred_stopset_not_found"
                        )
                    )

                    continue


            #
            # Verify that the stopset belongs to
            # the preferred program.
            #

            if program is not None and stopset is not None:

                if stopset["program_id"] != program["id"]:

                    print(
                        f"ERROR: CSV row {row_number}: "
                        f"{contract_number} / "
                        f"{commercial_title}"
                    )

                    print(
                        f"- Preferred stopset "
                        f"'{stopset_name}' does not belong "
                        f"to preferred program "
                        f"'{program_name}'"
                    )

                    problems.append(
                        make_problem(
                            row_number,
                            row,
                            "stopset_not_in_preferred_program",
                            {
                                "program_id": program["id"],
                                "stopset_id": stopset["id"]
                            }
                        )
                    )

                    continue

            #
            # No preferred program or stopset means
            # there is no preference to validate.
            #

            if program is None:

                valid_rows += 1

                continue

            #
            # Convert rule times.
            #

            rule_start = time_to_seconds(
                row["start_time"].strip()
            )

            rule_end = time_to_seconds(
                row["end_time"].strip()
            )


            #
            # The rule needs a complete time window
            # for this analysis.
            #

            if (
                rule_start is None
                or rule_end is None
            ):

                print(
                    f"ERROR: CSV row {row_number}: "
                    f"{contract_number} / "
                    f"{commercial_title}"
                )

                print(
                    "- Rule start_time and end_time "
                    "are required for preference checking"
                )

                problems.append(
                    make_problem(
                        row_number,
                        row,
                        "rule_time_window_missing"
                    )
                )

                continue


            #
            # Convert program times.
            #

            program_start = time_to_seconds(
                program["start_time"]
            )

            program_end = time_to_seconds(
                program["end_time"]
            )


            #
            # If the program has no time boundaries,
            # the rule window is the valid preference window.
            #

            if (
                program_start is None
                or program_end is None
            ):

                valid_window = (
                    rule_start,
                    rule_end
                )

            else:

                valid_window = get_intersection(
                    rule_start,
                    rule_end,
                    program_start,
                    program_end
                )


            #
            # Rule and program do not overlap.
            #

            if valid_window is None:

                print(
                    f"ERROR: CSV row {row_number}: "
                    f"{contract_number} / "
                    f"{commercial_title}"
                )

                print(
                    f"- Rule window "
                    f"{row['start_time']}-"
                    f"{row['end_time']} "
                    f"does not overlap preferred "
                    f"program "
                    f"'{program_name}' "
                    f"({program['start_time']}-"
                    f"{program['end_time']})"
                )

                problems.append(
                    make_problem(
                        row_number,
                        row,
                        "rule_program_no_overlap",
                        {
                            "rule_start_time": (
                                row["start_time"]
                            ),
                            "rule_end_time": (
                                row["end_time"]
                            ),
                            "program_start_time": (
                                program["start_time"]
                            ),
                            "program_end_time": (
                                program["end_time"]
                            )
                        }
                    )
                )

                continue


            valid_start, valid_end = valid_window

            if stopset is None:

                print(
                    f"OK: CSV row {row_number}: "
                    f"{contract_number} / "
                    f"{commercial_title}"
                )

                valid_rows += 1

                continue

            #
            # Convert stopset times.
            #

            stopset_start = time_to_seconds(
                stopset["start_time"]
            )

            stopset_end = time_to_seconds(
                stopset["end_time"]
            )


            if (
                stopset_start is None
                or stopset_end is None
            ):

                print(
                    f"ERROR: CSV row {row_number}: "
                    f"{contract_number} / "
                    f"{commercial_title}"
                )

                print(
                    f"- Preferred stopset "
                    f"'{stopset_name}' has no "
                    f"complete time window"
                )

                problems.append(
                    make_problem(
                        row_number,
                        row,
                        "stopset_time_window_missing",
                        {
                            "stopset_id": stopset["id"],
                            "program_id": program["id"],
                            "valid_start_time": (
                                seconds_to_time(valid_start)
                            ),
                            "valid_end_time": (
                                seconds_to_time(valid_end)
                            )
                        }
                    )
                )

                continue


            #
            # Check the preferred stopset.
            #

            if stopset_fits(
                stopset_start,
                stopset_end,
                valid_start,
                valid_end
            ):

                print(
                    f"OK: CSV row {row_number}: "
                    f"{contract_number} / "
                    f"{commercial_title}"
                )

                valid_rows += 1

                continue


            #
            # Preferred stopset is outside the valid
            # preference window.
            #

            print(
                f"ERROR: CSV row {row_number}: "
                f"{contract_number} / "
                f"{commercial_title}"
            )

            print(
                f"- Preferred stopset "
                f"'{stopset_name}' "
                f"{stopset['start_time']}-"
                f"{stopset['end_time']} "
                f"is outside the valid preference "
                f"window "
                f"{seconds_to_time(valid_start)}-"
                f"{seconds_to_time(valid_end)}"
            )


            problems.append(
                make_problem(
                    row_number,
                    row,
                    "preferred_stopset_outside_valid_window",
                    {
                        "program_id": program["id"],
                        "stopset_id": stopset["id"],

                        "program_start_time": (
                            program["start_time"]
                        ),

                        "program_end_time": (
                            program["end_time"]
                        ),

                        "rule_start_time": (
                            row["start_time"]
                        ),

                        "rule_end_time": (
                            row["end_time"]
                        ),

                        "valid_start_time": (
                            seconds_to_time(valid_start)
                        ),

                        "valid_end_time": (
                            seconds_to_time(valid_end)
                        ),

                        "stopset_start_time": (
                            stopset["start_time"]
                        ),

                        "stopset_end_time": (
                            stopset["end_time"]
                        )
                    }
                )
            )


    #
    # Write machine-readable report.
    #

    report = {
        "source_file": os.path.abspath(
            csv_file
        ),

        "rows_checked": rows_checked,

        "valid_rows": valid_rows,

        "problem_rows": len(problems),

        "problems": problems
    }


    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )


    #
    # Final summary.
    #

    print()

    print(
        f"Rows checked: {rows_checked}"
    )

    print(
        f"Valid rows:   {valid_rows}"
    )

    print(
        f"Rows with errors: {len(problems)}"
    )

    print()

    print(
        "Analysis report written to:"
    )

    print(
        report_file
    )

    print()


    if problems:

        print(
            "FAIL: Contract item rule "
            "configuration errors found."
        )

        return False


    print(
        "PASS: All contract item rules "
        "are valid."
    )

    return True


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Check contract item rules in a CSV "
            "and write a machine-readable report."
        )
    )


    parser.add_argument(
        "csv_file",
        help="Contract item rules CSV file"
    )


    parser.add_argument(
        "--report",
        default=None,
        help=(
            "JSON report filename. "
            "Defaults to <csv>.problems.json"
        )
    )


    args = parser.parse_args()


    if not os.path.exists(args.csv_file):

        raise FileNotFoundError(
            f"CSV file does not exist: "
            f"{args.csv_file}"
        )


    if args.report:

        report_file = args.report

    else:

        report_file = (
            args.csv_file
            + ".problems.json"
        )


    success = check_contract_item_rules_csv(
        args.csv_file,
        report_file
    )


    if not success:

        raise SystemExit(1)


if __name__ == "__main__":
    main()
