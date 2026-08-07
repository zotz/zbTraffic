# File: database/seed_contract_items_database.py

from traffic.contract_items import add_contract_item


def seed_contract_items():


    #
    # Existing commercial Customer 1
    #

    add_contract_item(

        contract_id=1,

        commercial_id=1,

        quantity=300,

        description="Summer Boat Sale",

        priority=1,

        notes="Existing commercial test"

    )



    #
    # Future commercial
    #

    add_contract_item(

        contract_id=1,

        commercial_id=None,
        #commercial_id=3,

        commercial_title="Future Spring Boat Campaign",

        quantity=50,

        spot_length_seconds=30,

        description="Future commercial test",

        priority=1,

        notes="Commercial not produced yet"

    )



    #
    # Existing commercial Customer 2
    #

    add_contract_item(

        contract_id=2,

        commercial_id=2,

        quantity=100,

        description="Summer Auto blowout",

        priority=1,

        notes="Existing commercial test"

    )

    #
    # Existing commercial Customer 3
    #

    add_contract_item(

        contract_id=3,

        commercial_id=3,

        quantity=200,

        description="Summer Travel special",

        priority=1,

        notes="Existing commercial test"

    )


    print(
        "Contract items seeded successfully."
    )



if __name__ == "__main__":

    seed_contract_items()
