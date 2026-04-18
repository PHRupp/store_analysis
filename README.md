# Store Analysis Project

This project provides a utility to load store data from CSV files into a local SQLite database for analysis. It specifically handles customer records, order history, and line-item details, including custom logic to filter out non-standard "Upcharge" records from the items dataset.

## Data Dictionary

The following tables are generated in the `business_data.db` SQLite database during the load process.

### Customers Table
Stores unique information for every customer in the system.

| Column Head | Data Type | Description |
| :--- | :--- | :--- |
| customer_id | INTEGER | Unique identifier for the customer (Primary Key). |
| first_name | TEXT | The customer's given name. |
| last_name | TEXT | The customer's family name. |
| email | TEXT | The customer's contact email address. |
| created_at | TEXT | Timestamp when the customer record was created. |

### Orders Table
Contains high-level transaction data for each purchase.

| Column Head | Data Type | Description |
| :--- | :--- | :--- |
| order_id | INTEGER | Unique identifier for the order (Primary Key). |
| customer_id | INTEGER | Reference to the customer who placed the order. |
| order_date | TEXT | The date and time the transaction occurred. |
| total_amount | REAL | The total monetary value of the order. |
| status | TEXT | The fulfillment status (e.g., Completed, Pending, Cancelled). |

### Items Table
Contains individual line items for every order. Note that records flagged as "Upcharges" are excluded during the import process.

| Column Head | Data Type | Description |
| :--- | :--- | :--- |
| item_id | INTEGER | Unique identifier for the line item. |
| order_id | INTEGER | Reference to the order this item belongs to. |
| product_name | TEXT | The name of the product purchased. |
| quantity | INTEGER | The number of units purchased. |
| unit_price | REAL | The price per unit at the time of purchase. |

## Getting Started

### Prerequisites
Ensure you have the dependencies installed:
```bash
pip install pandas
```

### Execution
To clear the old database and reload data from your Downloads folder, run:
```bash
bash run.sh
```