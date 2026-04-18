import argparse
import sqlite3
import pandas as pd
import sys
import os

def load_csv_to_sqlite(customers_path, orders_path, items_path, db_name="business_data.db"):
    """
    Reads customer and order CSV files and stores them in a local SQLite database.
    """
    # Check if files exist before processing
    if not os.path.exists(customers_path):
        print(f"Error: Customers file not found at {customers_path}")
        sys.exit(1)
    if not os.path.exists(orders_path):
        print(f"Error: Orders file not found at {orders_path}")
        sys.exit(1)
    if not os.path.exists(items_path):
        print(f"Error: Items file not found at {items_path}")
        sys.exit(1)

    try:
        # Establish a connection to the local SQLite database
        with sqlite3.connect(db_name) as conn:
            print(f"Connecting to database: {db_name}")

            # Load Customers
            print(f"Processing customers: {customers_path}...")
            customers_df = pd.read_csv(customers_path)
            customers_df.to_sql("customers", conn, if_exists="replace", index=False)

            # Load Orders
            print(f"Processing orders: {orders_path}...")
            orders_df = pd.read_csv(orders_path)
            orders_df.to_sql("orders", conn, if_exists="replace", index=False)

            # Load Items
            print(f"Processing items: {items_path}...")
            items_df = pd.read_csv(items_path)
            items_df.to_sql("items", conn, if_exists="replace", index=False)

            print("Data successfully loaded into 'customers', 'orders', and 'items' tables.")

    except Exception as e:
        print(f"An error occurred during database operations: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Load Customer and Order CSV data into SQLite.")
    parser.add_argument("--customers", required=True, help="Path to the customers .csv file")
    parser.add_argument("--orders", required=True, help="Path to the orders .csv file")
    parser.add_argument("--items", required=True, help="Path to the items .csv file")

    args = parser.parse_args()

    load_csv_to_sqlite(args.customers, args.orders, args.items)

if __name__ == "__main__":
    main()
