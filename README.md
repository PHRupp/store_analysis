# Store Analysis Project

This project provides a utility to load store data from CSV files into a local SQLite database for analysis. It specifically handles customer records, order history, and line-item details, including custom logic to filter out non-standard "Upcharge" records from the items dataset.

## TODO
- Update procesing for items.csv to remove the upcharge records.

## Data Dictionary

The following tables are generated in the `business_data.db` SQLite database during the load process.

### Customers Table
Stores unique information for every customer in the system.

| Column Head | Data Type | Description |
| :--- | :--- | :--- |
| Store ID | INTEGER | Identifier for the store location. |
| Name | TEXT | Full name of the customer. |
| Email | TEXT | Primary contact email address. |
| Phone | TEXT | Primary contact phone number. |
| Secondary Tel | TEXT | Alternative contact phone number. |
| Address | TEXT | Customer's physical or billing address. |
| Customer ID | INTEGER | Unique system identifier for the customer (Primary Key). |
| Custom ID | TEXT | External or custom customer reference. |
| Discount | REAL | Standard discount percentage or amount for the customer. |
| Credit | REAL | Available store credit balance. |
| Email Opt In | TEXT | Status of marketing email subscription. |
| Promo Signup ID | TEXT | Identifier for the promotion used during signup. |
| Notes | TEXT | General notes visible to staff. |
| Private Notes | TEXT | Internal or restricted customer notes. |
| Business ID | TEXT | Business tax ID or registration number. |
| Stripe Card | TEXT | Token or status for Stripe payment method. |
| EVO Card | TEXT | Token or status for EVO payment method. |
| Clearent Card | TEXT | Token or status for Clearent payment method. |
| CC Pay | TEXT | General credit card payment preference. |
| App Customer | TEXT | Indicator if the customer uses the mobile app. |
| Signed Up Date | TIMESTAMP | Date when the customer registered. |
| Birthday Month | INTEGER | Month of the customer's birthday. |
| Birthday Day | INTEGER | Day of the customer's birthday. |
| Price List ID | INTEGER | Identifier for the assigned pricing tier. |
| Price List | TEXT | Name of the assigned price list. |
| Route # | TEXT | Assigned delivery route number. |
| Last Order | TIMESTAMP | Date of the most recent transaction. |
| Tax 1 Exempt | TEXT | Exemption status for primary tax. |
| Tax 2 Exempt | TEXT | Exemption status for secondary tax. |
| Tax 3 Exempt | TEXT | Exemption status for tertiary tax. |
| Source | TEXT | Acquisition channel for the customer. |
| Total spending | REAL | Lifetime total spending amount. |
| Total sales | REAL | Total value of sales transactions. |
| Total orders | INTEGER | Total count of orders placed. |
| Source store | TEXT | The original store where the customer signed up. |

### Orders Table
Contains high-level transaction data for each purchase.

| Column Head | Data Type | Description |
| :--- | :--- | :--- |
| Store ID | INTEGER | Identifier for the specific store location. |
| Store Name | TEXT | Name of the store where the order was placed. |
| Order ID | INTEGER | Unique identifier for the order (Primary Key). |
| Placed | TIMESTAMP | Timestamp when the order was created. |
| Staff Taking Order | TEXT | Name of the employee who processed the order intake. |
| Ready By | TIMESTAMP | Date/time the order is estimated to be ready. |
| Cleaned | TIMESTAMP | Timestamp when the items were marked as cleaned. |
| Staff Marking Cleaned | TEXT | Staff member who performed the cleaning check. |
| Collected | TIMESTAMP | Timestamp when the order was picked up by the customer. |
| Staff Completing | TEXT | Staff member who finalized the transaction. |
| Customer | TEXT | Full name of the customer. |
| Customer ID | INTEGER | Reference to the unique customer record. |
| Custom ID | TEXT | External or legacy customer reference ID. |
| Email | TEXT | Contact email for the customer. |
| Phone | TEXT | Contact phone number. |
| Address | TEXT | Customer's physical address. |
| Promo Signup ID | TEXT | Identifier for promotional campaigns or signups. |
| Pieces | INTEGER | Total number of individual items in the order. |
| Summary | TEXT | Brief overview of the order contents. |
| Notes | TEXT | General internal or customer notes. |
| Pickup | TEXT | Indicator if pickup service was requested. |
| Pickup Date | TIMESTAMP | Scheduled date for pickup. |
| Staff Pickup | TEXT | Staff assigned to the pickup. |
| Delivery | TEXT | Indicator if delivery service was requested. |
| Bags In | INTEGER | Number of bags received at intake. |
| Bags Out | INTEGER | Number of bags prepared for return. |
| Retail | REAL | Total retail value before discounts. |
| Paid | TEXT | Payment status (e.g., Paid, Unpaid). |
| Payment Type | TEXT | Method of payment used. |
| Card Payment Type | TEXT | Specific card network or processor used. |
| Payment Date | TIMESTAMP | Timestamp of the payment transaction. |
| Staff Taking Payment | TEXT | Staff member who processed the payment. |
| Route # | TEXT | Delivery route assignment. |
| Discount | REAL | Total discount amount applied. |
| Cash Discount | REAL | Specific discount for cash payments. |
| Product Rules Discount | REAL | Discounts triggered by product-specific rules. |
| Credit | REAL | Store credit amount applied to the order. |
| Pre Pay Amount | REAL | Amount paid in advance. |
| Total | REAL | Final amount charged after discounts and credits. |
| Total after Credit Used | REAL | Final balance after applying store credit. |
| Tax | REAL | Primary tax amount. |
| Tax 2 | REAL | Secondary tax amount. |
| Tax 3 | REAL | Tertiary tax amount. |
| Status | TEXT | Current fulfillment status of the order. |
| Locker Location ID | TEXT | Identifier for locker pickup location. |
| Locker Name | TEXT | Name or description of the locker. |
| Section IDs | TEXT | References to storage or processing sections. |
| Rack | TEXT | Storage rack location. |
| Total weight | REAL | Physical weight of the order items. |

### Items Table
Contains individual line items for every order. Note that records flagged as "Upcharges" are excluded during the import process.

| Column Head | Data Type | Description |
| :--- | :--- | :--- |
| Store ID | INTEGER | Identifier for the specific store location. |
| Item ID | INTEGER | Unique identifier for the line item. |
| Section ID | INTEGER | Identifier for the store section or department. |
| Section | TEXT | Name of the section where the item is located. |
| Order ID | INTEGER | Reference to the order this item belongs to. |
| Placed | TIMESTAMP | Timestamp of when the item was added to the order. |
| Express | TEXT | Indicator for express or rush processing. |
| Item | TEXT | Descriptive name of the item or product. |
| Product ID | INTEGER | System-level identifier for the product. |
| Custom Product ID | TEXT | External or custom SKU for the product. |
| Quantity | INTEGER | The number of units purchased. |
| Pieces per Product | INTEGER | Unit multiplier for packaging details. |
| Total Pcs | INTEGER | The total count of pieces (Quantity * Pieces per Product). |
| Item Notes | TEXT | Specific customer or internal notes for the item. |
| Customer ID | INTEGER | Reference to the customer who placed the order. |
| Custom ID | TEXT | Custom reference identifier for the customer. |
| Customer | TEXT | The full name of the customer. |
| Email | TEXT | Customer contact email address. |
| Phone | TEXT | Customer contact phone number. |
| Address | TEXT | Fulfillment or billing address. |
| Paid | TEXT | Status indicating if the item has been paid for. |
| Payment Type | TEXT | Method used for the transaction. |
| Order Status | TEXT | Current lifecycle stage of the parent order. |
| Retail | REAL | Standard retail price of the item. |
| Price Mod | REAL | Adjustments or discounts applied to the price. |
| Cost Price | REAL | The base cost or wholesale price of the item. |
| Price per Item | REAL | The final price charged per unit. |
| Total | REAL | The calculated total value for the line item. |

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