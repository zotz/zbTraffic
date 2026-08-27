#
# traffic/reconciliation.py
#
# Database-based reconciliation of zbTraffic spots against
# Rivendell as-played reports.
#

from traffic.database import get_connection


#
# Reconciliation states.
#

MATCH = "MATCH"
TIME_WINDOW_MATCH = "TIME_WINDOW_MATCH"
MISSING = "MISSING"
EXTRA = "EXTRA"


#
# Default maximum difference between zbTraffic's scheduled
# time and Rivendell's scheduled time for a time-window match.
#

DEFAULT_TIME_WINDOW_SECONDS = 120


#
# Convert HH:MM:SS to seconds after midnight.
#

def time_to_seconds(value):

    parts = value.strip().split(":")

    if len(parts) != 3:
        raise ValueError(
            f"Invalid time: {value}"
        )

    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2])

    return (
        hour * 3600
        + minute * 60
        + second
    )


#
# Normalize cart numbers so that, for example,
# "000020" and "20" compare equal.
#

def normalize_cart(value):

    if value is None:
        return ""

    value = str(value).strip()

    if value.isdigit():
        return str(int(value))

    return value


#
# Load the actual Exported spots from the database.
#
# This is the important distinction from the old fake
# reconciliation mode: these are the real zbTraffic
# database records.
#

def load_exported_spots(air_date):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                spots.id,
                spots.air_date,
                spots.air_time,
                spots.status,

                commercials.cart_number,
                commercials.title,
                commercials.length_seconds

            FROM spots

            LEFT JOIN commercials
                ON spots.commercial_id = commercials.id

            WHERE
                spots.air_date = ?
                AND spots.status = 'Exported'

            ORDER BY
                spots.air_time,
                spots.id
            """,
            (
                air_date,
            )
        )

        return cursor.fetchall()

    finally:

        connection.close()


#
# Parse a Rivendell as-played report.
#
# Expected format:
#
#     scheduled_time actual_time scheduled_length played_length
#     cart_number title...
#
# Example:
#
#     16:45:00 16:49:06 0:00:30 00:00:29 000020 zbT Zephyr Life 30
#
# The title may contain spaces, so everything after the
# cart number is treated as the title.
#

def parse_rivendell_file(filename):

    records = []

    with open(
        filename,
        "r",
        encoding="utf-8",
        errors="replace"
    ) as source:

        for line_number, raw_line in enumerate(
            source,
            start=1
        ):

            line = raw_line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) < 6:
                continue

            scheduled_time = parts[0]
            actual_time = parts[1]
            scheduled_length = parts[2]
            played_length = parts[3]
            cart_number = parts[4]

            title = " ".join(
                parts[5:]
            )

            try:

                scheduled_seconds = time_to_seconds(
                    scheduled_time
                )

                actual_seconds = time_to_seconds(
                    actual_time
                )

            except ValueError:

                continue

            records.append(
                {
                    "line_number": line_number,
                    "scheduled_time": scheduled_time,
                    "actual_time": actual_time,
                    "scheduled_length": scheduled_length,
                    "played_length": played_length,
                    "cart_number": cart_number,
                    "title": title,
                    "scheduled_seconds": scheduled_seconds,
                    "actual_seconds": actual_seconds
                }
            )

    return records


#
# Reconcile database spots against Rivendell records.
#
# Matching is based on:
#
#     1. cart number
#     2. exact scheduled time, if possible
#     3. otherwise scheduled time within the configured
#        time window
#
# Rivendell actual playback time is retained in the result
# but is not used to determine the match.
#

def reconcile(
    exported_spots,
    rivendell_records,
    time_window_seconds=DEFAULT_TIME_WINDOW_SECONDS
):

    unused_rivendell = set(
        range(
            len(rivendell_records)
        )
    )

    rows = []

    spots = sorted(
        exported_spots,
        key=lambda spot: (
            time_to_seconds(
                spot["air_time"]
            ),
            spot["id"]
        )
    )

    for spot in spots:

        our_cart = normalize_cart(
            spot["cart_number"]
        )

        our_seconds = time_to_seconds(
            spot["air_time"]
        )

        exact_matches = []
        window_matches = []

        for index in unused_rivendell:

            record = rivendell_records[index]

            rivendell_cart = normalize_cart(
                record["cart_number"]
            )

            if rivendell_cart != our_cart:
                continue

            difference = (
                record["scheduled_seconds"]
                - our_seconds
            )

            if difference == 0:

                exact_matches.append(
                    index
                )

            elif abs(difference) <= time_window_seconds:

                window_matches.append(
                    (
                        abs(difference),
                        index
                    )
                )

        #
        # Prefer an exact match.
        #

        if exact_matches:

            index = exact_matches[0]
            status = MATCH

        #
        # Otherwise use the closest time-window match.
        #

        elif window_matches:

            window_matches.sort()

            _, index = window_matches[0]

            status = TIME_WINDOW_MATCH

        #
        # Nothing matched this database spot.
        #

        else:

            index = None
            status = MISSING

        if index is not None:

            unused_rivendell.remove(
                index
            )

            rivendell = rivendell_records[index]

            difference = (
                rivendell["actual_seconds"]
                - our_seconds
            )

        else:

            rivendell = None
            difference = None

        rows.append(
            {
                "status": status,
                "checked": status in (
                    MATCH,
                    TIME_WINDOW_MATCH
                ),
                "spot": spot,
                "rivendell": rivendell,
                "difference": difference
            }
        )

    #
    # Anything left in Rivendell was not represented by
    # an Exported zbTraffic spot.
    #

    for index in sorted(
        unused_rivendell,
        key=lambda value: (
            rivendell_records[value]["scheduled_seconds"],
            value
        )
    ):

        rows.append(
            {
                "status": EXTRA,
                "checked": False,
                "spot": None,
                "rivendell": rivendell_records[index],
                "difference": None
            }
        )

    #
    # Keep the display/order deterministic.
    #

    def sort_key(row):

        if row["spot"] is not None:

            return (
                time_to_seconds(
                    row["spot"]["air_time"]
                ),
                0
            )

        return (
            row["rivendell"]["scheduled_seconds"],
            1
        )

    rows.sort(
        key=sort_key
    )

    return rows


#
# Count reconciliation results.
#

def reconciliation_counts(rows):

    counts = {
        MATCH: 0,
        TIME_WINDOW_MATCH: 0,
        MISSING: 0,
        EXTRA: 0
    }

    for row in rows:

        status = row["status"]

        if status in counts:
            counts[status] += 1

    return counts


#
# Return the database spot IDs represented by successful
# reconciliation matches.
#

def matched_spot_ids(rows):

    return [
        row["spot"]["id"]
        for row in rows
        if (
            row["status"] in (
                MATCH,
                TIME_WINDOW_MATCH
            )
            and row["spot"] is not None
        )
    ]


#
# Mark successfully reconciled Exported spots as Completed.
#
# This deliberately retains the status check so that a spot
# cannot accidentally be changed from some other status.
#

def mark_completed(rows):

    spot_ids = matched_spot_ids(rows)

    if not spot_ids:
        return 0

    connection = get_connection()
    cursor = connection.cursor()

    try:

        completed = 0

        for spot_id in spot_ids:

            cursor.execute(
                """
                UPDATE spots

                SET status = 'Completed'

                WHERE
                    id = ?
                    AND status = 'Exported'
                """,
                (
                    spot_id,
                )
            )

            completed += cursor.rowcount

        connection.commit()

        return completed

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()