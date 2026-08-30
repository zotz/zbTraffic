#!/bin/bash

# scheduleem.sh
# Schedule the test contracts so far.




# Schedule all contract items from the highest ID down to 5.

highest_id=$(sqlite3 data/traffic.db \
    "SELECT MAX(id) FROM contract_items;")

for id in $(seq "$highest_id" -1 5); do
    echo "===== Contract Item $id ====="
    python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity($id))"
done

# Contract item 2 is intentionally not scheduled.


# Contract item 1 is one of the original seed/test items.
# It is intentionally scheduled separately from the big test suite.
echo "===== Contract Item 1 ====="
python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity(1))"


# Contract item 4 is intentionally not scheduled.


# Contract item 3 is another original seed/test item.
# It is intentionally scheduled separately from the big test suite.
echo "===== Contract Item 3 ====="
python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity(3))"


