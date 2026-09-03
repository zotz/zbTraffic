#!/bin/bash

# File: tests/scheduler_regression_test.sh

echo
echo "========================================"
echo "Scheduler Regression Tests"
echo "========================================"


#
# Test 1: Scheduled quantities
#

echo
echo "Test 1: Scheduled quantities"

python3 - <<'PY'
import sqlite3
import sys

connection = sqlite3.connect("data/traffic.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        ci.id,
        ci.quantity,
        COUNT(s.id)
    FROM contract_items ci
    LEFT JOIN spots s
        ON s.contract_item_id = ci.id
        AND s.status = 'Scheduled'
    WHERE ci.id IN (1, 3)
    GROUP BY
        ci.id,
        ci.quantity
    ORDER BY
        ci.id
""")

rows = cursor.fetchall()

failed = False

for contract_item_id, expected_quantity, scheduled_quantity in rows:

    print(
        f"  Contract item {contract_item_id}: "
        f"expected={expected_quantity}, "
        f"scheduled={scheduled_quantity}"
    )

    if scheduled_quantity != expected_quantity:
        failed = True

if failed:
    print("FAIL: Scheduled quantities do not match.")
    sys.exit(1)

print("PASS")
PY

if [ $? -ne 0 ]; then
    exit 1
fi


#
# Test 2: No Pending spots remain
#

echo
echo "Test 2: No Pending spots remain"

python3 - <<'PY'
import sqlite3
import sys

connection = sqlite3.connect("data/traffic.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        contract_item_id,
        COUNT(*)
    FROM spots
    WHERE contract_item_id IN (1, 3)
      AND status = 'Pending'
    GROUP BY
        contract_item_id
    ORDER BY
        contract_item_id
""")

rows = cursor.fetchall()

if rows:

    for contract_item_id, count in rows:
        print(
            f"  Contract item {contract_item_id}: "
            f"{count} Pending spots"
        )

    print("FAIL: Pending spots remain.")
    sys.exit(1)

print("PASS")
PY

if [ $? -ne 0 ]; then
    exit 1
fi


#
# Test 3: Scheduled dates are within contract item flight
#

echo
echo "Test 3: Scheduled dates are within contract item flight"

python3 - <<'PY'
import sqlite3
import sys

connection = sqlite3.connect("data/traffic.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        s.id,
        s.contract_item_id,
        s.air_date,
        ci.start_date,
        ci.end_date
    FROM spots s
    JOIN contract_items ci
        ON ci.id = s.contract_item_id
    WHERE s.contract_item_id IN (1, 3)
      AND s.status = 'Scheduled'
      AND (
          s.air_date < ci.start_date
          OR s.air_date > ci.end_date
      )
    ORDER BY
        s.contract_item_id,
        s.air_date
""")

rows = cursor.fetchall()

if rows:

    for row in rows:
        print(
            f"  Spot {row[0]}: "
            f"contract_item={row[1]}, "
            f"air_date={row[2]}, "
            f"flight={row[3]} -> {row[4]}"
        )

    print("FAIL: Scheduled spot is outside contract item flight.")
    sys.exit(1)

print("PASS")
PY

if [ $? -ne 0 ]; then
    exit 1
fi


#
# Test 4: No overfilled avails
#
# Spot length comes from commercials.length_seconds.
#

echo
echo "Test 4: No overfilled avails"

python3 - <<'PY'
import sqlite3
import sys

connection = sqlite3.connect("data/traffic.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        a.id,
        a.air_date,
        a.start_time,
        a.length_seconds,
        SUM(c.length_seconds) AS used_seconds
    FROM avails a
    JOIN spots s
        ON s.avail_id = a.id
       AND s.status = 'Scheduled'
    JOIN commercials c
        ON c.id = s.commercial_id
    GROUP BY
        a.id,
        a.air_date,
        a.start_time,
        a.length_seconds
    HAVING
        SUM(c.length_seconds) > a.length_seconds
    ORDER BY
        a.air_date,
        a.start_time
""")

rows = cursor.fetchall()

if rows:

    for row in rows:
        print(
            f"  Avail {row[0]} on {row[1]} {row[2]}: "
            f"capacity={row[3]}, "
            f"used={row[4]}"
        )

    print("FAIL: One or more avails are overfilled.")
    sys.exit(1)

print("PASS")
PY

if [ $? -ne 0 ]; then
    exit 1
fi


#
# Test 5: Every scheduled spot has an avail
#

echo
echo "Test 5: Every scheduled spot has an avail"

python3 - <<'PY'
import sqlite3
import sys

connection = sqlite3.connect("data/traffic.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        id,
        contract_item_id
    FROM spots
    WHERE contract_item_id IN (1, 3)
      AND status = 'Scheduled'
      AND avail_id IS NULL
""")

rows = cursor.fetchall()

if rows:

    for spot_id, contract_item_id in rows:
        print(
            f"  Spot {spot_id}: "
            f"contract_item={contract_item_id}"
        )

    print("FAIL: Scheduled spot has no avail.")
    sys.exit(1)

print("PASS")
PY

if [ $? -ne 0 ]; then
    exit 1
fi


#
# Test 6: Scheduled spots reference valid avails
#

echo
echo "Test 6: Scheduled spots reference valid avails"

python3 - <<'PY'
import sqlite3
import sys

connection = sqlite3.connect("data/traffic.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        s.id,
        s.contract_item_id,
        s.avail_id
    FROM spots s
    LEFT JOIN avails a
        ON a.id = s.avail_id
    WHERE s.contract_item_id IN (1, 3)
      AND s.status = 'Scheduled'
      AND a.id IS NULL
""")

rows = cursor.fetchall()

if rows:

    for spot_id, contract_item_id, avail_id in rows:
        print(
            f"  Spot {spot_id}: "
            f"contract_item={contract_item_id}, "
            f"avail_id={avail_id}"
        )

    print("FAIL: Scheduled spot references nonexistent avail.")
    sys.exit(1)

print("PASS")
PY

if [ $? -ne 0 ]; then
    exit 1
fi


#
# Test 7: Show spot distribution by day
#

echo
echo "========================================"
echo "Spot Distribution By Day"
echo "========================================"

python3 - <<'PY'
import sqlite3

connection = sqlite3.connect("data/traffic.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        contract_item_id,
        air_date,
        COUNT(*) AS spots
    FROM spots
    WHERE contract_item_id IN (1, 3)
      AND status = 'Scheduled'
    GROUP BY
        contract_item_id,
        air_date
    ORDER BY
        contract_item_id,
        air_date
""")

rows = cursor.fetchall()

if not rows:

    print("No scheduled spots found.")

else:

    current_item = None

    for contract_item_id, air_date, spots in rows:

        if contract_item_id != current_item:
            print()
            print(f"Contract item {contract_item_id}:")
            current_item = contract_item_id

        print(f"  {air_date}: {spots}")
PY


#
# Test 8: Show utilization of avails containing scheduled spots
#

echo
echo "========================================"
echo "Used Avail Utilization"
echo "========================================"

python3 - <<'PY'
import sqlite3

connection = sqlite3.connect("data/traffic.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        a.id,
        a.air_date,
        a.start_time,
        a.length_seconds,
        SUM(c.length_seconds) AS used_seconds
    FROM avails a
    JOIN spots s
        ON s.avail_id = a.id
       AND s.status = 'Scheduled'
    JOIN commercials c
        ON c.id = s.commercial_id
    GROUP BY
        a.id,
        a.air_date,
        a.start_time,
        a.length_seconds
    ORDER BY
        a.air_date,
        a.start_time
""")

for (
    avail_id,
    air_date,
    start_time,
    capacity,
    used_seconds
) in cursor.fetchall():

    print(
        f"  Avail {avail_id} "
        f"{air_date} {start_time}: "
        f"{used_seconds}/{capacity} seconds"
    )
PY

#

# Test 9: Separation rule is seeded

#

echo
echo "Test 9: Separation rule is seeded"

python3 - <<'PY'
from traffic.database import get_connection
from traffic.separation_rules import add_separation_rule
import sys

connection = get_connection()
cursor = connection.cursor()

cursor.execute(
    """
    SELECT id
    FROM separation_rules
    WHERE
        (
            category1_id = ?
            AND category2_id = ?
        )
        OR
        (
            category1_id = ?
            AND category2_id = ?
        )
    """,
    (
        2,
        4,
        4,
        2
    )
)

existing = cursor.fetchone()

rule = None

if existing is None:

    rule, errors = add_separation_rule(
        2,
        4,
        20,
        "Scheduler regression test"
    )

    if errors:
        print("FAIL: Could not seed separation rule.")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)

    print("  Seeded Automotive <-> Retail separation rule.")

else:

    print("  Automotive <-> Retail separation rule already exists.")

connection.close()

from traffic.separation_rules import get_separation_minutes

automotive_to_retail = get_separation_minutes(
    2,
    4
)

retail_to_automotive = get_separation_minutes(
    4,
    2
)


print(
    f"  Automotive -> Retail: "
    f"{automotive_to_retail} minutes"
)

print(
    f"  Retail -> Automotive: "
    f"{retail_to_automotive} minutes"
)


passed = True

if automotive_to_retail != 20:

    print(
        "FAIL: Automotive -> Retail "
        "separation rule is incorrect."
    )

    passed = False


if retail_to_automotive != 20:

    print(
        "FAIL: Retail -> Automotive "
        "separation rule is incorrect."
    )

    passed = False





if passed:

    print("PASS")

else:

    sys.exit(1)
PY

if [ $? -ne 0 ]; then
exit 1
fi


#

# Test 10: Separation rule rejects insufficient separation

#

echo
echo "Test 10: Separation rejection"

python3 - <<'PY'
from traffic.separation_rules import check_separation
import sys


allowed = check_separation(
    2,
    4,
    15
)


print(
    f"  15-minute separation: "
    f"{'allowed' if allowed else 'rejected'}"
)


if allowed:

    print(
        "FAIL: 15-minute separation "
        "should be rejected."
    )

    sys.exit(1)


print("PASS")
PY

if [ $? -ne 0 ]; then
exit 1
fi



#

# Test 11: Separation rule allows sufficient separation

#

echo
echo "Test 11: Separation allowed"

python3 - <<'PY'
from traffic.separation_rules import check_separation
import sys


allowed = check_separation(
    2,
    4,
    30
)


print(
    f"  30-minute separation: "
    f"{'allowed' if allowed else 'rejected'}"
)


if not allowed:

    print(
        "FAIL: 30-minute separation "
        "should be allowed."
    )

    sys.exit(1)


print("PASS")
PY

if [ $? -ne 0 ]; then
exit 1
fi



#

# Test 12: Scheduled spots respect separation rules

#

echo
echo "Test 12: Scheduled spots respect separation rules"

python3 - <<'PY'
import sqlite3
import sys
from datetime import datetime

from traffic.separation_rules import get_separation_minutes


connection = sqlite3.connect(
    "data/traffic.db"
)

cursor = connection.cursor()


cursor.execute(
    """
    SELECT
        s.id,
        s.air_date,
        s.air_time,
        c.customer_id,
        c.category_id
    FROM spots s
    JOIN commercials c
        ON c.id = s.commercial_id
    WHERE s.status = 'Scheduled'
      AND s.contract_item_id IN (1, 3)
      AND c.category_id IS NOT NULL
    ORDER BY
        s.air_date,
        s.air_time,
        s.id
    """
)


rows = cursor.fetchall()

connection.close()


spots = []


for (
    spot_id,
    air_date,
    air_time,
    customer_id,
    category_id
) in rows:

    air_datetime = datetime.strptime(
        f"{air_date} {air_time}",
        "%Y-%m-%d %H:%M:%S"
    )

    spots.append(
        (
            spot_id,
            air_datetime,
            customer_id,
            category_id
        )
    )


failed = False


for i in range(len(spots)):

    (
        spot1_id,
        time1,
        customer1_id,
        category1_id
    ) = spots[i]


    for j in range(i + 1, len(spots)):

        (
            spot2_id,
            time2,
            customer2_id,
            category2_id
        ) = spots[j]


        #
        # Separation rules do not apply
        # between spots for the same customer.
        #

        if customer1_id == customer2_id:

            continue


        required_minutes = (
            get_separation_minutes(
                category1_id,
                category2_id
            )
        )


        if required_minutes == 0:

            continue


        minutes_apart = (
            time2 - time1
        ).total_seconds() / 60


        if minutes_apart < required_minutes:

            print(
                f"  Spot {spot1_id} "
                f"and Spot {spot2_id}: "
                f"{minutes_apart:.0f} minutes apart, "
                f"required={required_minutes}"
            )

            failed = True


if failed:

    print(
        "FAIL: Scheduled spots violate "
        "separation rules."
    )

    sys.exit(1)


print("PASS")
PY

if [ $? -ne 0 ]; then
    exit 1
fi

echo
echo "========================================"
echo "ALL 12 SCHEDULER REGRESSION TESTS PASSED"
echo "========================================"

