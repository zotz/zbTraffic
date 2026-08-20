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
#python3 -m database.import_separation_rules_csv database/data/separation_rules_big.csv


# python3 -m database.generate_avails_range 1 2026-07-01 2026-12-30
python3 -m database.generate_avails_range 1 2026-08-15 2026-08-15


# 1. a customer
#python3 -m database.seed2big_database
python3 -m database.import_customers_csv database/data/customers_t001.csv
# 2. a commercial
python3 -m database.import_commercials_csv database/data/commercials_t001.csv
# 3. a contract
python3 -m database.import_contracts_csv database/data/contracts_t001.csv
# 4. a contract item
python3 -m database.import_contract_items_csv database/data/contract_items_t001.csv
# 5. a contract-item rule
python3 -m database.import_contract_item_rules_csv database/data/contract_item_rules_t001.csv



# No scheduling please, we will do this by hand to try and see what is going wrong.
#for id in $(seq 5 20); do
#    echo "===== Contract Item $id ====="
#    python3 -c "from traffic.scheduler import schedule_contract_item_quantity; print(schedule_contract_item_quantity($id))"
#done



