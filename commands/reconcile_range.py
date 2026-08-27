#
# commands/reconcile_range.py
#
# Export, fake-play, reconcile, and complete a range of dates.
#
# This utility is intended for testing. It uses the real zbTraffic
# database spots and the real reconciliation engine, but uses
# logtoplayed.py to manufacture a Rivendell as-played report.
#
# Workflow for each date:
#
#     Scheduled
#         |
#         v
#     export_rivendell_log
#         |
#         v
#     Exported
#         |
#         v
#     logtoplayed.py
#         |
#         v
#     as-played
#         |
#         v
#     reconciliation
#         |
#         v
#     Completed
#
# The utility does NOT mark spots Completed when reconciliation
# produces MISSING or EXTRA records.
#

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta


from traffic.reconciliation import (
    load_exported_spots,
    parse_rivendell_file,
    reconcile,
    reconciliation_counts,
    mark_completed
)


#
# Existing file naming conventions.
#

EXPORT_DIRECTORY = "logs"
ASPLAYED_DIRECTORY = "asplayed"

LOG_PREFIX = "zbt_"


#
# Path to the existing fake as-played utility.
#

LOGTOPLAYED = "prototype/grk/logtoplayed.py"


#
# Parse a command-line date.
#

def parse_date(value):

    try:

        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        raise argparse.ArgumentTypeError(
            f"Invalid date: {value}; expected YYYY-MM-DD"
        )


#
# Generate each date in an inclusive range.
#

def date_range(start_date, end_date):

    current = start_date

    while current <= end_date:

        yield current

        current += timedelta(
            days=1
        )


#
# Run the existing zbTraffic Rivendell export command.
#
# We deliberately invoke it the same way you normally do:
#
#     python3 -m commands.export_rivendell_log YYYY-MM-DD
#
# This avoids making assumptions about the internal implementation
# of the export command.
#

def export_date(air_date):

    date_string = air_date.isoformat()

    print(
        f"Exporting: {date_string}"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "commands.export_rivendell_log",
            date_string
        ]
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"Export failed for {date_string}"
        )


#
# Generate a fake as-played report from the exported log.
#

def generate_asplayed(air_date):

    date_string = air_date.isoformat()
    compact_date = air_date.strftime(
        "%Y%m%d"
    )

    exported_file = os.path.join(
        EXPORT_DIRECTORY,
        f"{LOG_PREFIX}{compact_date}.log"
    )

    asplayed_file = os.path.join(
        ASPLAYED_DIRECTORY,
        f"{LOG_PREFIX}{compact_date}.log"
    )

    if not os.path.exists(exported_file):

        raise FileNotFoundError(
            f"Exported log was not created: "
            f"{exported_file}"
        )

    os.makedirs(
        ASPLAYED_DIRECTORY,
        exist_ok=True
    )

    print(
        f"Generating as-played: {date_string}"
    )

    result = subprocess.run(
        [
            sys.executable,
            LOGTOPLAYED,
            exported_file,
            asplayed_file
        ]
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"logtoplayed failed for {date_string}"
        )

    if not os.path.exists(asplayed_file):

        raise FileNotFoundError(
            f"As-played file was not created: "
            f"{asplayed_file}"
        )

    return asplayed_file


#
# Reconcile one date.
#

def reconcile_date(air_date, asplayed_file):

    date_string = air_date.isoformat()

    spots = load_exported_spots(
        date_string
    )

    rivendell = parse_rivendell_file(
        asplayed_file
    )

    rows = reconcile(
        spots,
        rivendell
    )

    counts = reconciliation_counts(
        rows
    )

    print(
        f"Reconciliation: {date_string}"
    )

    print(
        f"  Exported spots:     {len(spots)}"
    )

    print(
        f"  As-played records:   {len(rivendell)}"
    )

    print(
        f"  MATCH:              {counts['MATCH']}"
    )

    print(
        f"  TIME_WINDOW_MATCH:  {counts['TIME_WINDOW_MATCH']}"
    )

    print(
        f"  MISSING:            {counts['MISSING']}"
    )

    print(
        f"  EXTRA:              {counts['EXTRA']}"
    )

    #
    # Only complete spots when the reconciliation is clean.
    #
    # This is intentionally conservative for the testing utility.
    #

    if (
        counts["MISSING"] == 0
        and counts["EXTRA"] == 0
    ):

        completed = mark_completed(
            rows
        )

        print(
            f"  Completed:          {completed}"
        )

        return {
            "success": True,
            "counts": counts,
            "completed": completed
        }

    print(
        "  NOT COMPLETED: reconciliation "
        "contained MISSING or EXTRA records."
    )

    return {
        "success": False,
        "counts": counts,
        "completed": 0
    }


#
# Process the requested date range.
#

def process_range(start_date, end_date):

    total_dates = 0
    successful_dates = 0
    failed_dates = 0

    total_completed = 0

    total_counts = {
        "MATCH": 0,
        "TIME_WINDOW_MATCH": 0,
        "MISSING": 0,
        "EXTRA": 0
    }

    print()
    print("=" * 60)
    print("zbTraffic Reconciliation Range")
    print("=" * 60)
    print(
        f"Start date: {start_date.isoformat()}"
    )
    print(
        f"End date:   {end_date.isoformat()}"
    )
    print()

    for air_date in date_range(
        start_date,
        end_date
    ):

        total_dates += 1

        print()
        print(
            "-" * 60
        )
        print(
            air_date.isoformat()
        )
        print(
            "-" * 60
        )

        try:

            #
            # Step 1:
            # Export the day's scheduled spots.
            #

            export_date(
                air_date
            )

            #
            # Step 2:
            # Manufacture the as-played report.
            #

            asplayed_file = generate_asplayed(
                air_date
            )

            #
            # Step 3:
            # Reconcile the real database records.
            #

            result = reconcile_date(
                air_date,
                asplayed_file
            )

            counts = result["counts"]

            for key in total_counts:

                total_counts[key] += counts[key]

            total_completed += result[
                "completed"
            ]

            if result["success"]:

                successful_dates += 1

            else:

                failed_dates += 1

        except Exception as error:

            failed_dates += 1

            print(
                f"ERROR: {error}"
            )

            #
            # Continue with the next date rather than
            # destroying the usefulness of a long-range
            # test run because one date failed.
            #

            continue

    print()
    print("=" * 60)
    print("Reconciliation Range Results")
    print("=" * 60)

    print(
        f"Dates processed:     {total_dates}"
    )

    print(
        f"Dates successful:    {successful_dates}"
    )

    print(
        f"Dates failed:        {failed_dates}"
    )

    print()

    print(
        f"MATCH:               {total_counts['MATCH']}"
    )

    print(
        f"TIME_WINDOW_MATCH:   "
        f"{total_counts['TIME_WINDOW_MATCH']}"
    )

    print(
        f"MISSING:             {total_counts['MISSING']}"
    )

    print(
        f"EXTRA:               {total_counts['EXTRA']}"
    )

    print()

    print(
        f"Spots completed:     {total_completed}"
    )

    print()

    if failed_dates:

        print(
            "RECONCILIATION RANGE COMPLETED "
            "WITH ERRORS"
        )

        return 1

    print(
        "RECONCILIATION RANGE COMPLETED "
        "SUCCESSFULLY"
    )

    return 0


#
# Command-line interface.
#

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Export, fake-play, reconcile, and "
            "complete a range of zbTraffic dates."
        )
    )

    parser.add_argument(
        "start_date",
        type=parse_date,
        help="First date, YYYY-MM-DD"
    )

    parser.add_argument(
        "end_date",
        type=parse_date,
        help="Last date, YYYY-MM-DD"
    )

    args = parser.parse_args()

    if args.end_date < args.start_date:

        parser.error(
            "end_date must not be before start_date"
        )

    return process_range(
        args.start_date,
        args.end_date
    )


if __name__ == "__main__":

    sys.exit(
        main()
    )
