#!/usr/bin/env python3

# File: traffic/utilities.py

from datetime import datetime


def current_timestamp():

    """
    Return the current date and time in the
    standard zbTraffic timestamp format.

    Example:
        2026-07-27 14:35:42
    """

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

def normalize_time(
    value
):

    if not value:

        return value


    parts = value.split(":")


    if len(parts) == 2:

        return value + ":00"


    return value
