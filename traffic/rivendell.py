#!/usr/bin/env python3

# File: traffic/rivendell.py


from traffic.spots import (
    list_spots_by_date,
    export_spot
)


#
# Rivendell format specification
#

DEFAULT_RECORD_TYPE = "02"

RECORD_LENGTH = 80


RECORD_TYPE_START = 0
RECORD_TYPE_END = 2

CART_NUMBER_START = 3
CART_NUMBER_END = 9

TITLE_START = 12
TITLE_END = 37

LENGTH_START = 37
LENGTH_END = 41

MONTH_START = 44
MONTH_END = 46

DAY_START = 47
DAY_END = 49

YEAR_START = 50
YEAR_END = 52

HOUR_START = 53
HOUR_END = 55

MINUTE_START = 56
MINUTE_END = 58

SECOND_START = 59
SECOND_END = 61



def put_field(
    line,
    start,
    end,
    value
):

    width = end - start

    text = str(value)

    text = text[:width]

    text = text.ljust(
        width
    )

    line[start:end] = list(text)



def format_rivendell_spot(
    spot,
    record_type=DEFAULT_RECORD_TYPE
):

    line = [" "] * RECORD_LENGTH


    year, month, day = (
        spot["air_date"].split("-")
    )

    hour, minute, second = (
        spot["air_time"].split(":")
    )


    length_seconds = spot["length_seconds"]

    minutes = length_seconds // 60

    seconds = length_seconds % 60


    length = (
        f"{minutes:02d}{seconds:02d}"
    )


    put_field(
        line,
        RECORD_TYPE_START,
        RECORD_TYPE_END,
        record_type
    )

    put_field(
        line,
        CART_NUMBER_START,
        CART_NUMBER_END,
        spot["cart_number"]
    )

    put_field(
        line,
        TITLE_START,
        TITLE_END,
        spot["title"]
    )

    put_field(
        line,
        LENGTH_START,
        LENGTH_END,
        length
    )

    put_field(
        line,
        MONTH_START,
        MONTH_END,
        month
    )

    put_field(
        line,
        DAY_START,
        DAY_END,
        day
    )

    put_field(
        line,
        YEAR_START,
        YEAR_END,
        year[2:4]
    )

    put_field(
        line,
        HOUR_START,
        HOUR_END,
        hour
    )

    put_field(
        line,
        MINUTE_START,
        MINUTE_END,
        minute
    )

    put_field(
        line,
        SECOND_START,
        SECOND_END,
        second
    )


    return "".join(line)



def export_rivendell_log(
    air_date,
    filename
):

    """
    Export scheduled spots for one date
    to a Rivendell traffic log file.
    """


    spots = list_spots_by_date(
        air_date
    )


    exported = 0


    with open(
        filename,
        "w"
    ) as logfile:


        for spot in spots:


            if spot["status"] not in (
                "Scheduled",
                "Exported"
            ):

                continue


            logfile.write(
                format_rivendell_spot(
                    spot
                )
            )

            logfile.write(
                "\n"
            )

            export_spot(
                spot["id"]
            )

            exported += 1


    return exported
