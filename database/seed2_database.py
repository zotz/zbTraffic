#!/usr/bin/env python3

# File: database/seed2_database.py
#
# Development/test database seed.
#
# Requires:
#   create_initial_records.py has been run.
#   seed_database.py has been run for categories.
#
# Uses:
#   seed_common.py

import argparse
from datetime import date
from traffic.utilities import current_timestamp

from database.seed_common import (
    check_prerequisites,
    get_first_station_id,
    get_customer_id_by_company_name,
)


def seed_customers():

    from traffic.customers import add_customer

    from database.seed_common import (
        get_customer_id_by_company_name,
    )


    print(
        "Creating customers..."
    )


    customers = {}


    #
    # zbT Test Customer
    #

    company_name = "zbT First Test Customer"


    customer_id = get_customer_id_by_company_name(
        company_name
    )


    if customer_id is None:

        customer_id, errors = add_customer(
            company_name=company_name,
            telephone="242-555-8699",
            email="ron@zbT.com"
        )


        if customer_id is None:

            raise RuntimeError(
                "Unable to create "
                + company_name
                + ": "
                + ", ".join(errors)
            )


    customers["zbt_test"] = customer_id



    #
    # Second test customer
    #
    # Replace these details with the customer
    # you want to use for future testing.
    #

    company_name = "zbT Second Test Customer"


    customer_id = get_customer_id_by_company_name(
        company_name
    )


    if customer_id is None:

        customer_id, errors = add_customer(
            company_name=company_name,
            telephone="242-555-0000",
            email="second@2zbT.com"
        )


        if customer_id is None:

            raise RuntimeError(
                "Unable to create "
                + company_name
                + ": "
                + ", ".join(errors)
            )


    customers["zbt_second_test"] = customer_id

    #
    # Third test customer
    #

    company_name = "zbT Third Test Customer"


    customer_id = get_customer_id_by_company_name(
        company_name
    )


    if customer_id is None:

        customer_id, errors = add_customer(
            company_name=company_name,
            telephone="242-555-0001",
            email="third@3zbT.com"
        )


        if customer_id is None:

            raise RuntimeError(
                "Unable to create "
                + company_name
                + ": "
                + ", ".join(errors)
            )


    customers["zbt_third_test"] = customer_id

    return customers



def seed_contacts(
    customers
):

    from traffic.contacts import add_contact


    print(
        "Creating contacts..."
    )


    contacts = {}


    #
    # zbT Test Customer
    #

    contact_id, errors = add_contact(
        customer_id=customers["zbt_test"],
        first_name="Ron",
        last_name="Test",
        telephone="242-555-8699",
        email="ron@zbT.com"
    )


    if contact_id is None:

        raise RuntimeError(
            "Unable to create contact for "
            "zbT Test Customer: "
            + ", ".join(errors)
        )


    contacts["zbt_test_contact"] = contact_id



    #
    # zbT Second Test Customer
    #

    contact_id, errors = add_contact(
        customer_id=customers["zbt_second_test"],
        first_name="Test",
        last_name="Person",
        telephone="242-555-0000",
        email="second@2zbT.com"
    )


    if contact_id is None:

        raise RuntimeError(
            "Unable to create contact for "
            "zbT Second Test Customer: "
            + ", ".join(errors)
        )


    contacts["zbt_second_contact"] = contact_id



    #
    # zbT Third Test Customer
    #

    contact_id, errors = add_contact(
        customer_id=customers["zbt_third_test"],
        first_name="Test",
        last_name="Customer",
        telephone="242-555-0001",
        email="third@3zbT.com"
    )


    if contact_id is None:

        raise RuntimeError(
            "Unable to create contact for "
            "zbT Third Test Customer: "
            + ", ".join(errors)
        )


    contacts["zbt_third_contact"] = contact_id


    return contacts

def seed_commercials(
    customers
):

    from traffic.commercials import add_commercial


    print(
        "Creating commercials..."
    )


    commercials = {}


    #
    # zbT C1 Fake 30 sec ad
    #

    commercial_id, errors = add_commercial(
        customer_id=customers["zbt_test"],
        title="zbT C1 Fake 30 sec ad",
        length_seconds=30,
        filename="000002_000.wav",
        cart_number="000002",
        category_id=2
    )


    if commercial_id is None:

        raise RuntimeError(
            "Unable to create zbT C1 Fake 30 sec ad: "
            + ", ".join(errors)
        )


    commercials["c1_fake_30"] = {
        "id": commercial_id,
        "length": 30
    }



    #
    # zbT C2 Fake 60 sec ad
    #

    commercial_id, errors = add_commercial(
        customer_id=customers["zbt_second_test"],
        title="zbT C2 Fake 60 sec ad",
        length_seconds=60,
        filename="000003_000.wav",
        cart_number="000003",
        category_id=4
    )


    if commercial_id is None:

        raise RuntimeError(
            "Unable to create zbT C2 Fake 60 sec ad: "
            + ", ".join(errors)
        )


    commercials["c2_fake_60"] = {
        "id": commercial_id,
        "length": 60
    }



    #
    # zbT C3 Retail Test 30 sec ad
    #

    commercial_id, errors = add_commercial(
        customer_id=customers["zbt_third_test"],
        title="zbT C3 Retail Test 30 sec ad",
        length_seconds=30,
        filename="000004_000.wav",
        cart_number="000004",
        category_id=1
    )


    if commercial_id is None:

        raise RuntimeError(
            "Unable to create zbT C3 Retail Test 30 sec ad: "
            + ", ".join(errors)
        )


    commercials["c3_retail_30"] = {
        "id": commercial_id,
        "length": 30
    }



    return commercials


def seed_pending_spots(
    station_id,
    commercials,
    seed_date,
    spot_status
):

    from traffic.spots import (
        add_spot
    )


    print(
        "Creating pending spots..."
    )


    spots = []


    rotation = [
        commercials["c1_fake_30"],
        commercials["c2_fake_60"],
        commercials["c3_retail_30"],
    ]


    for hour in range(
        6,
        23
    ):

        for minute in (
            15,
            30,
            45
        ):

            current_seconds = (
                hour * 3600
                + minute * 60
            )


            for commercial in rotation:

                air_hour = current_seconds // 3600

                air_minute = (
                    current_seconds % 3600
                ) // 60

                air_second = (
                    current_seconds % 60
                )


                air_time = (
                    f"{air_hour:02d}:"
                    f"{air_minute:02d}:"
                    f"{air_second:02d}"
                )


                spot_id = add_spot(
                    station_id,
                    commercial["id"],
                    None,
                    None,
                    status=spot_status
                )


                spots.append(
                    spot_id
                )


                current_seconds += (
                    commercial["length"]
                )


    print(
        f"Created {len(spots)} pending spots."
    )


    return spots


def seed_spots(
    station_id,
    commercials,
    seed_date,
    spot_status
):

    from traffic.spots import (
        add_spot
    )


    print(
        "Creating scheduled spots..."
    )


    spots = []


    rotation = [
        commercials["c1_fake_30"],
        commercials["c2_fake_60"],
        commercials["c3_retail_30"],
    ]


    for hour in range(
        6,
        23
    ):

        for minute in (
            15,
            30,
            45
        ):

            current_seconds = (
                hour * 3600
                + minute * 60
            )


            for commercial in rotation:

                air_hour = current_seconds // 3600

                air_minute = (
                    current_seconds % 3600
                ) // 60

                air_second = (
                    current_seconds % 60
                )


                air_time = (
                    f"{air_hour:02d}:"
                    f"{air_minute:02d}:"
                    f"{air_second:02d}"
                )


                spot_id = add_spot(
                    station_id,
                    commercial["id"],
                    seed_date,
                    air_time,
                    status=spot_status
                )


                spots.append(
                    spot_id
                )


                current_seconds += (
                    commercial["length"]
                )


    print(
        f"Created {len(spots)} scheduled spots."
    )


    return spots


def seed_no_spots(
    station_id,
    commercials,
    seed_date,
    spot_status
):

    from traffic.spots import (
        add_spot
    )


    print(
        "Creating no spots..."
    )


    spots = []



    print(
        f"Created {len(spots)} no spots."
    )


    return spots


def update_spot_statuses(
    spots
):

    from traffic.spots import (
        export_spot,
        cancel_spot,
        complete_spot
    )


    print(
        "Updating spot statuses..."
    )


    if len(spots) < 3:

        raise RuntimeError(
            "Need at least 3 spots for status testing."
        )


    #
    # Spot 1:
    # Scheduled -> Exported
    #

    export_result = export_spot(
        spots[0]
    )


    #
    # Spot 2:
    # Scheduled -> Cancelled
    #

    cancel_result = cancel_spot(
        spots[1]
    )


    #
    # Spot 3:
    # Scheduled -> Exported -> Completed
    #

    export_complete_test = export_spot(
        spots[2]
    )


    complete_result = complete_spot(
        spots[2]
    )


    print(
        "Status test results:"
    )


    print(
        f"Spot {spots[0]} exported: {bool(export_result)}"
    )

    print(
        f"Spot {spots[1]} cancelled: {bool(cancel_result)}"
    )

    print(
        f"Spot {spots[2]} exported: {bool(export_complete_test)}"
    )

    print(
        f"Spot {spots[2]} completed: {bool(complete_result)}"
    )


    return {
        "exported": export_result,
        "cancelled": cancel_result,
        "completed": complete_result
    }


def main():

    parser = argparse.ArgumentParser(
        description="Seed zbTraffic test database"
    )

    parser.add_argument(
        "--date",
        help="Air date YYYY-MM-DD (default: today)"
    )

    parser.add_argument(
        "--test-statuses",
        action="store_true",
        help="Apply export/cancel/complete test statuses"
    )

    parser.add_argument(
        "--spot-status",
        choices=[
            "Pending",
            "Scheduled",
            "No"
        ],
        default="No",
        help="Initial status for seeded spots"
        # skip adding spots for "No"
    )

    args = parser.parse_args()


    if args.date:

        seed_date = args.date

    else:

        seed_date = date.today().isoformat()



    print(
        "Checking prerequisites..."
    )


    check_prerequisites(
        [
            "stations",
            "categories"
        ]
    )


    print(
        "Prerequisites OK."
    )


    station_id = get_first_station_id()


    if station_id is None:

        raise RuntimeError(
            "No station found."
        )


    customers = seed_customers()


    seed_contacts(
        customers
    )


    commercials = seed_commercials(
        customers
    )

    if args.spot_status == "Pending":

        spots = seed_pending_spots(
            station_id,
            commercials,
            seed_date,
            args.spot_status
        )
    elif args.spot_status == "Scheduled":

        spots = seed_spots(
            station_id,
            commercials,
            seed_date,
            args.spot_status
        )
    else:

        spots = seed_no_spots(
            station_id,
            commercials,
            seed_date,
            args.spot_status
        )


    if args.test_statuses:

        update_spot_statuses(
            spots
        )


    print(
        "Seed2 database complete."
    )


if __name__ == "__main__":

    main()
