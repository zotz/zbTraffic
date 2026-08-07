#!/usr/bin/env python3

# File: database/seed_stopsets.py

from traffic.stopsets import add_stopset


def seed_stopsets():


    stopsets = [

        #
        # Morning Show
        # Program ID 2
        # 6am to 10am
        #


        # 6am
        (
            2,
            "Morning Break 1",
            "06:15",
            "06:18",
            180
        ),

        (
            2,
            "Morning Break 2",
            "06:30",
            "06:33",
            180
        ),

        (
            2,
            "Morning Break 3",
            "06:45",
            "06:48",
            180
        ),


        # 7am
        (
            2,
            "Morning Break 4",
            "07:15",
            "07:18",
            180
        ),

        (
            2,
            "Morning Break 5",
            "07:30",
            "07:33",
            180
        ),

        (
            2,
            "Morning Break 6",
            "07:45",
            "07:48",
            180
        ),


        # 8am
        (
            2,
            "Morning Break 7",
            "08:15",
            "08:18",
            180
        ),

        (
            2,
            "Morning Break 8",
            "08:30",
            "08:33",
            180
        ),

        (
            2,
            "Morning Break 9",
            "08:45",
            "08:48",
            180
        ),


        # 9am
        (
            2,
            "Morning Break 10",
            "09:15",
            "09:18",
            180
        ),

        (
            2,
            "Morning Break 11",
            "09:30",
            "09:33",
            180
        ),

        (
            2,
            "Morning Break 12",
            "09:45",
            "09:48",
            180
        ),

        #
        # Midday Show
        # Program ID 3
        # 10am to 3pm
        #

        # 10am
        (
            3,
            "Midday Break 1",
            "10:15",
            "10:18",
            180
        ),

        (
            3,
            "Midday Break 2",
            "10:30",
            "10:33",
            180
        ),

        (
            3,
            "Midday Break 3",
            "10:45",
            "10:48",
            180
        ),

        # 11am
        (
            3,
            "Midday Break 4",
            "11:15",
            "11:18",
            180
        ),

        (
            3,
            "Midday Break 5",
            "11:30",
            "11:33",
            180
        ),

        (
            3,
            "Midday Break 6",
            "11:45",
            "11:48",
            180
        ),

        # 12noon
        (
            3,
            "Midday Break 7",
            "12:15",
            "12:18",
            180
        ),

        (
            3,
            "Midday Break 8",
            "12:30",
            "12:33",
            180
        ),

        (
            3,
            "Midday Break 9",
            "12:45",
            "12:48",
            180
        ),


        # 1pm
        (
            3,
            "Midday Break 10",
            "13:15",
            "13:18",
            180
        ),

        (
            3,
            "Midday Break 11",
            "13:30",
            "13:33",
            180
        ),

        (
            3,
            "Midday Break 12",
            "13:45",
            "13:48",
            180
        ),


        # 2pm
        (
            3,
            "Midday Break 13",
            "14:15",
            "14:18",
            180
        ),

        (
            3,
            "Midday Break 14",
            "14:30",
            "14:33",
            180
        ),

        (
            3,
            "Midday Break 15",
            "14:45",
            "14:48",
            180
        ),


 



        #
        # Afternoon Drive
        # Program ID 4
        # 3pm to 7pm
        #

        # 3pm
        (
            4,
            "Drive Break 1",
            "15:15",
            "15:18",
            180
        ),

        (
            4,
            "Drive Break 2",
            "15:30",
            "15:33",
            180
        ),

        (
            4,
            "Drive Break 3",
            "15:45",
            "15:48",
            180
        ),

        # 4pm
        (
            4,
            "Drive Break 4",
            "16:15",
            "16:18",
            180
        ),

        (
            4,
            "Drive Break 5",
            "16:30",
            "16:33",
            180
        ),

        (
            4,
            "Drive Break 6",
            "16:45",
            "16:48",
            180
        ),

        # 5pm
        (
            4,
            "Drive Break 7",
            "17:15",
            "17:18",
            180
        ),

        (
            4,
            "Drive Break 8",
            "17:30",
            "17:33",
            180
        ),

        (
            4,
            "Drive Break 9",
            "17:45",
            "17:48",
            180
        ),

        # 6pm
        (
            4,
            "Drive Break 10",
            "18:15",
            "18:18",
            180
        ),

        (
            4,
            "Drive Break 11",
            "18:30",
            "18:33",
            180
        ),

        (
            4,
            "Drive Break 12",
            "18:45",
            "18:48",
            180
        ),









    ]


    for stopset in stopsets:

        stopset_id = add_stopset(
            stopset[0],
            stopset[1],
            stopset[2],
            stopset[3],
            stopset[4]
        )

        print(
            f"Added stopset ID {stopset_id}: {stopset[1]}"
        )



if __name__ == "__main__":

    seed_stopsets()
