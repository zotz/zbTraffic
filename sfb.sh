#!/bin/bash
# sfb.sh
# I was going to call it startfresh.sh but I want something shorter for this right now.
# It is to drop the zbTraffic database and reset it up to my last testing setup for further dev work.

cd ~/projects/zbTraffic

echo 'dropping database'
rm data/traffic.db
echo 'running create database'
python3 -m database.create_database
# Create initial recorsd for:
# categories | Uncategorized
# stations | Default Station
# programs | Default Program
# stopsets | Default Stopset
# salespeople | House
# We want to run this.
echo 'running create initial records'
python3 -m database.create_initial_records
# seed_database was only creating categories at the end.
# python3 -m database.seed_database
# use the category importer instead
echo 'running the category importer'
python3 -m database.import_categories_csv database/data/categories_all.csv
# seed2_database seeds
# customers - 3
# contacts - 3
# commercials - 3
# spots - 3 can be scheduled, pending. or 0 - no spots created.
# The line below was not creating any spots.
#echo 'running seed2_database'
#python3 -m database.seed2_database --spot-status No
#echo 'running seed2big_database'
#python3 -m database.seed2big_database
echo 'running customer csv importer'
python3 -m database.import_customers_csv database/data/customers_big.csv

echo 'running commercial csv importer'
python3 -m database.import_commercials_csv database/data/commercials_big.csv
# stop using seed_programs_database
# python3 -m database.seed_programs_database
# programs importer instead
echo 'running program csv importer'
python3 -m database.import_programs_csv database/data/programs_all.csv
# stop using seed_stopsets
#python3 -m database.seed_stopsets --date 2026-08-08
# And start using stopsets importer instead
echo 'running stopset csv importer'
python3 -m database.import_stopsets_csv database/data/stopsets_all.csv



#python3 -m database.seed_separation_rules_database
python3 -m database.generate_avails_range 1 2026-01-01 2026-12-30


#python3 -m database.seed_spots_database --date 2026-08-07 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-08 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-09 --spot-status Pending

#python3 -m database.seed_contracts_database
python3 -m database.import_contracts_csv database/data/contracts_seed.csv

# python3 -m database.seed_contract_items_database
python3 -m database.import_contract_items_csv database/data/contract_items_seed.csv



########### Seed big contracts suite
python3 -m database.import_separation_rules_csv database/data/separation_rules_big.csv
python3 -m database.import_contracts_csv database/data/contracts_big.csv
python3 -m database.import_contract_items_csv database/data/contract_items_big.csv
python3 -m database.import_contract_item_rules_csv database/data/contract_item_rules_big.csv

# take these out so that no spots are scheduled
python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity(1))"
python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity(3))"

# No scheduling please, we will do this by hand to try and see what is going wrong.
for id in $(seq 5 20); do
    echo "===== Contract Item $id ====="
    python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity($id))"
done


# call regression test here. only call in sfb.sh not in sfbnosched.sh
./tests/scheduler_regression_test.sh



# this is how we export logs right now
#python3 -m commands.export_rivendell_log 2026-08-07
#python3 -m commands.export_rivendell_log 2026-08-08
#python3 -m commands.export_rivendell_log 2026-08-09

# This is how we copy logs to the rivendell machine
#scp logs/zbt_*.log rd@192.168.86.137:/home/rd/Desktop/ewxfer/zbt/

# Some useful commands
# python3 -m prototype.traffic_board &
# sqlitebrowser data/traffic.db &
# python3 -m gui.database_browser &
