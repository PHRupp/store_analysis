import argparse
import sqlite3
import pandas as pd
import sys
import os

def apply_sql_logic(conn):
    """
    Discovers and executes all SQL scripts in the /sql directory to create database views.
    """
    sql_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql")
    if not os.path.exists(sql_root):
        print(f"Warning: SQL directory not found at {sql_root}. Skipping SQL applications.")
        return

    for root, _, files in os.walk(sql_root):
        for filename in sorted(files):
            if filename.endswith(".sql"):
                print(f"Applying SQL script: {filename}")
                try:
                    with open(os.path.join(root, filename), "r") as f:
                        conn.executescript(f.read())
                except sqlite3.Error as e:
                    print(f"Error applying {filename}: {e}")

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
            # Ensure date-related columns are treated as datetime objects
            for col in ['Signed Up Date', 'Last Order']:
                if col in customers_df.columns:
                    customers_df[col] = pd.to_datetime(customers_df[col], errors='coerce')
            customers_df.to_sql("customers", conn, if_exists="replace", index=False)

            # Load Orders
            print(f"Processing orders: {orders_path}...")
            orders_df = pd.read_csv(orders_path)
            # Ensure date-related columns are treated as datetime objects
            order_date_cols = ['Placed', 'Ready By', 'Cleaned', 'Collected', 'Payment Date', 'Pickup Date', 'Paid By']
            for col in order_date_cols:
                if col in orders_df.columns:
                    orders_df[col] = pd.to_datetime(orders_df[col], errors='coerce')
            orders_df.to_sql("orders", conn, if_exists="replace", index=False)

            # Load Items
            print(f"Processing items: {items_path}...")
            items_df = pd.read_csv(items_path)
            # Ensure date-related columns are treated as datetime objects
            if 'Placed' in items_df.columns:
                items_df['Placed'] = pd.to_datetime(items_df['Placed'], errors='coerce')
            items_df.to_sql("items", conn, if_exists="replace", index=False)

            # Apply SQL views and analytical queries
            apply_sql_logic(conn)

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
