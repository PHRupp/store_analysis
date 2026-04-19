import sqlite3
import pandas as pd
import os
import logging

# Database configuration
DB_NAME = "business_data.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)

logger = logging.getLogger(__name__)

def fetch_store_names():
    """
    Retrieves unique Store Names from the store_lookup view.
    """
    if not os.path.exists(DB_PATH):
        return []
    query = 'SELECT "Store Name" FROM store_lookup ORDER BY "Store Name"'
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(query, conn)
            return df["Store Name"].tolist()
    except Exception as e:
        logger.error(f"Error fetching store names: {e}")
        return []

def fetch_customer_stats(store_name=None, account_filter='All'):
    """
    Retrieves customer segmentation stats from the customer_order_summary view.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['customer_category', 'customer_count', 'total_spend'])

    query = 'SELECT "Customer Category" AS customer_category, COUNT("Customer ID") as customer_count, SUM(total_spend) as total_spend FROM customer_order_summary'
    conditions = []
    params = []
    if store_name and store_name != 'All':
        conditions.append('"Store Name" = ?')
        params.append(store_name)
    if account_filter != 'All':
        conditions.append('account_type = ?')
        params.append(account_filter)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' GROUP BY "Customer Category"'
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching customer stats: {e}")
        return pd.DataFrame(columns=['customer_category', 'customer_count', 'total_spend'])

def fetch_top_customers(store_name=None, account_filter='All', limit=50):
    """
    Retrieves the top customers by total spending, including their median spend and detailed metadata.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['Name', 'total_spend', 'median_spend', 'customer_category', 'order_count', 'discount', 'recency', 'median_days_between_orders'])

    query = '''
    SELECT 
        "Name", 
        total_spend, 
        median_spend, 
        "Customer Category" AS customer_category, 
        order_count, 
        "Discount" AS discount, 
        "days since last order" AS recency, 
        median_days_between_orders 
    FROM customer_order_summary
    '''
    conditions = []
    params = []
    if store_name and store_name != 'All':
        conditions.append('"Store Name" = ?')
        params.append(store_name)
    if account_filter != 'All':
        conditions.append('account_type = ?')
        params.append(account_filter)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY total_spend DESC LIMIT ?'
    params.append(limit)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching top customers: {e}")
        return pd.DataFrame(columns=['Name', 'total_spend', 'median_spend', 'customer_category', 'order_count', 'discount', 'recency', 'median_days_between_orders'])

def fetch_monthly_revenue(store_name=None, start_date=None, end_date=None, account_filter='All'):
    """
    Connects to the SQLite database and retrieves total revenue aggregated by month.
    Optionally filters by a specific Store ID.
    """
    if not os.path.exists(DB_PATH):
        logger.error(f"Database {DB_NAME} not found. Please run load_db.py first.")
        return pd.DataFrame(columns=['month_year', 'total_revenue'])
    
    # Base query for monthly aggregation with commercial/retail split
    query = '''
    SELECT 
        strftime("%Y-%m", o."Placed") as month_year, 
        CASE 
            WHEN c."Business ID" IS NULL OR c."Business ID" = '' THEN 'Retail' 
            ELSE 'Commercial' 
        END as account_type,
        SUM(o."Total") as total_revenue 
    FROM orders o
    JOIN customers c ON o."Customer ID" = c."Customer ID" AND o."Store ID" = c."Store ID"
    WHERE o."Placed" IS NOT NULL
    '''
    params = []

    if store_name and store_name != 'All':
        query += ' AND o."Store Name" = ?'
        params.append(store_name)

    if start_date:
        query += ' AND o."Placed" >= ?'
        params.append(start_date)

    if end_date:
        query += ' AND o."Placed" <= ?'
        params.append(end_date)
    
    if account_filter != 'All':
        query += '''AND (CASE WHEN c."Business ID" IS NULL OR c."Business ID" = '' THEN 'Retail' ELSE 'Commercial' END) = ?'''
        params.append(account_filter)

    query += ' GROUP BY month_year, account_type ORDER BY month_year ASC'

    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(query, conn, params=params)
            return df
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        return pd.DataFrame(columns=['month_year', 'total_revenue'])