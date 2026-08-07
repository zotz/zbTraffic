# File: commands/spots_generate.py

import sys

from traffic.spot_generator import (
    generate_spots_for_contract_item
)



def main():

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "python3 -m commands.spots_generate <contract_item_id>"
        )

        return


    contract_item_id = int(
        sys.argv[1]
    )


    spots = generate_spots_for_contract_item(
        contract_item_id
    )


    print()

    print(
        f"Generated {len(spots)} spots."
    )

    print()


    for spot_id in spots:

        print(
            f"Spot ID: {spot_id}"
        )


    print()



if __name__ == "__main__":

    main()
