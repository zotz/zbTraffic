#!/bin/bash
# sft001.sh
# starting fresh testing 001
# It is to drop the zbTraffic database and reset it up to the first testing config

cd ~/projects/zbTraffic

rm data/traffic.db
python3 -m database.create_database
# Create initial recorsd for:
# categories | Uncategorized
# stations | Default Station
# programs | Default Program
# stopsets | Default Stopset
# salespeople | House
# We want to run this.
python3 -m database.create_initial_records
# seed_database was only creating categories at the end.
# python3 -m database.seed_database
# use the category importer instead
python3 -m database.import_categories_csv database/data/categories_all.csv
#python3 -m database.import_categories_csv database/data/categories_big.csv

python3 -m database.import_programs_csv database/data/programs_all.csv
# stop using seed_stopsets
#python3 -m database.seed_stopsets --date 2026-08-08
# And start using stopsets importer instead
python3 -m database.import_stopsets_csv database/data/stopsets_all.csv



#python3 -m database.seed_separation_rules_database
python3 -m database.import_separation_rules_csv database/data/separation_rules_big.csv


python3 -m database.generate_avails_range 1 2026-07-01 2026-12-30




########### Seed big contracts suite
# categories are handled eariler now as part of the seeding above.
#python3 -m database.import_categories_csv database/data/categories_big.csv
#python3 -m database.import_separation_rules_csv database/data/separation_rules_big.csv
#python3 -m database.import_contracts_csv database/data/contracts_big.csv
#python3 -m database.import_contract_items_csv database/data/contract_items_big.csv
#python3 -m database.import_contract_item_rules_csv database/data/contract_item_rules_big.csv



# No scheduling please, we will do this by hand to try and see what is going wrong.
#for id in $(seq 5 20); do
#    echo "===== Contract Item $id ====="
#    python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity($id))"
#done

# take these out so that no spots are scheduled
#python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity(1))"
#python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity(3))"


# call regression test here.
#./tests/scheduler_regression_test.sh


# Add another contract_item_rule
#python3 -m commands.contract_item_rule_add \
#    --contract-item 1 \
#    --program 2





# Don't do these 3 right now. They create and assign spots to avails
# This means the resulting spots end with a status of Scheduled
#python3 -m commands.spots_generate 1
#python3 -m commands.spots_generate 3
#python3 -m commands.spots_generate 4
# Do these 3 instead. They create spots with a Pending status intended to be manually
# scheduled with python3 -m prototype.traffic_board
#python3 -m database.seed_spots_database --date 2026-08-09 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-10 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-11 --spot-status Pending

#python3 -m commands.export_rivendell_log 2026-08-07
#python3 -m commands.export_rivendell_log 2026-08-08
#python3 -m commands.export_rivendell_log 2026-08-09

#scp logs/zbt_*.log rd@192.168.86.137:/home/rd/Desktop/ewxfer/zbt/

# Some useful commands
# python3 -m prototype.traffic_board &
# sqlitebrowser data/traffic.db &
# python3 -m gui.database_browser &
