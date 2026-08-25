# database/import_contract_items_csv.py

import csv
import sys
import os

from traffic.database import get_connection
from traffic.contract_items import add_contract_item


def find_contract(
    cursor,
    contract_number
):
    """
    Find a contract by contract number.
    """

    cursor.execute(
        """
        SELECT
            id,
            customer_id
        FROM contracts
        WHERE contract_number = ?
        """,
        (
            contract_number,
        )
    )

    rows = cursor.fetchall()

    if len(rows) == 0:
        return None

    if len(rows) > 1:
        raise ValueError(
            f"Multiple contracts found for "
            f"contract number '{contract_number}'"
        )

    return rows[0]


def find_customer(
    cursor,
    company_name
):
    """
    Find a customer by company name.
    """

    cursor.execute(
        """
        SELECT
            id
        FROM customers
        WHERE company_name = ?
        """,
        (
            company_name,
        )
    )

    rows = cursor.fetchall()

    if len(rows) == 0:
        return None

    if len(rows) > 1:
        raise ValueError(
            f"Multiple customers found for "
            f"company '{company_name}'"
        )

    return rows[0]["id"]


def find_commercial(
    cursor,
    customer_id,
    title
):
    """
    Find a commercial belonging to a specific customer.
    """

    cursor.execute(
        """
        SELECT
            id
        FROM commercials
        WHERE customer_id = ?
        AND title = ?
        """,
        (
            customer_id,
            title
        )
    )

    rows = cursor.fetchall()

    if len(rows) == 0:
        return None

    if len(rows) > 1:
        raise ValueError(
            f"Multiple commercials found for "
            f"customer ID {customer_id} "
            f"with title '{title}'"
        )

    return rows[0]["id"]


def import_contract_items_csv(
    csv_file
):
    """
    Import contract items from a CSV file.
    """

    connection = get_connection()
    cursor = connection.cursor()

    imported = 0
    errors = 0

    try:

        with open(
            csv_file,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            required_columns = [
                "contract",
                "commercial",
                "description",
                "quantity",
                "pricing_type",
                "unit_price",
                "total_price",
                "spot_length_seconds",
                "start_date",
                "end_date",
                "priority",
                "rotation_group",
                "notes"
            ]

            missing_columns = [
                column
                for column in required_columns
                if column not in reader.fieldnames
            ]

            if missing_columns:

                raise ValueError(
                    "Missing CSV columns: "
                    + ", ".join(missing_columns)
                )

            for row_number, row in enumerate(
                reader,
                start=2
            ):

                try:

                    contract_number = (
                        row["contract"].strip()
                    )

                    commercial_title = (
                        row["commercial"].strip()
                    )

                    description = (
                        row["description"].strip()
                    )

                    start_date = (
                        row["start_date"].strip()
                        or None
                    )

                    end_date = (
                        row["end_date"].strip()
                        or None
                    )

                    rotation_group = (
                        row["rotation_group"].strip()
                    )

                    notes = (
                        row["notes"].strip()
                    )

                    if not contract_number:
                        raise ValueError(
                            "Contract number is empty"
                        )



                    #
                    # Quantity
                    #

                    try:

                        quantity = int(
                            row["quantity"].strip()
                        )

                    except ValueError:

                        raise ValueError(
                            f"Invalid quantity "
                            f"'{row['quantity']}'"
                        )

                    if quantity < 0:

                        raise ValueError(
                            "Quantity cannot be negative"
                        )

                    #
                    # Pricing type
                    #

                    pricing_type = (
                        row["pricing_type"].strip()
                        or "PER_SPOT"
                    )

                    if pricing_type not in (
                        "PER_SPOT",
                        "TOTAL"
                    ):

                        raise ValueError(
                            f"Invalid pricing_type "
                            f"'{pricing_type}'"
                        )

                    #
                    # Prices
                    #
                    # Prices are stored in the CSV as integer cents.
                    #

                    try:

                        unit_price = int(
                            row["unit_price"].strip()
                        )

                    except ValueError:

                        raise ValueError(
                            f"Invalid unit_price "
                            f"'{row['unit_price']}'"
                        )


                    try:

                        total_price = int(
                            row["total_price"].strip()
                        )

                    except ValueError:

                        raise ValueError(
                            f"Invalid total_price "
                            f"'{row['total_price']}'"
                        )


                    if unit_price < 0:

                        raise ValueError(
                            "Unit price cannot be negative"
                        )


                    if total_price < 0:

                        raise ValueError(
                            "Total price cannot be negative"
                        )


                    #
                    # Spot length
                    #

                    spot_length_text = (
                        row["spot_length_seconds"].strip()
                    )

                    if spot_length_text:

                        try:

                            spot_length_seconds = int(
                                spot_length_text
                            )

                        except ValueError:

                            raise ValueError(
                                f"Invalid spot length "
                                f"'{row['spot_length_seconds']}'"
                            )

                        if spot_length_seconds <= 0:

                            raise ValueError(
                                "Spot length must be "
                                "greater than zero"
                            )

                    else:

                        spot_length_seconds = None


                    #
                    # Priority
                    #

                    try:

                        priority = int(
                            row["priority"].strip()
                            or "1"
                        )

                    except ValueError:

                        raise ValueError(
                            f"Invalid priority "
                            f"'{row['priority']}'"
                        )

                    #
                    # Find contract
                    #

                    contract = find_contract(
                        cursor,
                        contract_number
                    )

                    if contract is None:

                        raise ValueError(
                            f"Contract "
                            f"'{contract_number}' "
                            f"does not exist"
                        )

                    contract_id = contract["id"]
                    customer_id = contract["customer_id"]

                    #
                    # Find customer
                    #
                    # We retrieve the customer name through
                    # the contract so that the commercial
                    # relationship remains tied to the
                    # contract's customer.
                    #

                    cursor.execute(
                        """
                        SELECT
                            company_name
                        FROM customers
                        WHERE id = ?
                        """,
                        (
                            customer_id,
                        )
                    )

                    customer = cursor.fetchone()

                    if customer is None:

                        raise ValueError(
                            f"Customer ID "
                            f"{customer_id} does not exist"
                        )

                    company_name = customer["company_name"]

                    #
                    # Find commercial
                    #

                    if commercial_title:

                        commercial_id = find_commercial(
                            cursor,
                            customer_id,
                            commercial_title
                        )

                        if commercial_id is None:

                            raise ValueError(
                                f"Commercial "
                                f"'{commercial_title}' "
                                f"for customer "
                                f"'{company_name}' "
                                f"does not exist"
                            )

                    else:

                        commercial_id = None

                    #
                    # Add contract item
                    #

                    contract_item_id = add_contract_item(
                        contract_id=contract_id,
                        commercial_id=commercial_id,
                        description=description,
                        quantity=quantity,
                        pricing_type=pricing_type,
                        unit_price=unit_price,
                        total_price=total_price,
                        spot_length_seconds=spot_length_seconds,
                        start_date=start_date,
                        end_date=end_date,
                        priority=priority,
                        rotation_group=rotation_group,
                        notes=notes
                    )

                    print(
                        f"  Added contract item "
                        f"{contract_item_id}: "
                        f"{company_name} / "
                        f"{commercial_title}"
                    )

                    imported += 1

                except Exception as error:

                    print(
                        f"  ERROR on CSV row "
                        f"{row_number}: "
                        f"{error}"
                    )

                    errors += 1

        if errors:

            connection.rollback()

        else:

            connection.commit()

    finally:

        connection.close()

    return imported, errors


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: "
            "python3 -m database.import_contract_items_csv "
            "<csv_file>"
        )

        sys.exit(1)

    csv_file = sys.argv[1]

    if not os.path.isfile(csv_file):

        print(
            f"CSV file not found: {csv_file}"
        )

        sys.exit(1)

    print()
    print(
        "Importing contract items from:"
    )
    print(
        f"  {csv_file}"
    )
    print()

    imported, errors = (
        import_contract_items_csv(
            csv_file
        )
    )

    print()
    print(
        f"Imported {imported} contract items."
    )

    if errors:

        print(
            f"Encountered {errors} errors."
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
