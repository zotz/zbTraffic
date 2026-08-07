# zbTraffic Version 1 - Proposed Database Structure, Workflow and Architecture

## Purpose

This document describes the proposed architecture for zbTraffic Version 1.

The intent is **not** to perfectly model every traffic system in use, but rather to provide a practical design that allows a working system to be developed while leaving room for future expansion.

---

# Design Goals

zbTraffic should:

* Be independent of any particular automation system.
* Support Rivendell as the initial export target.
* Allow future support for other automation systems.
* Separate programming decisions from traffic decisions.
* Allow stations to grow into more advanced scheduling over time.

---

# Overall Workflow

```
Programming
        |
        v
Program Schedule
        |
        v
Traffic Clock Assignment
        |
        v
Commercial Break Definitions
        |
        v
Daily Avail Generation
        |
        v
Customer Orders / Contracts
        |
        v
Traffic Scheduling
        |
        v
Scheduled Spots
        |
        v
Export
        |
        v
Automation System
        |
        v
Playback Completion
```

---

# Separation of Responsibilities

## Programming

Programming determines:

* What programs air
* What dayparts exist
* Which traffic clocks are used
* Where commercial breaks occur

Programming **does not** decide which commercials air.

---

## Sales

Sales determines:

* Which customers advertise
* What commercials they own
* How many spots they purchase
* Which dayparts they purchase

Sales **does not** decide where commercials are scheduled.

---

## Traffic

Traffic determines:

* Which commercial fills which available break
* Separation rules
* Conflicts
* Export

---

## Automation (Rivendell)

Automation determines:

* Actual playback
* Music
* IDs
* Jingles
* Execution

Automation does **not** determine commercial inventory.

---

# Rivendell Relationship

zbTraffic should **not** attempt to duplicate Rivendell clocks.

Instead:

```
Rivendell Clock
        |
        |
        +------ loosely related ------+
                                      |
                               zbTraffic Clock
```

Each zbTraffic Clock may optionally reference a Rivendell Clock Code.

Example:

```
zbTraffic Clock

Code:
MD1

Name:
Morning Drive Standard

Rivendell Clock Code:
MD1
```

The relationship is informational.

---

# Proposed Database Structure

## Existing Tables

Current tables remain:

* customers
* contacts
* commercials
* categories
* contracts
* contract_items
* stations
* users
* scheduled_spots

---

# New Tables

## dayparts

Defines customer-facing dayparts.

Example:

```
Morning Drive
Late Morning
Midday
Afternoon Drive
Evenings
Late Night
Overnight
```

Suggested fields:

```
id
name
description
active
created_date
modified_date
```

---

## traffic_clocks

Defines reusable traffic clocks.

Suggested fields:

```
id
code
name
description
rivendell_clock_code
active
created_date
modified_date
```

Example:

```
Code:
MD1

Name:
Morning Drive Standard
```

---

## traffic_clock_breaks

Defines commercial breaks within a traffic clock.

Suggested fields:

```
id
traffic_clock_id
offset_seconds
duration_seconds
created_date
modified_date
```

Example:

```
15 minutes
180 seconds

30 minutes
180 seconds

45 minutes
180 seconds
```

---

## daypart_schedule

Assigns dayparts and traffic clocks to days.

Suggested fields:

```
id
station_id
day_of_week
start_time
end_time
daypart_id
traffic_clock_id
created_date
modified_date
```

Version 1 assumes repeating weekly schedules.

Future versions may support exceptions.

---

## avails

Generated daily from the daypart schedule.

Suggested fields:

```
id
station_id
air_date
air_time
traffic_clock_break_id
duration_seconds
status
created_date
modified_date
```

Status examples:

```
Open
Filled
Blocked
Cancelled
```

---

## unscheduled_spots

Represents customer demand.

Suggested fields:

```
id
contract_item_id
commercial_id
priority
status
created_date
modified_date
```

Status examples:

```
Open
Scheduled
Cancelled
```

---

# Scheduled Spots

scheduled_spots becomes the final product.

Workflow:

```
Avail
        +
Unscheduled Spot

        |

Scheduled Spot
```

Scheduled spots continue to export to Rivendell.

---

# Python Modules

## Existing

```
traffic/
    customers.py
    contacts.py
    commercials.py
    scheduled_spots.py
    contracts.py
```

---

## Proposed New Modules

```
traffic/
    dayparts.py
    traffic_clocks.py
    traffic_clock_breaks.py
    daypart_schedule.py
    avails.py
    unscheduled_spots.py
    scheduler.py
```

---

# Command Line Utilities

Proposed additions:

```
clock_add.py
clock_edit.py
clock_list.py

break_add.py
break_list.py

daypart_add.py
daypart_list.py

schedule_add.py
schedule_list.py

generate_avails.py

unscheduled_spot_add.py
unscheduled_spot_list.py

schedule_day.py
```

---

# GUI

Eventually the GUI should expose:

```
Customers

Commercials

Contracts

Dayparts

Traffic Clocks

Clock Breaks

Day Schedules

Avails

Scheduled Spots
```

The existing database browser remains useful during development.

---

# Version 1 Simplifying Assumptions

To allow progress:

1. Weekly schedules repeat.
2. No holiday exceptions.
3. No clock version history.
4. No automatic optimisation.
5. Scheduler fills available inventory in a simple deterministic order.
6. Breaks have fixed durations.
7. Commercials may be mixed in any order provided total duration does not exceed break duration.
8. Stations agree to operate within these constraints.

---

# Future Enhancements

Possible Version 2 features:

* Holiday schedules
* Clock version history
* Multiple automation systems
* Music scheduler integration
* Preferred positions
* Separation optimisation
* Revenue optimisation
* Automatic make-goods
* Automatic bonus spots
* Multi-station scheduling
* Sales forecasting
* Inventory reporting

---

# Immediate Development Order

1. dayparts
2. traffic_clocks
3. traffic_clock_breaks
4. daypart_schedule
5. generate_avails
6. unscheduled_spots
7. scheduler
8. Rivendell export updates

This order allows the inventory side of the system to be completed before adding increasingly sophisticated scheduling logic.

