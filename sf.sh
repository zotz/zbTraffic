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
python3 -m database.seed_stopsets --date 2026-08-06

python3 -m database.generate_avails_range 1 2026-01-01 2026-12-30


#python3 -m database.seed_spots_database --date 2026-08-07 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-08 --spot-status Pending
#python3 -m database.seed_spots_database --date 2026-08-09 --spot-status Pending

python3 -m database.seed_contracts_database
python3 -m database.seed_contract_items_database

#python3 -m commands.export_rivendell_log 2026-08-07
#python3 -m commands.export_rivendell_log 2026-08-08
#python3 -m commands.export_rivendell_log 2026-08-09

#scp logs/zbt_*.log rd@192.168.86.137:/home/rd/Desktop/ewxfer/zbt/

# Some useful commands
# python3 -m prototype.traffic_board &
# sqlitebrowser data/traffic.db &
# python3 -m gui.database_browser &
