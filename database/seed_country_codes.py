# File: database/seed_country_codes.py

"""
Seed the country_codes table with the initial country code(s).
"""

from traffic.country_codes import create_country_code


def seed_country_codes():
    """
    Add the initial country codes used by zbTraffic.
    """

    country_codes = [
        ("BS", "Bahamas"),
    ]

    for country_code, country_name in country_codes:
        country_id, errors = create_country_code(
            country_code,
            country_name
        )

        if errors:
            # The row may already exist, which is harmless when
            # the seed script is run more than once.
            if errors == ["Country code already exists."]:
                print(
                    f"{country_code} already exists - skipped."
                )
            else:
                print(
                    f"ERROR: {country_code}: "
                    f"{'; '.join(errors)}"
                )
        else:
            print(
                f"Added {country_code} - {country_name} "
                f"(ID {country_id})"
            )


if __name__ == "__main__":
    seed_country_codes()
