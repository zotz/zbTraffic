#!/bin/bash
# sns1.sh
# Start new Station
# Drop the database
# re-create the database
# Put only the very basic records into the database except put in a good number of categories
##### THIS MAY CAUSE AN ISSUE because the Default Category is not record 1 in the table #####
# User can change what is needed and enter the records for their own station
# using the GUI Menu Systems


cd ~/projects/zbTraffic

rm data/traffic.db
python3 -m database.create_database
python3 -m database.create_initial_records

python3 -m database.import_categories_csv database/data/categories_all.csv

#python3 -m database.seed_database
#python3 -m database.seed2_database --spot-status No
#python3 -m database.seed2big_database
#python3 -m database.seed_programs_database
#python3 -m database.seed_stopsets --date 2026-08-08
#python3 -m database.seed_separation_rules_database
#python3 -m database.generate_avails_range 1 2026-01-01 2026-12-30


#python3 -m database.seed_spots_database --date 2026-08-07 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-08 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-09 --spot-status Pending

#python3 -m database.seed_contracts_database
#python3 -m database.seed_contract_items_database
# make a contract item rule:
#python3 -m commands.contract_item_rule_add \
#    --contract-item 1 \
#    --days Mon \
#    --start 08:00:00 \
#    --end 10:00:00
    
#python3 -m commands.contract_item_rule_edit 1 \
#    --days Mon \
#    --start 08:00:00 \
#    --end 10:00:00 \
#    --program 2
    
#python3 -m commands.contract_item_rule_edit 1 \
#    --days Mon \
#    --start 08:00:00 \
#    --end 10:00:00 \
#    --program 2 \
#    --spots-per-week 2

#python3 -m commands.contract_item_rule_edit 1 \
#    --days Mon,Tue,Wed,Thu,Fri \
#    --start 08:00:00 \
#    --end 10:00:00 \
#    --program 2 \
#    --spots-per-week 2

#python3 -m commands.contract_item_rule_edit 1 \
#    --days Mon \
#    --start 08:00:00 \
#    --end 10:00:00 \
#    --program 2 \
#    --spots-per-week 2

#python3 -m commands.contract_item_rule_edit 1 \
#    --days Mon,Tue,Wed,Thu,Fri \
#    --start 08:00:00 \
#    --end 10:00:00 \
#    --program 2 \
#    --spots-per-day 1 \
#    --spots-per-week 2

#python3 -m commands.contract_item_rule_add \
#    --contract-item 3 \
#    --days Mon,Wed,Fri \
#    --start 12:00:00 \
#    --end 17:00:00 \
#    --program 3 \
#    --spots-per-day 2 \
#    --spots-per-week 5


########### Seed big contracts suite
#python3 -m database.import_categories_csv database/data/categories_big.csv
#python3 -m database.import_separation_rules_csv database/data/separation_rules_big.csv
#python3 -m database.import_contracts_csv database/data/contracts_big.csv
#python3 -m database.import_contract_items_csv database/data/contract_items_big.csv
#python3 -m database.import_contract_item_rules_csv database/data/contract_item_rules_big.csv

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
