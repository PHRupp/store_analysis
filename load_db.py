import argparse
import sqlite3
import pandas as pd
import sys
import os
import logging

# Configure logging to screen and file
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "store_analysis.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def apply_sql_logic(conn):
    """
    Discovers and executes all SQL scripts in the /sql directory to create database views.
    """
    sql_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql")
    if not os.path.exists(sql_root):
        logger.warning(f"SQL directory not found at {sql_root}. Skipping SQL applications.")
        return

    for root, _, files in os.walk(sql_root):
        for filename in sorted(files):
            if filename.endswith(".sql"):
                logger.info(f"Applying SQL script: {filename}")
                try:
                    with open(os.path.join(root, filename), "r") as f:
                        conn.executescript(f.read())
                except sqlite3.Error as e:
                    logger.error(f"Error applying {filename}: {e}")

def load_csv_to_sqlite(customers_path, orders_path, items_path, old_pos_orders_path=None, db_name="business_data.db"):
    """
    Reads customer and order CSV files and stores them in a local SQLite database.
    """
    # Check if files exist before processing
    if not os.path.exists(customers_path):
        logger.error(f"Customers file not found at {customers_path}")
        sys.exit(1)
    if not os.path.exists(orders_path):
        logger.error(f"Orders file not found at {orders_path}")
        sys.exit(1)
    if not os.path.exists(items_path):
        logger.error(f"Items file not found at {items_path}")
        sys.exit(1)

    try:
        # Establish a connection to the local SQLite database
        with sqlite3.connect(db_name) as conn:
            logger.info(f"Connecting to database: {db_name}")

            # Load Customers
            logger.info(f"Processing customers: {customers_path}...")
            customers_df = pd.read_csv(customers_path)
            # Ensure date-related columns are treated as datetime objects
            for col in ['Signed Up Date', 'Last Order']:
                if col in customers_df.columns:
                    customers_df[col] = pd.to_datetime(customers_df[col], errors='coerce')
            customers_df.to_sql("customers", conn, if_exists="replace", index=False)

            # Load Orders
            logger.info(f"Processing orders: {orders_path}...")
            orders_df = pd.read_csv(orders_path)
            # Ensure date-related columns are treated as datetime objects
            order_date_cols = ['Placed', 'Ready By', 'Cleaned', 'Collected', 'Payment Date', 'Pickup Date', 'Paid By']
            for col in order_date_cols:
                if col in orders_df.columns:
                    orders_df[col] = pd.to_datetime(orders_df[col], errors='coerce')
            orders_df.to_sql("orders", conn, if_exists="replace", index=False)

            # Load Old POS Orders if provided
            if old_pos_orders_path:
                if os.path.exists(old_pos_orders_path):
                    logger.info(f"Appending old POS orders: {old_pos_orders_path}...")
                    old_orders_df = pd.read_csv(old_pos_orders_path)
                    for col in order_date_cols:
                        if col in old_orders_df.columns:
                            old_orders_df[col] = pd.to_datetime(old_orders_df[col], errors='coerce')
                    old_orders_df.to_sql("orders", conn, if_exists="append", index=False)
                else:
                    logger.warning(f"Old POS orders file not found at {old_pos_orders_path}. Skipping append.")

            # Load Items
            logger.info(f"Processing items: {items_path}...")
            items_df = pd.read_csv(items_path)
            # Ensure date-related columns are treated as datetime objects
            if 'Placed' in items_df.columns:
                items_df['Placed'] = pd.to_datetime(items_df['Placed'], errors='coerce')
            items_df.to_sql("items", conn, if_exists="replace", index=False)

            # Apply SQL views and analytical queries
            apply_sql_logic(conn)

            logger.info("Data successfully loaded into 'customers', 'orders', and 'items' tables.")

    except Exception as e:
        logger.error(f"An error occurred during database operations: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Load Customer and Order CSV data into SQLite.")
    parser.add_argument("--customers", required=True, help="Path to the customers .csv file")
    parser.add_argument("--orders", required=True, help="Path to the orders .csv file")
    parser.add_argument("--items", required=True, help="Path to the items .csv file")
    parser.add_argument("--old_pos_orders", help="Optional path to old POS orders .csv file to append")
    parser.add_argument("--database", default="business_data.db", help="Path to the SQLite database file")

    args = parser.parse_args()

    load_csv_to_sqlite(args.customers, args.orders, args.items, args.old_pos_orders, args.database)

if __name__ == "__main__":
    main()
