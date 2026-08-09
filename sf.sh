#!/bin/bash
# sf.sh
# I was going to call it startfresh.sh but I want something shorter for this right now.
# It is to drop the zbTraffic database and reset it up to my last testing setup for further dev work.

cd ~/projects/zbTraffic

rm data/traffic.db
python3 -m database.create_database
python3 -m database.create_initial_records
python3 -m database.seed_database
python3 -m database.seed2_database --spot-status No
python3 -m database.seed_programs_database
python3 -m database.seed_stopsets --date 2026-08-08

python3 -m database.generate_avails_range 1 2026-01-01 2026-12-30


#python3 -m database.seed_spots_database --date 2026-08-07 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-08 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-09 --spot-status Pending

python3 -m database.seed_contracts_database
python3 -m database.seed_contract_items_database
# make a contract item rule:
python3 -m commands.contract_item_rule_add \
    --contract-item 1 \
    --days Mon \
    --start 08:00:00 \
    --end 10:00:00
    
python3 -m commands.contract_item_rule_edit 1 \
    --days Mon \
    --start 08:00:00 \
    --end 10:00:00 \
    --program 2
    
python3 -m commands.contract_item_rule_edit 1 \
    --days Mon \
    --start 08:00:00 \
    --end 10:00:00 \
    --program 2 \
    --spots-per-week 2

python3 -m commands.contract_item_rule_edit 1 \
    --days Mon,Tue,Wed,Thu,Fri \
    --start 08:00:00 \
    --end 10:00:00 \
    --program 2 \
    --spots-per-week 2

python3 -m commands.contract_item_rule_edit 1 \
    --days Mon \
    --start 08:00:00 \
    --end 10:00:00 \
    --program 2 \
    --spots-per-week 2

python3 -m commands.contract_item_rule_edit 1 \
    --days Mon,Tue,Wed,Thu,Fri \
    --start 08:00:00 \
    --end 10:00:00 \
    --program 2 \
    --spots-per-day 1 \
    --spots-per-week 2



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
