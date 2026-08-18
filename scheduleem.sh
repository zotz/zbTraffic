#!/bin/bash

# scheduleem.sh
# Schedule the test contracts so far.




# Schedule 5 to 20 first Perhaps try 20 to 5
#for id in $(seq 20 -1 5); do
for id in {20..5}; do
    echo "===== Contract Item $id ====="
    python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity($id))"
done


# python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity(20))"


# Do these after the others above
python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity(1))"
python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity(3))"
