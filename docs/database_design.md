# zbTraffic Database Design

## Overview

zbTraffic is intended to be a radio traffic (commercial scheduling) system designed to run on Linux. The initial development uses Python and SQLite, with the goal of supporting MySQL and MariaDB in the future.

The guiding design philosophy is:

* Preserve historical data whenever possible.
* Prefer deactivating records rather than deleting them.
* Separate business entities into logical components.
* Keep the scheduling engine independent from the user interface.
* Develop and test small command-line utilities before implementing the graphical interface.

## Database Architecture

The database is divided into five major areas:

1. Station Management
2. Customer Management
3. Commercial Management
4. Contract Management
5. Scheduling Management

```
                Stations
                    |
                 Programs
                    |
                 Stopsets
                    |
                    |
                    V
Customers ---------------- Commercials
     |                          |
     |                          |
  Contacts                      |
     |                          |
     +---------- Contracts -----+
                     |
                     |
                Contract Items
                     |
                     |
             Contract Item Rules
                     |
                     |
               Scheduled Spots
                     |
                     |
               Separation Rules
                     |
                     |
                    Users
```

## Stations

The stations table stores information about radio stations.

Fields:

* id
* name
* call_letters
* frequency
* active
* created_date
* modified_date

Examples:

* ZB Radio
* Island FM
* Classic Hits 95.9

## Programs

Programs are associated with stations.

Examples:

* Morning Show
* Midday Mix
* Afternoon Drive
* Evening Jazz

Fields:

* id
* station_id
* name
* description
* start_time
* end_time
* active
* created_date
* modified_date

## Stopsets

A stopset represents a commercial break within a program.

Examples:

* 7:15 AM Stopset
* 8:30 AM News Break
* Noon Commercial Break

Fields:

* id
* program_id
* name
* start_time
* end_time
* maximum_seconds
* active

The maximum_seconds field will eventually be used by the scheduling engine to prevent over-filling a stopset.

## Customers

Customers are businesses that purchase advertising.

Examples:

* Joe's Hardware
* ABC Plumbing
* Island Marine Supply

Fields:

* id
* company_name
* address information
* telephone
* email
* category_id
* active
* created_date
* modified_date

The customer record represents the company itself and not an individual contact person.

The current design philosophy is:

* Preserve customer history.
* Deactivate customers rather than deleting them.
* Maintain historical contract information.

## Contacts

Customers may have multiple contacts.

Examples:

* Sales Manager
* Marketing Director
* Accounts Payable
* General Manager

Fields:

* id
* customer_id
* first_name
* last_name
* title
* telephone
* email
* active

## Salespeople

Salespeople represent account executives responsible for selling advertising contracts.

Fields:

* id
* first_name
* last_name
* telephone
* email
* commission_rate
* active

Future versions may support:

* commission reporting
* salesperson summaries
* sales statistics

## Commercials

Commercials represent the actual audio assets owned by customers.

Examples:

* Summer Sale (30 seconds)
* Truck Event (60 seconds)
* Christmas Promotion (15 seconds)

Fields:

* id
* customer_id
* title
* length_seconds
* filename
* category_id
* active
* created_date

A commercial is intentionally separate from a contract. The same commercial may be used in multiple advertising campaigns.

Examples:

```
Customer:
    Joe's Hardware

Commercial:
    Summer Sale

May be used by:

    June Campaign
    August Campaign
    Christmas Campaign
```

## Contracts

Contracts represent agreements between the station and the customer.

Examples:

* July Campaign
* Christmas Campaign
* Annual Advertising Agreement

Fields:

* id
* customer_id
* salesperson_id
* contract_number
* start_date
* end_date
* total_value
* status
* notes
* created_date
* modified_date

Examples of contract status values might include:

* Pending
* Active
* Completed
* Cancelled
* Expired

## Contract Items

Contract items define the individual advertising purchases contained within a contract.

Examples:

```
Contract:
    Summer Campaign

Contains:

    50 x 30 second spots

and

    20 x 60 second spots
```

Fields:

* id
* contract_id
* commercial_id
* quantity
* start_date
* end_date
* priority
* rotation
* notes

A contract may contain multiple contract items.

## Contract Item Rules

Contract item rules define scheduling restrictions.

Fields:

* id
* contract_item_id
* day_of_week
* start_time
* end_time
* preferred_program_id
* preferred_stopset_id
* spots_per_day
* spots_per_week
* allow_news
* allow_special_events

Examples of future scheduling rules include:

* weekdays only
* weekends only
* morning drive only
* maximum two spots per day
* maximum ten spots per week
* preferred stopset placement

These rules will eventually become part of the scheduling engine.

## Scheduled Spots

Scheduled spots represent commercials that have been assigned to a station schedule.

Fields:

* id
* station_id
* contract_item_id
* commercial_id
* air_date
* air_time
* status
* actual_air_time
* notes

Examples of status values may include:

* Scheduled
* Aired
* Missed
* Cancelled
* Make-Good Required

This table is expected to become one of the most important tables within the system.

It will support:

* traffic reports
* affidavits of performance
* billing
* make-goods
* schedule verification
* historical reporting

## Categories

Categories provide logical groupings for both customers and commercials.

Examples:

* Automotive
* Retail
* Restaurant
* Political
* Public Service
* Financial Services

Categories are also used by separation rules.

## Separation Rules

Separation rules prevent inappropriate commercial placement.

Fields:

* id
* category1_id
* category2_id
* minimum_minutes

Examples include:

```
Automotive
    minimum separation:
    30 minutes

Political
    minimum separation:
    60 minutes

Retail
    minimum separation:
    15 minutes
```

Future versions may support more sophisticated rules involving:

* customers
* categories
* stations
* programs
* stopsets

## Users

The users table stores application user accounts.

Fields:

* id
* username
* password_hash
* role
* active

Possible roles include:

* Administrator
* Traffic Manager
* Sales
* Programming
* Read Only

Passwords are never stored in plain text.

## Future Development Goals

The planned development order is currently:

1. Customer Management
2. Commercial Management
3. Contract Management
4. Scheduling Rules
5. Scheduling Engine
6. Reporting
7. Billing Support
8. Graphical User Interface

## Design Philosophy

Several design principles guide zbTraffic:

* Preserve historical information whenever possible.
* Deactivate records instead of deleting them.
* Keep scheduling logic separate from user interface code.
* Keep business logic separate from database access.
* Support multiple database backends.
* Build and test small components before integrating larger systems.
* Favor readability and maintainability over clever implementations.

The ultimate goal is to provide a flexible radio traffic scheduling system that can support multiple stations, complex scheduling requirements, and future expansion while remaining understandable and maintainable.

