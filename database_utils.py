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

def fetch_overdue_customers(store_name=None, account_filter='All', limit=20):
    """
    Retrieves customers who are past their expected visit date based on median order intervals.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['Name', 'days_past_expected', 'median_spend', 'order_count', 'median_days_between_orders', 'recency', 'customer_category', 'total_spend'])

    query = '''
    SELECT 
        "Name", 
        ("days since last order" - median_days_between_orders) AS days_past_expected,
        median_spend,
        order_count,
        median_days_between_orders,
        "days since last order" AS recency,
        "Customer Category" AS customer_category,
        total_spend
    FROM customer_order_summary
    '''
    conditions = [
        'median_days_between_orders IS NOT NULL',
        '("days since last order" - median_days_between_orders) < 360',
        'order_count > 10'
    ]
    params = []
    if store_name and store_name != 'All':
        conditions.append('"Store Name" = ?')
        params.append(store_name)
    if account_filter != 'All':
        conditions.append('account_type = ?')
        params.append(account_filter)

    query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY days_past_expected DESC LIMIT ?'
    params.append(limit)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching overdue customers: {e}")
        return pd.DataFrame(columns=['Name', 'days_past_expected', 'median_spend', 'order_count', 'median_days_between_orders', 'recency', 'customer_category', 'total_spend'])

def fetch_new_customers_trend(store_name=None, account_filter='All', start_date=None, end_date=None):
    """
    Retrieves the count of new customers per month based on their first order date.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['month_year', 'customer_category', 'new_customer_count'])

    query = 'SELECT strftime("%Y-%m", first_order_date) AS month_year, "Customer Category" AS customer_category, COUNT("Customer ID") AS new_customer_count FROM customer_order_summary'
    conditions = []
    params = []
    if store_name and store_name != 'All':
        conditions.append('"Store Name" = ?')
        params.append(store_name)
    if account_filter != 'All':
        conditions.append('account_type = ?')
        params.append(account_filter)
    if start_date:
        conditions.append('first_order_date >= ?')
        params.append(start_date)
    if end_date:
        conditions.append('first_order_date <= ?')
        params.append(end_date)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' GROUP BY month_year, customer_category ORDER BY month_year ASC'

    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching new customer trends: {e}")
        return pd.DataFrame(columns=['month_year', 'customer_category', 'new_customer_count'])

def fetch_last_order_trend(store_name=None, account_filter='All', start_date=None, end_date=None):
    """
    Retrieves the count of customers based on their last order date per month.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['month_year', 'customer_category', 'last_order_count'])

    query = 'SELECT strftime("%Y-%m", last_order_date) AS month_year, "Customer Category" AS customer_category, COUNT("Customer ID") AS last_order_count FROM customer_order_summary'
    conditions = []
    params = []
    if store_name and store_name != 'All':
        conditions.append('"Store Name" = ?')
        params.append(store_name)
    if account_filter != 'All':
        conditions.append('account_type = ?')
        params.append(account_filter)
    if start_date:
        conditions.append('last_order_date >= ?')
        params.append(start_date)
    if end_date:
        conditions.append('last_order_date <= ?')
        params.append(end_date)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' GROUP BY month_year, customer_category ORDER BY month_year ASC'

    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching last order trends: {e}")
        return pd.DataFrame(columns=['month_year', 'customer_category', 'last_order_count'])

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
        SUM(o."Total") as total_revenue,
        SUM(o."Pieces") as total_pieces
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

def fetch_order_trends(store_name=None, start_date=None, end_date=None, account_filter='All'):
    """
    Retrieves median invoice amount and order count by month.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['month_year', 'median_invoice', 'order_count'])
    
    conditions = ['o."Placed" IS NOT NULL']
    params = []
    
    if store_name and store_name != 'All':
        conditions.append('o."Store Name" = ?')
        params.append(store_name)
    if start_date:
        conditions.append('o."Placed" >= ?')
        params.append(start_date)
    if end_date:
        conditions.append('o."Placed" <= ?')
        params.append(end_date)
    if account_filter != 'All':
        conditions.append("(CASE WHEN c.\"Business ID\" IS NULL OR c.\"Business ID\" = '' THEN 'Retail' ELSE 'Commercial' END) = ?")
        params.append(account_filter)

    where_clause = " WHERE " + " AND ".join(conditions)
    
    query = f'''
    WITH RawData AS (
        SELECT 
            strftime("%Y-%m", o."Placed") as month_year, 
            o."Total",
            ROW_NUMBER() OVER (PARTITION BY strftime("%Y-%m", o."Placed") ORDER BY o."Total") as rn,
            COUNT(*) OVER (PARTITION BY strftime("%Y-%m", o."Placed")) as cnt
        FROM orders o
        JOIN customers c ON o."Customer ID" = c."Customer ID" AND o."Store ID" = c."Store ID"
        {where_clause}
    )
    SELECT 
        month_year, 
        AVG("Total") as median_invoice,
        MAX(cnt) as order_count
    FROM RawData
    WHERE rn BETWEEN cnt / 2.0 AND cnt / 2.0 + 1
    GROUP BY month_year
    ORDER BY month_year ASC
    '''
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching order trends: {e}")
        return pd.DataFrame(columns=['month_year', 'median_invoice', 'order_count'])

def fetch_category_order_trends(store_name=None, start_date=None, end_date=None, account_filter='All'):
    """
    Retrieves the count of orders grouped by month and customer category.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['month_year', 'customer_category', 'order_count'])

    conditions = ['o."Placed" IS NOT NULL']
    params = []
    
    if store_name and store_name != 'All':
        conditions.append('o."Store Name" = ?')
        params.append(store_name)
    if start_date:
        conditions.append('o."Placed" >= ?')
        params.append(start_date)
    if end_date:
        conditions.append('o."Placed" <= ?')
        params.append(end_date)
    if account_filter != 'All':
        conditions.append("(CASE WHEN c.\"Business ID\" IS NULL OR c.\"Business ID\" = '' THEN 'Retail' ELSE 'Commercial' END) = ?")
        params.append(account_filter)

    where_clause = " WHERE " + " AND ".join(conditions)

    query = f'''
    SELECT 
        strftime("%Y-%m", o."Placed") as month_year, 
        cs."Customer Category" as customer_category,
        COUNT(o."Order ID") as order_count
    FROM orders o
    JOIN customer_order_summary cs ON o."Customer ID" = cs."Customer ID" AND o."Store ID" = cs."Store ID"
    JOIN customers c ON o."Customer ID" = c."Customer ID" AND o."Store ID" = c."Store ID"
    {where_clause}
    GROUP BY month_year, customer_category
    ORDER BY month_year ASC
    '''
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching category order trends: {e}")
        return pd.DataFrame(columns=['month_year', 'customer_category', 'order_count'])

def fetch_order_totals(store_name=None, start_date=None, end_date=None, account_filter='All'):
    """
    Retrieves the raw 'Total' for every order matching the filters for histogram analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['Total', 'customer_category'])
    
    conditions = ['o."Placed" IS NOT NULL']
    params = []
    
    if store_name and store_name != 'All':
        conditions.append('o."Store Name" = ?')
        params.append(store_name)
    if start_date:
        conditions.append('o."Placed" >= ?')
        params.append(start_date)
    if end_date:
        conditions.append('o."Placed" <= ?')
        params.append(end_date)
    if account_filter != 'All':
        conditions.append("(CASE WHEN c.\"Business ID\" IS NULL OR c.\"Business ID\" = '' THEN 'Retail' ELSE 'Commercial' END) = ?")
        params.append(account_filter)

    where_clause = " WHERE " + " AND ".join(conditions)
    
    query = f'''
    SELECT 
        o."Total",
        cs."Customer Category" as customer_category
    FROM orders o
    JOIN customers c ON o."Customer ID" = c."Customer ID" AND o."Store ID" = c."Store ID"
    JOIN customer_order_summary cs ON o."Customer ID" = cs."Customer ID" AND o."Store ID" = cs."Store ID"
    {where_clause}
    '''
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching order totals: {e}")
        return pd.DataFrame(columns=['Total', 'customer_category'])

def fetch_daytime_data(store_name=None, start_date=None, end_date=None, account_filter='All', day_of_week='All'):
    """
    Retrieves the time component of 'Placed' and customer category for daytime analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['placed_hour', 'customer_category'])
    
    conditions = [
        'o."Placed" IS NOT NULL',
        'CAST(strftime("%H", o."Placed") AS INTEGER) BETWEEN 7 AND 19'
    ]
    params = []
    
    if store_name and store_name != 'All':
        conditions.append('o."Store Name" = ?')
        params.append(store_name)
    if start_date:
        conditions.append('o."Placed" >= ?')
        params.append(start_date)
    if end_date:
        conditions.append('o."Placed" <= ?')
        params.append(end_date)
    if account_filter != 'All':
        conditions.append("(CASE WHEN c.\"Business ID\" IS NULL OR c.\"Business ID\" = '' THEN 'Retail' ELSE 'Commercial' END) = ?")
        params.append(account_filter)

    if day_of_week and day_of_week != 'All':
        conditions.append("strftime('%w', o.\"Placed\") = ?")
        params.append(str(day_of_week))

    where_clause = " WHERE " + " AND ".join(conditions)
    
    query = f'''
    SELECT 
        strftime('%H', o."Placed") as placed_hour,
        cs."Customer Category" as customer_category
    FROM orders o
    JOIN customers c ON o."Customer ID" = c."Customer ID" AND o."Store ID" = c."Store ID"
    JOIN customer_order_summary cs ON o."Customer ID" = cs."Customer ID" AND o."Store ID" = cs."Store ID"
    {where_clause}
    '''
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching daytime data: {e}")
        return pd.DataFrame(columns=['placed_hour', 'customer_category'])

def fetch_collection_data(store_name=None, start_date=None, end_date=None, account_filter='All', day_of_week='All'):
    """
    Retrieves the time component of 'Collected' and customer category for daytime analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['collected_hour', 'customer_category'])
    
    conditions = [
        'o."Collected" IS NOT NULL',
        'CAST(strftime("%H", o."Collected") AS INTEGER) BETWEEN 7 AND 19'
    ]
    params = []
    
    if store_name and store_name != 'All':
        conditions.append('o."Store Name" = ?')
        params.append(store_name)
    if start_date:
        conditions.append('o."Placed" >= ?')
        params.append(start_date)
    if end_date:
        conditions.append('o."Placed" <= ?')
        params.append(end_date)
    if account_filter != 'All':
        conditions.append("(CASE WHEN c.\"Business ID\" IS NULL OR c.\"Business ID\" = '' THEN 'Retail' ELSE 'Commercial' END) = ?")
        params.append(account_filter)

    if day_of_week and day_of_week != 'All':
        conditions.append("strftime('%w', o.\"Collected\") = ?")
        params.append(str(day_of_week))

    where_clause = " WHERE " + " AND ".join(conditions)
    
    query = f'''
    SELECT 
        strftime('%H', o."Collected") as collected_hour,
        cs."Customer Category" as customer_category
    FROM orders o
    JOIN customers c ON o."Customer ID" = c."Customer ID" AND o."Store ID" = c."Store ID"
    JOIN customer_order_summary cs ON o."Customer ID" = cs."Customer ID" AND o."Store ID" = cs."Store ID"
    {where_clause}
    '''
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        logger.error(f"Error fetching collection data: {e}")
        return pd.DataFrame(columns=['collected_hour', 'customer_category'])