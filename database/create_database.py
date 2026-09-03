#!/usr/bin/env python3

# File: database/create_database.py

import sqlite3
import os


# Find the project directory
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATABASE_NAME = os.path.join(
    BASE_DIR,
    "data",
    "traffic.db"
)

# create db tables in this order:
# 01. categories
# 02. stations
# 04. tax_rates
# 04. programs
# 05. stopsets
# 06. customers
# 07. contacts
# 08. salespeople
# 09. commercials
# 10. contracts
# 11. contract_items
# 12. contract_item_rules
# 13. avails
# 14. spots
# 15. separation_rules
# 16. users
# 17. invoices
# 18. invoice_items
# 19. invoice_item_spots
# 19. payments
#

def create_database():

    # Make sure data directory exists
    database_directory = os.path.dirname(DATABASE_NAME)

    os.makedirs(
        database_directory,
        exist_ok=True
    )


    conn = sqlite3.connect(DATABASE_NAME)

    # Enable foreign key enforcement in SQLite
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    cursor = conn.cursor()


    tables = [

    """
    CREATE TABLE IF NOT EXISTS categories (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,
        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS stations (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        call_letters TEXT,
        frequency TEXT,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS tax_rates (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        rate INTEGER NOT NULL,

        effective_date TEXT NOT NULL,

        CHECK (rate >= 0),
        
        UNIQUE (name, rate, effective_date)
    )
    """,



    """
    CREATE TABLE IF NOT EXISTS programs (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        station_id INTEGER NOT NULL,

        name TEXT NOT NULL,

        description TEXT,

        start_time TEXT,
        end_time TEXT,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(station_id)
            REFERENCES stations(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS stopsets (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        program_id INTEGER NOT NULL,

        name TEXT,

        start_time TEXT,
        end_time TEXT,

        maximum_seconds INTEGER,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(program_id)
            REFERENCES programs(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS customers (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        company_name TEXT NOT NULL,

        address_line1 TEXT,
        address_line2 TEXT,

        locality TEXT,
        administrative_area TEXT,
        postal_code TEXT,
        country_code TEXT,

        telephone TEXT,
        email TEXT,

        category_id INTEGER,
        
        tax_status TEXT NOT NULL DEFAULT 'TAXABLE',

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,

        FOREIGN KEY(category_id)
            REFERENCES categories(id),
            
        CHECK (
            tax_status IN ('TAXABLE', 'EXEMPT')
        )
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS contacts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER NOT NULL,

        first_name TEXT,
        last_name TEXT,

        job_title TEXT,

        telephone TEXT,
        email TEXT,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(customer_id)
            REFERENCES customers(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS salespeople (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        first_name TEXT,
        last_name TEXT,

        telephone TEXT,
        email TEXT,

        commission_rate REAL DEFAULT 0,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS commercials (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER NOT NULL,

        title TEXT NOT NULL,

        length_seconds INTEGER,

        filename TEXT,

        cart_number TEXT,

        category_id INTEGER,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(customer_id)
            REFERENCES customers(id),


        FOREIGN KEY(category_id)
            REFERENCES categories(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS contracts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER NOT NULL,

        salesperson_id INTEGER NOT NULL,

        station_id INTEGER NOT NULL,

        contract_number TEXT NOT NULL DEFAULT '',

        description TEXT NOT NULL DEFAULT '',

        start_date TEXT,
        end_date TEXT,

        status TEXT NOT NULL DEFAULT 'Draft',

        notes TEXT NOT NULL DEFAULT '',

        active INTEGER NOT NULL DEFAULT 1,

        -- Payment timing for this contract:
        -- POSTPAID
        -- PREPAID
        payment_timing TEXT NOT NULL DEFAULT 'POSTPAID',

        -- Primarily used for POSTPAID contracts.
        payment_terms_days INTEGER NOT NULL DEFAULT 30,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(customer_id)
            REFERENCES customers(id),


        FOREIGN KEY(salesperson_id)
            REFERENCES salespeople(id),


        FOREIGN KEY(station_id)
            REFERENCES stations(id)

        -- Payment timing is intentionally kept at the contract
        -- level, rather than on the customer or invoice.
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS contract_items (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        contract_id INTEGER NOT NULL,

        commercial_id INTEGER,

        commercial_title TEXT NOT NULL DEFAULT '',

        description TEXT NOT NULL DEFAULT '',

        quantity INTEGER NOT NULL DEFAULT 0,

        -- PER_SPOT:
        --     unit_price is authoritative.
        --     total_price is calculated.
        --
        -- TOTAL:
        --     total_price is authoritative.
        --     unit_price is calculated and may contain many
        --     decimal places.
        pricing_type TEXT NOT NULL DEFAULT 'PER_SPOT',

        -- Prices are stored as integer cents.
        -- For PER_SPOT, unit_price is authoritative.
        -- For TOTAL, total_price is authoritative and
        -- unit_price is calculated.

        unit_price INTEGER,

        total_price INTEGER,



        spot_length_seconds INTEGER NOT NULL DEFAULT 0,

        start_date TEXT,
        end_date TEXT,

        priority INTEGER NOT NULL DEFAULT 1,

        rotation_group TEXT NOT NULL DEFAULT '',

        notes TEXT NOT NULL DEFAULT '',

        active INTEGER NOT NULL DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(contract_id)
            REFERENCES contracts(id),


        FOREIGN KEY(commercial_id)
            REFERENCES commercials(id),

        CHECK (
            pricing_type IN ('PER_SPOT', 'TOTAL')
        ),

        CHECK (
            quantity >= 0
        ),

        CHECK (
            unit_price IS NULL OR unit_price >= 0
        ),

        CHECK (
            total_price IS NULL OR total_price >= 0
        )
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS contract_item_rules (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        contract_item_id INTEGER NOT NULL,

        days_of_week TEXT,

        start_time TEXT,
        end_time TEXT,

        preferred_program_id INTEGER,

        preferred_stopset_id INTEGER,

        min_spots_per_day INTEGER DEFAULT NULL,
        
        max_spots_per_day INTEGER DEFAULT NULL,
        
        min_spots_per_week INTEGER DEFAULT NULL,
        
        max_spots_per_week INTEGER DEFAULT NULL,

        allow_news INTEGER DEFAULT 1,

        allow_special_events INTEGER DEFAULT 1,

        active INTEGER DEFAULT 1,

        notes TEXT,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(contract_item_id)
            REFERENCES contract_items(id),


        FOREIGN KEY(preferred_program_id)
            REFERENCES programs(id),


        FOREIGN KEY(preferred_stopset_id)
            REFERENCES stopsets(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS avails
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        station_id INTEGER NOT NULL,

        stopset_id INTEGER,

        air_date TEXT NOT NULL,

        start_time TEXT NOT NULL,

        length_seconds INTEGER NOT NULL,

        status TEXT DEFAULT 'Open',

        notes TEXT,

        created_date TEXT,

        modified_date TEXT,

        FOREIGN KEY(station_id)
            REFERENCES stations(id),

        FOREIGN KEY(stopset_id)
            REFERENCES stopsets(id)

    )
    """,


    """
    CREATE TABLE IF NOT EXISTS spots (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        station_id INTEGER NOT NULL,


        -- Optional until contract workflow is implemented.
        contract_item_id INTEGER,


        commercial_id INTEGER,


        -- NULL means the spot has not yet been assigned
        -- to a commercial avail.
        avail_id INTEGER,


        air_date TEXT,

        air_time TEXT,


        -- Traffic lifecycle only:
        -- Pending
        -- Scheduled
        -- Exported
        -- Completed
        -- Cancelled
        --
        -- Billing state is deliberately NOT part of this field.

        status TEXT DEFAULT 'Pending',


        actual_air_time TEXT,


        notes TEXT,


        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(station_id)
            REFERENCES stations(id),


        FOREIGN KEY(contract_item_id)
            REFERENCES contract_items(id),


        FOREIGN KEY(commercial_id)
            REFERENCES commercials(id),


        FOREIGN KEY(avail_id)
            REFERENCES avails(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS separation_rules (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        category1_id INTEGER NOT NULL,

        category2_id INTEGER NOT NULL,


        minimum_minutes INTEGER DEFAULT 0,

        active INTEGER DEFAULT 1,

        notes TEXT,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(category1_id)
            REFERENCES categories(id),


        FOREIGN KEY(category2_id)
            REFERENCES categories(id)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        password_hash TEXT NOT NULL,

        role TEXT,

        active INTEGER DEFAULT 1,

        created_date TEXT,
        modified_date TEXT
    )
    """,


    #
    # Billing / A/R
    #
    # An invoice represents a customer charge. It may be created
    # before any spots air (for PREPAID contracts), or later from
    # completed spots (for POSTPAID contracts).
    #
    # Invoice status is deliberately separate from spot status.
    #
    # Draft
    # Issued
    # Void
    #
    # Paid / partially paid / overdue are derived from payments,
    # invoice total and due date.
    #


    """
    CREATE TABLE IF NOT EXISTS invoice_sequences (

        year INTEGER PRIMARY KEY,

        last_number INTEGER NOT NULL DEFAULT 0,

        CHECK (year >= 2000),

        CHECK (last_number >= 0)
    )
    """,



    """
    CREATE TABLE IF NOT EXISTS invoices (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER NOT NULL,

        contract_id INTEGER,

        invoice_number TEXT UNIQUE,

        invoice_date TEXT,

        due_date TEXT,

        status TEXT NOT NULL DEFAULT 'Draft',

        subtotal INTEGER NOT NULL DEFAULT 0,
        
        taxable_subtotal INTEGER NOT NULL DEFAULT 0,

        tax INTEGER NOT NULL DEFAULT 0,

        total INTEGER NOT NULL DEFAULT 0,

        notes TEXT,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(customer_id)
            REFERENCES customers(id),


        FOREIGN KEY(contract_id)
            REFERENCES contracts(id),

        CHECK (
            status IN ('Draft', 'Issued', 'Void')
        ),

        CHECK (subtotal >= 0),
        
        CHECK (taxable_subtotal >= 0),

        CHECK (tax >= 0),

        CHECK (total >= 0)
    )
    """,


    """
    CREATE TABLE IF NOT EXISTS invoice_items (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        invoice_id INTEGER NOT NULL,

        contract_item_id INTEGER,

        description TEXT NOT NULL,
        
        taxable INTEGER NOT NULL DEFAULT 1,

        quantity REAL NOT NULL DEFAULT 1,
        
        -- Tax rate stored in basis points:
        --     0    = 0%
        --     500  = 5%
        --     750  = 7.5%
        --     1500 = 15%
        
        tax_rate INTEGER NOT NULL DEFAULT 0,

        unit_price INTEGER,

        amount INTEGER NOT NULL DEFAULT 0,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(invoice_id)
            REFERENCES invoices(id),


        FOREIGN KEY(contract_item_id)
            REFERENCES contract_items(id),
            
        CHECK (taxable IN (0, 1)),

        CHECK (quantity >= 0),
        
        CHECK (tax_rate >= 0),

        CHECK (
            unit_price IS NULL OR unit_price >= 0
        ),

        CHECK (amount >= 0)
    )
    """,


    #
    # Links actual completed spots to the invoice item that billed them.
    #
    # This is what prevents the same spot from being billed twice.
    #
    # active = 1:
    #     This association is currently valid.
    #
    # active = 0:
    #     Historical/reversed association, such as after voiding
    #     an invoice.
    #

    """
    CREATE TABLE IF NOT EXISTS invoice_item_spots (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        invoice_item_id INTEGER NOT NULL,

        spot_id INTEGER NOT NULL,

        active INTEGER NOT NULL DEFAULT 1,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(invoice_item_id)
            REFERENCES invoice_items(id),


        FOREIGN KEY(spot_id)
            REFERENCES spots(id),

        CHECK (active IN (0, 1))
    )
    """,


    #
    # Payments
    #
    # invoice_id may be NULL for an unapplied customer payment/credit.
    #

    """
    CREATE TABLE IF NOT EXISTS payments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_id INTEGER NOT NULL,

        invoice_id INTEGER,

        payment_date TEXT NOT NULL,
        
        -- Amount stored as integer cents.
        amount INTEGER NOT NULL,

        payment_method TEXT,

        reference TEXT,

        notes TEXT,

        created_date TEXT,
        modified_date TEXT,


        FOREIGN KEY(customer_id)
            REFERENCES customers(id),


        FOREIGN KEY(invoice_id)
            REFERENCES invoices(id),

        CHECK (amount > 0)
    )
    """

    ]


    for table in tables:
        cursor.execute(table)


    #
    # Indexes used by existing traffic operations and the new
    # billing/A/R operations.
    #

    indexes = [

        """
        CREATE INDEX IF NOT EXISTS
        idx_contract_items_contract
        ON contract_items(contract_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_contract_item_rules_item
        ON contract_item_rules(contract_item_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_avails_air_date
        ON avails(air_date)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_spots_contract_item
        ON spots(contract_item_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_spots_air_date
        ON spots(air_date)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_spots_status
        ON spots(status)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_invoices_customer
        ON invoices(customer_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_invoices_contract
        ON invoices(contract_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_invoices_due_date
        ON invoices(due_date)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_invoice_items_invoice
        ON invoice_items(invoice_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_invoice_items_contract_item
        ON invoice_items(contract_item_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_invoice_item_spots_invoice_item
        ON invoice_item_spots(invoice_item_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_invoice_item_spots_spot
        ON invoice_item_spots(spot_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_payments_customer
        ON payments(customer_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_payments_invoice
        ON payments(invoice_id)
        """,

        #
        # A spot may have only ONE active billing association.
        #
        # Historical inactive associations are allowed.
        #

        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        ux_invoice_item_spots_active_spot
        ON invoice_item_spots(spot_id)
        WHERE active = 1
        """
    ]


    for index in indexes:
        cursor.execute(index)


    #insert_default_data(
    #    cursor
    #)

    conn.commit()
    conn.close()



if __name__ == "__main__":

    create_database()

    print("Traffic database created:")
    print(DATABASE_NAME)