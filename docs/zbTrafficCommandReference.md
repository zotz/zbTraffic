# zbTraffic Command Reference

## Overview

This document lists the current zbTraffic command-line utilities, their purpose, and examples of usage.

Commands are located in:

```
zbTraffic/
└── commands/
```

Commands should normally be run from the project directory using Python module execution:

```bash
python3 -m commands.command_name
```

Example:

```bash
python3 -m commands.customer_list
```

Using `-m` allows Python to correctly locate the `traffic` package.

---

# Database Commands

## `database/create_database.py`

## Purpose

Creates the zbTraffic database.

This creates the required tables for:

* stations
* programs
* stopsets
* categories
* customers
* contacts
* commercials
* contracts
* contract items
* contract rules
* scheduled spots
* separation rules
* users

## Usage

```bash
python3 -m database.create_database
```

## Notes

During development, this is commonly used after deleting the existing database.

Typical development cycle:

```
Delete database
Create database
Seed database
Test commands
```

---

## `database/seed_database.py`

## Purpose

Populates a newly created database with test and default data.

Used to avoid manually re-entering development data after rebuilding the database.

## Usage

```bash
python3 -m database.seed_database
```

## Expected Data

May include:

* default categories
* test station
* House salesperson
* test customers
* test commercials
* test contracts

---

# Customer Commands

## `customer_add.py`

## Purpose

Adds a new customer.

## Usage

```bash
python3 -m commands.customer_add
```

## Example

```
Company Name:
Lumex Instruments

Telephone:
555-1234

Email:
sales@example.com
```

---

## `customer_list.py`

## Purpose

Displays customers.

## Usage

```bash
python3 -m commands.customer_list
```

## Future Options

Planned:

```
--inactive
--all
--table
```

---

## `customer_get.py`

## Purpose

Displays one customer.

## Usage

```bash
python3 -m commands.customer_get 1
```

---

## `customer_edit.py`

## Purpose

Edits customer information.

Current editable fields:

* company name
* telephone
* email

## Usage

```bash
python3 -m commands.customer_edit 1
```

---

## `customer_activate.py`

## Purpose

Activates a previously deactivated customer.

## Usage

```bash
python3 -m commands.customer_activate 1
```

---

## `customer_deactivate.py`

## Purpose

Deactivates a customer.

## Usage

```bash
python3 -m commands.customer_deactivate 1
```

---

# Commercial Commands

Commercials represent advertisements.

Relationship:

```
Customer
   |
Commercial
   |
Scheduled Spot
```

---

## `commercial_add.py`

## Purpose

Adds a commercial.

## Usage

```bash
python3 -m commands.commercial_add
```

## Stored Information

Includes:

* title
* cart number
* length
* filename
* category
* customer association

Example:

```
Title:
Fake 30 sec ad

Cart Number:
000002

Length:
30
```

---

## `commercial_list.py`

## Purpose

Lists commercials.

## Usage

```bash
python3 -m commands.commercial_list
```

---

## `commercial_get.py`

## Purpose

Displays one commercial.

## Usage

```bash
python3 -m commands.commercial_get 1
```

---

## `commercial_edit.py`

## Purpose

Edits commercial information.

## Usage

```bash
python3 -m commands.commercial_edit 1
```

---

## `commercial_activate.py`

## Purpose

Activates a commercial.

## Usage

```bash
python3 -m commands.commercial_activate 1
```

---

## `commercial_deactivate.py`

## Purpose

Deactivates a commercial.

## Usage

```bash
python3 -m commands.commercial_deactivate 1
```

---

# Category Commands

Categories are used for:

* commercial grouping
* separation rules
* future scheduling rules

---

## `category_add.py`

## Usage

```bash
python3 -m commands.category_add
```

---

## `category_list.py`

## Usage

```bash
python3 -m commands.category_list
```

---

## `category_activate.py`

## Usage

```bash
python3 -m commands.category_activate 1
```

---

# Contact Commands

Contacts belong to customers.

Relationship:

```
Customer
   |
Contact
```

---

## `contact_add.py`

## Usage

```bash
python3 -m commands.contact_add
```

---

## `contact_list.py`

## Usage

```bash
python3 -m commands.contact_list
```

---

# Scheduled Spot Commands

Scheduled spots represent actual airings.

Relationship:

```
Commercial
     |
Scheduled Spot
     |
Rivendell Export
```

---

## `scheduled_spot_add.py`

## Purpose

Creates a scheduled airing.

## Usage

```bash
python3 -m commands.scheduled_spot_add
```

Example:

```
Commercial:
1

Air Date:
2026-08-01

Air Time:
06:20:00
```

---

## `scheduled_spot_list.py`

## Purpose

Lists scheduled spots.

## Usage

```bash
python3 -m commands.scheduled_spot_list
```

---

## `scheduled_spot_edit.py`

## Purpose

Edits a scheduled spot.

Current editable fields:

* air date
* air time
* status
* notes

## Usage

```bash
python3 -m commands.scheduled_spot_edit 1
```

---

## `scheduled_spot_cancel.py`

## Purpose

Cancels a scheduled spot.

## Usage

```bash
python3 -m commands.scheduled_spot_cancel 1
```

Changes:

```
status = Cancelled
```

---

## `scheduled_spot_log.py`

## Purpose

Displays a traffic log view for a specific date.

## Usage

```bash
python3 -m commands.scheduled_spot_log 2026-08-01
```

Example:

```
Traffic Log: 2026-08-01

06:20:00  000002  Fake 30 sec ad  Scheduled
06:30:00  000003  Fake 60 sec ad  Scheduled
```

---

# Rivendell Commands

## `export_rivendell_log.py`

## Purpose

Exports scheduled spots into Rivendell fixed-width traffic log format.

## Usage

```bash
python3 -m commands.export_rivendell_log 2026-08-01
```

## Current Export Fields

```
Record Type
Cart Number
Title
Length
Month
Day
Year
Hour
Minute
Second
```

## Example Output

```
02 000002   Fake 30 sec ad           0030   08 01 26 06 20 00
02 000003   Fake 60 sec ad           0060   08 01 26 06 30 00
```

---

# Python Modules

These are not command-line programs but provide functionality used by commands.

---

## `traffic.customers`

Customer management functions.

Examples:

```python
add_customer()

get_customer()

update_company_name()

deactivate_customer()
```

---

## `traffic.commercials`

Commercial management functions.

Examples:

```python
add_commercial()

get_commercial()

update_length()

update_cart_number()
```

---

## `traffic.scheduled_spots`

Scheduled spot functions.

Examples:

```python
add_scheduled_spot()

get_scheduled_spot()

update_scheduled_spot()

cancel_scheduled_spot()

export_scheduled_spot()
```

---

## `traffic.rivendell`

Rivendell export formatting.

Examples:

```python
format_rivendell_spot()

export_rivendell_log()
```

---

# Future Improvements

## Table Output

All list commands should eventually support:

```bash
--table
```

Example:

```bash
python3 -m commands.customer_list --table
```

---

## Station-Specific Configuration

Future station configuration may include:

* export directory
* filename format
* automation system type
* exporter options

Example:

```
Station A
    Automation:
        Rivendell

    Export Path:
        /var/log/rivendell/


Station B
    Automation:
        Other System
```

---

## Automatic Scheduling

Future workflow:

```
Contracts
    |
Contract Items
    |
Scheduling Rules
    |
Scheduled Spots
    |
Export
```

Current development workflow creates scheduled spots manually.

---

# Current Development Focus

The current priority is:

```
zbTraffic Database
        |
Commercials
        |
Scheduled Spots
        |
Rivendell Export
        |
Rivendell Import Test
```

Automatic scheduling will be developed after the basic export/import workflow is proven.
