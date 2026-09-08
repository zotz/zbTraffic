# database/seed_station_invoice_settings.py

import sqlite3
from datetime import datetime

DB_PATH = "data/traffic.db"


def seed_station_invoice_settings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        stations = conn.execute("""
            SELECT id, name
            FROM stations
            ORDER BY id
        """).fetchall()

        if not stations:
            print("No stations found.")
            return

        now = datetime.now().isoformat(timespec="seconds")

        for station in stations:
            station_id = station["id"]
            station_name = station["name"]

            # ---------------------------------------------------------
            # Sample invoice settings
            #
            # Change these paths to the actual logo locations you
            # installed for your testing.
            # ---------------------------------------------------------

            biller_block = (
                "ZB Broadcasting Ltd.\n"
                "123 Broadcasting Way\n"
                "Nassau, Bahamas\n"
                "Phone: (242) 555-0100\n"
                "Email: billing@example.com"
            )

            corporate_logo = "data/incoice_assets/zbT_corporate_logo.png"
            station_logo = "data/invoice_assets/zbT_station_logo.png"

            payment_instructions = (
                "Payment is due according to the terms shown on this invoice.\n"
                "Please reference the invoice number with your payment."
            )

            invoice_footer = (
                "Thank you for your business.\n"
                "Please contact our billing department with any questions."
            )

            conn.execute("""
                INSERT INTO station_invoice_settings (
                    station_id,
                    biller_block,
                    corporate_logo,
                    station_logo,
                    payment_instructions,
                    invoice_footer,
                    created_date,
                    modified_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(station_id) DO UPDATE SET
                    biller_block = excluded.biller_block,
                    corporate_logo = excluded.corporate_logo,
                    station_logo = excluded.station_logo,
                    payment_instructions = excluded.payment_instructions,
                    invoice_footer = excluded.invoice_footer,
                    modified_date = excluded.modified_date
            """, (
                station_id,
                biller_block,
                corporate_logo,
                station_logo,
                payment_instructions,
                invoice_footer,
                now,
                now,
            ))

            print(f"Updated invoice settings for station {station_id}: {station_name}")

        conn.commit()
        print("\nStation invoice settings seeded successfully.")

    finally:
        conn.close()


if __name__ == "__main__":
    seed_station_invoice_settings()
