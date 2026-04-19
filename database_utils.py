import sqlite3
import pandas as pd
import os

# Database configuration
DB_NAME = "business_data.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)

def fetch_store_ids():
    """
    Retrieves unique Store IDs from the orders table to populate the dropdown.
    """
    if not os.path.exists(DB_PATH):
        return []
    query = 'SELECT DISTINCT "Store ID" FROM orders WHERE "Store ID" IS NOT NULL ORDER BY "Store ID"'
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(query, conn)
            return df["Store ID"].tolist()
    except Exception as e:
        print(f"Error fetching store IDs: {e}")
        return []

def fetch_customer_stats(store_id=None):
    """
    Retrieves customer segmentation stats from the customer_order_summary view.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['customer_category', 'customer_count', 'aggregate_spend'])

    query = 'SELECT "Customer Category" AS customer_category, COUNT("Customer ID") as customer_count, SUM(total_spend) as aggregate_spend FROM customer_order_summary'
    params = []
    if store_id and store_id != 'All':
        query += ' WHERE "Store ID" = ?'
        params.append(store_id)
    query += ' GROUP BY "Customer Category"'
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"Error fetching customer stats: {e}")
        return pd.DataFrame(columns=['customer_category', 'customer_count', 'aggregate_spend'])

def fetch_monthly_revenue(store_id=None, start_date=None, end_date=None):
    """
    Connects to the SQLite database and retrieves total revenue aggregated by month.
    Optionally filters by a specific Store ID.
    """
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_NAME} not found. Please run load_db.py first.")
        return pd.DataFrame(columns=['month_year', 'total_revenue'])
    
    # Base query for monthly aggregation with commercial/retail split
    query = '''
    SELECT 
        strftime("%Y-%m", o."Placed") as month_year, 
        CASE 
            WHEN c."Business ID" IS NOT NULL AND c."Business ID" != "" THEN 'Commercial' 
            ELSE 'Retail' 
        END as account_type,
        SUM(o."Total") as total_revenue 
    FROM orders o
    JOIN customers c ON o."Customer ID" = c."Customer ID" AND o."Store ID" = c."Store ID"
    WHERE o."Placed" IS NOT NULL
    '''
    params = []

    if store_id and store_id != 'All':
        query += ' AND o."Store ID" = ?'
        params.append(store_id)

    if start_date:
        query += ' AND o."Placed" >= ?'
        params.append(start_date)

    if end_date:
        query += ' AND o."Placed" <= ?'
        params.append(end_date)
    
    query += ' GROUP BY month_year, account_type ORDER BY month_year ASC'

    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(query, conn, params=params)
            return df
    except Exception as e:
        print(f"Error querying database: {e}")
        return pd.DataFrame(columns=['month_year', 'total_revenue'])