# File: database/generate_avails_range.py

import sys
from datetime import datetime, timedelta

from traffic.avails import generate_avails_for_date


def get_dates(
    start_date,
    end_date
):
    start = datetime.strptime(
        start_date,
        "%Y-%m-%d"
    )

    end = datetime.strptime(
        end_date,
        "%Y-%m-%d"
    )


    dates = []

    current = start


    while current <= end:

        dates.append(
            current.strftime("%Y-%m-%d")
        )

        current += timedelta(
            days=1
        )


    return dates



def main():

    if len(sys.argv) < 4:

        print(
            "Usage:"
        )

        print(
            "python3 -m database.generate_avails_range <station_id> <start_date> <end_date>"
        )

        return


    station_id = int(
        sys.argv[1]
    )

    start_date = sys.argv[2]

    end_date = sys.argv[3]


    dates = get_dates(
        start_date,
        end_date
    )


    for air_date in dates:

        print(
            f"Generating avails: {air_date}"
        )

        generate_avails_for_date(
            station_id,
            air_date
        )



if __name__ == "__main__":

    main()
