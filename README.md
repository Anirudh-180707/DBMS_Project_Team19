# Disaster Relief Resource Management System

A database case study that demonstrates the design and implementation of a disaster relief resource management system using **Firebird RDBMS**, with a Python desktop application for database interaction and FlameRobin for database administration.

The system manages disaster records, relief requests, organizations, resources, warehouses, inventory, and deliveries using relational database concepts and SQL.

## Team Members

| S. No. | Name | Roll Number |
|:---:|---|---|
| 1 | Anirudh L | CB.SC.U4CSE25706 |
| 2 | P Dheva Dharshan | CB.SC.U4CSE25737 |
| 3 | Rithikeswaran M | CB.SC.U4CSE25746 |

## Project Objectives

- Design a relational database for managing disaster relief resources.
- Maintain relationships between disasters, relief requests, organizations, and resources.
- Track warehouse inventory and resource deliveries.
- Implement database operations using SQL.
- Demonstrate primary keys, foreign keys, constraints, and referential integrity.
- Implement views, stored procedures, and triggers in Firebird.
- Develop a Python desktop application to interact with the database.
- Use FlameRobin to inspect and administer the database.

## Technology Stack

| Technology | Purpose |
|---|---|
| Firebird RDBMS | Relational database management and data storage |
| FlameRobin | Database administration and inspection |
| Python | Desktop application and database interaction |
| SQL | Queries, table definitions, and data manipulation |
| PSQL | Stored procedures and triggers |

## Database Schema

The database consists of eight related tables.

| Table | Purpose |
|---|---|
| `DISASTER` | Stores disaster-related records |
| `RELIEF_REQUEST` | Stores requests for relief resources |
| `ORGANIZATION` | Stores information about organizations involved in relief operations |
| `RESOURCE` | Stores information about available resource types |
| `WAREHOUSE` | Stores warehouse information |
| `INVENTORY` | Tracks resources available in warehouses |
| `DELIVERY` | Stores delivery records associated with relief requests |
| `DELIVERY_ITEM` | Records the inventory items associated with deliveries |

### Relationships

- One disaster can have multiple relief requests.
- Relief requests are associated with disasters, organizations, and resources.
- Deliveries are associated with relief requests.
- Delivery items are associated with deliveries and inventory records.
- Inventory records connect resources with warehouses.

Primary keys uniquely identify records, while foreign keys maintain relationships and enforce referential integrity between tables.

## Key Database Features

### 1. CRUD Operations

The application demonstrates the four fundamental database operations:

- **Create:** Insert new records.
- **Read:** Retrieve records using SQL queries.
- **Update:** Modify existing records.
- **Delete:** Remove records while respecting database constraints.

### 2. SQL Joins

Joins combine related information from multiple tables.

For example, the database can retrieve disasters together with their associated relief requests using a join between `DISASTER` and `RELIEF_REQUEST`.

### 3. Views

The database includes three views for retrieving commonly needed information:

- `V_PENDING_REQUESTS`
- `V_INVENTORY_SUMMARY`
- `V_DELIVERY_SUMMARY`

These views provide reusable queries for examining pending requests, inventory summaries, and delivery information.

### 4. Stored Procedure

**`UPDATE_REQUEST_STATUS`**

A stored procedure that changes the status of a relief request. It keeps the status-update logic within the database.

### 5. Trigger

**`BI_DELIVERY_ITEM_STOCK`**

A trigger that executes automatically when a delivery item is inserted. It updates the corresponding inventory stock, helping maintain consistency between deliveries and available resources.

### 6. Database Constraints

The database uses relational constraints, including:

- Primary keys
- Foreign keys
- Unique constraints
- NOT NULL constraints
- CHECK constraints

These constraints help maintain data integrity and prevent invalid records and relationships.

## Application Architecture

The project separates database administration from application interaction.

```text
                  User
                   |
                   v
          Python Desktop App
                   |
                   v
             Firebird RDBMS
                   |
                   v
       Disaster Relief Database
             (8 Tables)

          FlameRobin
               |
               v
          Firebird RDBMS
