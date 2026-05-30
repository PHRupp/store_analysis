import pandas as pd
import os
import logging
import time
import sqlalchemy as sa
from sqlalchemy import (
    select,
    func,
    case,
    and_,
    desc,
    literal_column,
    text,
    table,
    column,
    cast,
)

# Database configuration
DB_NAME = "business_data.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)

logger = logging.getLogger(__name__)


def build_common_conditions(
    conditions,
    store_name=None,
    store_col=None,
    start_date=None,
    date_col=None,
    end_date=None,
    account_filter="All",
    account_col=None,
):
    """
    Appends store name, date range, and account filter conditions to a given list of conditions.
    """
    if store_name and store_name != "All" and store_col is not None:
        conditions.append(store_col == store_name)
    if start_date and date_col is not None:
        conditions.append(date_col >= start_date)
    if end_date and date_col is not None:
        conditions.append(date_col <= end_date)
    if account_filter and account_filter != "All" and account_col is not None:
        conditions.append(account_col == account_filter)
    return conditions


def execute_query(stmt, is_scalar=False):
    """
    Executes an SQLAlchemy statement, handles logging, and returns the result.
    """
    logger.debug(f"Executing query: {stmt}")
    start_time = time.perf_counter()
    engine = sa.create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as conn:
        if is_scalar:
            result = conn.execute(stmt).scalar()
            end_time = time.perf_counter()
            logger.debug(
                f"Query completed in {end_time - start_time:.4f} seconds. Result: {result}"
            )
            return result
        else:
            df = pd.read_sql_query(stmt, conn)
            end_time = time.perf_counter()
            logger.debug(
                f"Query completed in {end_time - start_time:.4f} seconds. {len(df)} records returned."
            )
            return df


def fetch_store_names():
    """
    Retrieves unique Store Names from the store_lookup view.
    """
    if not os.path.exists(DB_PATH):
        return []
    store_lookup = table("store_lookup", column("Store Name"))
    stmt = select(store_lookup.c["Store Name"]).order_by(store_lookup.c["Store Name"])
    try:
        df = execute_query(stmt)
        return df["Store Name"].tolist()
    except Exception as e:
        logger.error(f"Error fetching store names: {e}")
        return []


def fetch_customer_stats(
    store_name=None, account_filter="All", start_date=None, end_date=None
):
    """
    Retrieves customer segmentation stats from the customer_summary table.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(
            columns=["customer_category", "customer_count", "total_spend"]
        )

    customer_summary = table(
        "customer_summary",
        column("Customer Category"),
        column("Customer ID"),
        column("total_spend"),
        column("Store Name"),
        column("account_type"),
        column("first_order_date"),
    )

    stmt = select(
        customer_summary.c["Customer Category"].label("customer_category"),
        func.count(customer_summary.c["Customer ID"]).label("customer_count"),
        func.sum(customer_summary.c.total_spend).label("total_spend"),
    )

    conditions = build_common_conditions(
        [],
        store_name=store_name,
        store_col=customer_summary.c["Store Name"],
        start_date=start_date,
        date_col=customer_summary.c.first_order_date,
        end_date=end_date,
        account_filter=account_filter,
        account_col=customer_summary.c.account_type,
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.group_by(customer_summary.c["Customer Category"])

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching customer stats: {e}")
        return pd.DataFrame(
            columns=["customer_category", "customer_count", "total_spend"]
        )


def fetch_top_customers(store_name=None, account_filter="All", limit=50):
    """
    Retrieves the top customers by total spending, including their median spend and detailed metadata.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(
            columns=[
                "Name",
                "total_spend",
                "median_spend",
                "customer_category",
                "order_count",
                "discount",
                "recency",
                "median_days_between_orders",
            ]
        )

    customer_summary = table(
        "customer_summary",
        column("Name"),
        column("total_spend"),
        column("median_spend"),
        column("Customer Category"),
        column("order_count"),
        column("Discount"),
        column("days since last order"),
        column("median_days_between_orders"),
        column("Store Name"),
        column("account_type"),
    )

    stmt = select(
        customer_summary.c.Name,
        customer_summary.c.total_spend,
        customer_summary.c.median_spend,
        customer_summary.c["Customer Category"].label("customer_category"),
        customer_summary.c.order_count,
        customer_summary.c.Discount.label("discount"),
        customer_summary.c["days since last order"].label("recency"),
        customer_summary.c.median_days_between_orders,
    )

    conditions = build_common_conditions(
        [],
        store_name=store_name,
        store_col=customer_summary.c["Store Name"],
        account_filter=account_filter,
        account_col=customer_summary.c.account_type,
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(desc(customer_summary.c.total_spend)).limit(limit)

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching top customers: {e}")
        return pd.DataFrame(
            columns=[
                "Name",
                "total_spend",
                "median_spend",
                "customer_category",
                "order_count",
                "discount",
                "recency",
                "median_days_between_orders",
            ]
        )


def fetch_overdue_customers(
    store_name=None, account_filter="All", limit=20, start_date=None, end_date=None
):
    """
    Retrieves customers who are past their expected visit date based on median order intervals.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(
            columns=[
                "Name",
                "days_past_expected",
                "median_spend",
                "order_count",
                "median_days_between_orders",
                "recency",
                "customer_category",
                "total_spend",
            ]
        )

    customer_summary = table(
        "customer_summary",
        column("Name"),
        column("days since last order"),
        column("median_days_between_orders"),
        column("median_spend"),
        column("order_count"),
        column("Customer Category"),
        column("total_spend"),
        column("Store Name"),
        column("account_type"),
        column("first_order_date"),
    )

    days_past_expected = (
        customer_summary.c["days since last order"]
        - customer_summary.c.median_days_between_orders
    ).label("days_past_expected")

    stmt = select(
        customer_summary.c.Name,
        days_past_expected,
        customer_summary.c.median_spend,
        customer_summary.c.order_count,
        customer_summary.c.median_days_between_orders,
        customer_summary.c["days since last order"].label("recency"),
        customer_summary.c["Customer Category"].label("customer_category"),
        customer_summary.c.total_spend,
    )

    conditions = [
        customer_summary.c.median_days_between_orders.isnot(None),
        days_past_expected < 360,
        customer_summary.c.order_count > 10,
    ]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=customer_summary.c["Store Name"],
        start_date=start_date,
        date_col=customer_summary.c.first_order_date,
        end_date=end_date,
        account_filter=account_filter,
        account_col=customer_summary.c.account_type,
    )

    stmt = stmt.where(and_(*conditions)).order_by(desc(days_past_expected)).limit(limit)

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching overdue customers: {e}")
        return pd.DataFrame(
            columns=[
                "Name",
                "days_past_expected",
                "median_spend",
                "order_count",
                "median_days_between_orders",
                "recency",
                "customer_category",
                "total_spend",
            ]
        )


def fetch_new_customers_trend(
    store_name=None, account_filter="All", start_date=None, end_date=None
):
    """
    Retrieves the count of new customers per month based on their first order date.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(
            columns=[
                "month_year",
                "customer_category",
                "new_customer_count",
                "returning_customer_count",
            ]
        )

    customer_summary = table(
        "customer_summary",
        column("first_order_date"),
        column("Customer Category"),
        column("Customer ID"),
        column("order_count"),
        column("Store Name"),
        column("account_type"),
    )

    month_year = func.strftime("%Y-%m", customer_summary.c.first_order_date).label(
        "month_year"
    )
    stmt = select(
        month_year,
        customer_summary.c["Customer Category"].label("customer_category"),
        func.count(customer_summary.c["Customer ID"]).label("new_customer_count"),
        func.sum(case((customer_summary.c.order_count > 1, 1), else_=0)).label(
            "returning_customer_count"
        ),
    )

    conditions = build_common_conditions(
        [],
        store_name=store_name,
        store_col=customer_summary.c["Store Name"],
        start_date=start_date,
        date_col=customer_summary.c.first_order_date,
        end_date=end_date,
        account_filter=account_filter,
        account_col=customer_summary.c.account_type,
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.group_by(month_year, customer_summary.c["Customer Category"]).order_by(
        month_year.asc()
    )

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching new customer trends: {e}")
        return pd.DataFrame(
            columns=[
                "month_year",
                "customer_category",
                "new_customer_count",
                "returning_customer_count",
            ]
        )


def fetch_last_order_trend(
    store_name=None,
    account_filter="All",
    start_date=None,
    end_date=None,
    min_lapsed_days=None,
):
    """
    Retrieves the count of customers based on their last order date per month.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(
            columns=["month_year", "customer_category", "last_order_count"]
        )

    customer_summary = table(
        "customer_summary",
        column("last_order_date"),
        column("Customer Category"),
        column("Customer ID"),
        column("Store Name"),
        column("account_type"),
        column("days since last order"),
    )

    month_year = func.strftime("%Y-%m", customer_summary.c.last_order_date).label(
        "month_year"
    )
    stmt = select(
        month_year,
        customer_summary.c["Customer Category"].label("customer_category"),
        func.count(customer_summary.c["Customer ID"]).label("last_order_count"),
    )

    conditions = build_common_conditions(
        [],
        store_name=store_name,
        store_col=customer_summary.c["Store Name"],
        start_date=start_date,
        date_col=customer_summary.c.last_order_date,
        end_date=end_date,
        account_filter=account_filter,
        account_col=customer_summary.c.account_type,
    )
    if min_lapsed_days is not None:
        conditions.append(customer_summary.c["days since last order"] > min_lapsed_days)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.group_by(month_year, customer_summary.c["Customer Category"]).order_by(
        text("month_year ASC")
    )

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching last order trends: {e}")
        return pd.DataFrame(
            columns=["month_year", "customer_category", "last_order_count"]
        )


def fetch_monthly_revenue(
    store_name=None, start_date=None, end_date=None, account_filter="All"
):
    """
    Connects to the SQLite database and retrieves total revenue aggregated by month.
    Optionally filters by a specific Store ID.
    """
    if not os.path.exists(DB_PATH):
        logger.error(f"Database {DB_NAME} not found. Please run load_db.py first.")
        return pd.DataFrame(columns=["month_year", "total_revenue"])

    orders_t = table(
        "orders",
        column("Placed"),
        column("Total"),
        column("Pieces"),
        column("Customer ID"),
        column("Store ID"),
        column("Store Name"),
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )

    month_year = func.strftime("%Y-%m", orders_t.c.Placed).label("month_year")
    account_type = case(
        (customers_t.c["Business ID"].is_(None), "Retail"),
        (customers_t.c["Business ID"] == "", "Retail"),
        else_="Commercial",
    ).label("account_type")

    stmt = select(
        month_year,
        account_type,
        func.sum(orders_t.c.Total).label("total_revenue"),
        func.sum(orders_t.c.Pieces).label("total_pieces"),
    ).select_from(
        orders_t.join(
            customers_t,
            and_(
                orders_t.c["Customer ID"] == customers_t.c["Customer ID"],
                orders_t.c["Store ID"] == customers_t.c["Store ID"],
            ),
        )
    )

    conditions = [orders_t.c.Placed.isnot(None)]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=orders_t.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=account_type,
    )

    stmt = (
        stmt.where(and_(*conditions))
        .group_by(month_year, account_type)
        .order_by(text("month_year ASC"))
    )

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        return pd.DataFrame(columns=["month_year", "total_revenue"])


def fetch_order_trends(
    store_name=None, start_date=None, end_date=None, account_filter="All"
):
    """
    Retrieves median invoice amount and order count by month.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["month_year", "median_invoice", "order_count"])

    orders_t = table(
        "orders",
        column("Placed"),
        column("Total"),
        column("Customer ID"),
        column("Store ID"),
        column("Store Name"),
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )

    month_year = func.strftime("%Y-%m", orders_t.c.Placed).label("month_year")
    rn = (
        func.row_number()
        .over(
            partition_by=func.strftime("%Y-%m", orders_t.c.Placed),
            order_by=orders_t.c.Total,
        )
        .label("rn")
    )
    cnt = (
        func.count()
        .over(partition_by=func.strftime("%Y-%m", orders_t.c.Placed))
        .label("cnt")
    )

    raw_data = select(month_year, orders_t.c.Total, rn, cnt).select_from(
        orders_t.join(
            customers_t,
            and_(
                orders_t.c["Customer ID"] == customers_t.c["Customer ID"],
                orders_t.c["Store ID"] == customers_t.c["Store ID"],
            ),
        )
    )

    conditions = [orders_t.c.Placed.isnot(None)]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=orders_t.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=case(
            (customers_t.c["Business ID"].is_(None), "Retail"),
            (customers_t.c["Business ID"] == "", "Retail"),
            else_="Commercial",
        ),
    )

    raw_data = raw_data.where(and_(*conditions)).cte("RawData")

    stmt = (
        select(
            raw_data.c.month_year,
            func.avg(raw_data.c.Total).label("median_invoice"),
            func.max(raw_data.c.cnt).label("order_count"),
        )
        .select_from(raw_data)
        .where(raw_data.c.rn.between(raw_data.c.cnt / 2.0, raw_data.c.cnt / 2.0 + 1))
        .group_by(raw_data.c.month_year)
        .order_by(raw_data.c.month_year.asc())
    )

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching order trends: {e}")
        return pd.DataFrame(columns=["month_year", "median_invoice", "order_count"])


def fetch_category_order_trends(
    store_name=None, start_date=None, end_date=None, account_filter="All"
):
    """
    Retrieves the count of orders grouped by month and customer category.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["month_year", "customer_category", "order_count"])

    orders_t = table(
        "orders",
        column("Placed"),
        column("Order ID"),
        column("Customer ID"),
        column("Store ID"),
        column("Store Name"),
    )
    customer_summary = table(
        "customer_summary",
        column("Customer ID"),
        column("Store ID"),
        column("Customer Category"),
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )

    month_year = func.strftime("%Y-%m", orders_t.c.Placed).label("month_year")

    stmt = select(
        month_year,
        customer_summary.c["Customer Category"].label("customer_category"),
        func.count(orders_t.c["Order ID"]).label("order_count"),
    ).select_from(
        orders_t.join(
            customer_summary,
            and_(
                orders_t.c["Customer ID"] == customer_summary.c["Customer ID"],
                orders_t.c["Store ID"] == customer_summary.c["Store ID"],
            ),
        ).join(
            customers_t,
            and_(
                orders_t.c["Customer ID"] == customers_t.c["Customer ID"],
                orders_t.c["Store ID"] == customers_t.c["Store ID"],
            ),
        )
    )

    conditions = [orders_t.c.Placed.isnot(None)]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=orders_t.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=case(
            (customers_t.c["Business ID"].is_(None), "Retail"),
            (customers_t.c["Business ID"] == "", "Retail"),
            else_="Commercial",
        ),
    )

    stmt = (
        stmt.where(and_(*conditions))
        .group_by(month_year, customer_summary.c["Customer Category"])
        .order_by(text("month_year ASC"))
    )

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching category order trends: {e}")
        return pd.DataFrame(columns=["month_year", "customer_category", "order_count"])


def fetch_order_totals(
    store_name=None, start_date=None, end_date=None, account_filter="All"
):
    """
    Retrieves the raw 'Total' for every order matching the filters for histogram analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["Total", "customer_category"])

    orders_t = table(
        "orders",
        column("Total"),
        column("Placed"),
        column("Customer ID"),
        column("Store ID"),
        column("Store Name"),
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )
    customer_summary = table(
        "customer_summary",
        column("Customer ID"),
        column("Store ID"),
        column("Customer Category"),
    )

    stmt = select(
        orders_t.c.Total,
        customer_summary.c["Customer Category"].label("customer_category"),
    ).select_from(
        orders_t.join(
            customers_t,
            and_(
                orders_t.c["Customer ID"] == customers_t.c["Customer ID"],
                orders_t.c["Store ID"] == customers_t.c["Store ID"],
            ),
        ).join(
            customer_summary,
            and_(
                orders_t.c["Customer ID"] == customer_summary.c["Customer ID"],
                orders_t.c["Store ID"] == customer_summary.c["Store ID"],
            ),
        )
    )

    conditions = [orders_t.c.Placed.isnot(None)]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=orders_t.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=case(
            (customers_t.c["Business ID"].is_(None), "Retail"),
            (customers_t.c["Business ID"] == "", "Retail"),
            else_="Commercial",
        ),
    )

    stmt = stmt.where(and_(*conditions))

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching order totals: {e}")
        return pd.DataFrame(columns=["Total", "customer_category"])


def fetch_daytime_data(
    store_name=None,
    start_date=None,
    end_date=None,
    account_filter="All",
    day_of_week="All",
):
    """
    Retrieves the time component of 'Placed' and customer category for daytime analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["placed_hour", "customer_category", "order_count"])

    orders_t = table(
        "orders",
        column("Placed"),
        column("Customer ID"),
        column("Store ID"),
        column("Store Name"),
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )
    customer_summary = table(
        "customer_summary",
        column("Customer ID"),
        column("Store ID"),
        column("Customer Category"),
    )

    placed_hour = func.strftime("%H", orders_t.c.Placed).label("placed_hour")

    stmt = select(
        placed_hour,
        customer_summary.c["Customer Category"].label("customer_category"),
        func.count().label("order_count"),
    ).select_from(
        orders_t.join(
            customers_t,
            and_(
                orders_t.c["Customer ID"] == customers_t.c["Customer ID"],
                orders_t.c["Store ID"] == customers_t.c["Store ID"],
            ),
        ).join(
            customer_summary,
            and_(
                orders_t.c["Customer ID"] == customer_summary.c["Customer ID"],
                orders_t.c["Store ID"] == customer_summary.c["Store ID"],
            ),
        )
    )

    conditions = [
        orders_t.c.Placed.isnot(None),
        cast(func.strftime("%H", orders_t.c.Placed), sa.Integer).between(7, 19),
    ]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=orders_t.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=case(
            (customers_t.c["Business ID"].is_(None), "Retail"),
            (customers_t.c["Business ID"] == "", "Retail"),
            else_="Commercial",
        ),
    )

    if day_of_week and day_of_week != "All":
        conditions.append(func.strftime("%w", orders_t.c.Placed) == str(day_of_week))

    stmt = stmt.where(and_(*conditions)).group_by(
        literal_column("1"), literal_column("2")
    )

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching daytime data: {e}")
        return pd.DataFrame(columns=["placed_hour", "customer_category", "order_count"])


def fetch_collection_data(
    store_name=None,
    start_date=None,
    end_date=None,
    account_filter="All",
    day_of_week="All",
):
    """
    Retrieves the time component of 'Collected' and customer category for daytime analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(
            columns=["collected_hour", "customer_category", "order_count"]
        )

    orders_t = table(
        "orders",
        column("Placed"),
        column("Collected"),
        column("Customer ID"),
        column("Store ID"),
        column("Store Name"),
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )
    customer_summary = table(
        "customer_summary",
        column("Customer ID"),
        column("Store ID"),
        column("Customer Category"),
    )

    collected_hour = func.strftime("%H", orders_t.c.Collected).label("collected_hour")

    stmt = select(
        collected_hour,
        customer_summary.c["Customer Category"].label("customer_category"),
        func.count().label("order_count"),
    ).select_from(
        orders_t.join(
            customers_t,
            and_(
                orders_t.c["Customer ID"] == customers_t.c["Customer ID"],
                orders_t.c["Store ID"] == customers_t.c["Store ID"],
            ),
        ).join(
            customer_summary,
            and_(
                orders_t.c["Customer ID"] == customer_summary.c["Customer ID"],
                orders_t.c["Store ID"] == customer_summary.c["Store ID"],
            ),
        )
    )

    conditions = [
        orders_t.c.Collected.isnot(None),
        cast(func.strftime("%H", orders_t.c.Collected), sa.Integer).between(7, 19),
    ]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=orders_t.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=case(
            (customers_t.c["Business ID"].is_(None), "Retail"),
            (customers_t.c["Business ID"] == "", "Retail"),
            else_="Commercial",
        ),
    )

    if day_of_week and day_of_week != "All":
        conditions.append(func.strftime("%w", orders_t.c.Collected) == str(day_of_week))

    stmt = stmt.where(and_(*conditions)).group_by(
        literal_column("1"), literal_column("2")
    )

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching collection data: {e}")
        return pd.DataFrame(
            columns=["collected_hour", "customer_category", "order_count"]
        )


def fetch_customer_intervals(
    store_name=None, account_filter="All", start_date=None, end_date=None
):
    """
    Retrieves the median interval for each customer for histogram analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(
            columns=["median_days_between_orders", "customer_category", "order_count"]
        )

    customer_summary = table(
        "customer_summary",
        column("median_days_between_orders"),
        column("Customer Category"),
        column("order_count"),
        column("Store Name"),
        column("account_type"),
        column("first_order_date"),
    )

    stmt = select(
        customer_summary.c.median_days_between_orders,
        customer_summary.c["Customer Category"].label("customer_category"),
        customer_summary.c.order_count,
    )

    conditions = [customer_summary.c.median_days_between_orders.isnot(None)]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=customer_summary.c["Store Name"],
        start_date=start_date,
        date_col=customer_summary.c.first_order_date,
        end_date=end_date,
        account_filter=account_filter,
        account_col=customer_summary.c.account_type,
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching customer intervals: {e}")
        return pd.DataFrame(
            columns=["median_days_between_orders", "customer_category", "order_count"]
        )


def fetch_customer_ltv(
    store_name=None, account_filter="All", start_date=None, end_date=None
):
    """
    Retrieves the total spend for each customer for histogram analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["total_spend", "customer_category"])

    customer_summary = table(
        "customer_summary",
        column("total_spend"),
        column("Customer Category"),
        column("Store Name"),
        column("account_type"),
        column("first_order_date"),
    )

    stmt = select(
        customer_summary.c.total_spend,
        customer_summary.c["Customer Category"].label("customer_category"),
    )

    conditions = [customer_summary.c.total_spend.isnot(None)]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=customer_summary.c["Store Name"],
        start_date=start_date,
        date_col=customer_summary.c.first_order_date,
        end_date=end_date,
        account_filter=account_filter,
        account_col=customer_summary.c.account_type,
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching customer ltv: {e}")
        return pd.DataFrame(columns=["total_spend", "customer_category"])


def fetch_unique_items():
    """
    Retrieves unique Item names from the items table that have at least 5 total pieces ordered, sorted alphabetically.
    """
    if not os.path.exists(DB_PATH):
        return []

    items_t = table("items", column("Item"), column("Total Pcs"))

    stmt = (
        select(items_t.c.Item)
        .where(items_t.c.Item.isnot(None))
        .group_by(items_t.c.Item)
        .having(
            func.sum(
                case(
                    (func.lower(items_t.c.Item).like("%rush%"), 1),
                    else_=items_t.c["Total Pcs"],
                )
            )
            >= 10
        )
        .order_by(items_t.c.Item)
    )

    try:
        df = execute_query(stmt)
        return df["Item"].tolist()
    except Exception as e:
        logger.error(f"Error fetching unique items: {e}")
        return []


def fetch_item_pieces_by_week(
    store_name=None,
    start_date=None,
    end_date=None,
    account_filter="All",
    selected_items=None,
):
    """
    Retrieves the total pieces over time, aggregated by week.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["week", "total_pieces", "account_type"])

    items_t = table(
        "items",
        column("Placed"),
        column("Item"),
        column("Total Pcs"),
        column("Order ID"),
        column("Store ID"),
        column("Customer ID"),
    )
    orders_t = table(
        "orders", column("Order ID"), column("Store ID"), column("Store Name")
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )

    placed_date = func.date(items_t.c.Placed).label("placed_date")
    account_type = case(
        (customers_t.c["Business ID"].is_(None), "Retail"),
        (customers_t.c["Business ID"] == "", "Retail"),
        else_="Commercial",
    ).label("account_type")
    total_pieces = func.sum(
        case(
            (func.lower(items_t.c.Item).like("%rush%"), 1), else_=items_t.c["Total Pcs"]
        )
    ).label("total_pieces")

    stmt = select(placed_date, account_type, total_pieces).select_from(
        items_t.join(
            orders_t,
            and_(
                items_t.c["Order ID"] == orders_t.c["Order ID"],
                items_t.c["Store ID"] == orders_t.c["Store ID"],
            ),
        ).join(
            customers_t,
            and_(
                items_t.c["Customer ID"] == customers_t.c["Customer ID"],
                items_t.c["Store ID"] == customers_t.c["Store ID"],
            ),
        )
    )

    conditions = [items_t.c.Placed.isnot(None)]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=items_t.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=account_type,
    )
    if selected_items:
        conditions.append(items_t.c.Item.in_(selected_items))

    stmt = stmt.where(and_(*conditions)).group_by(
        literal_column("placed_date"), literal_column("account_type")
    )

    try:
        df = execute_query(stmt)

        if not df.empty:
            df["placed_date"] = pd.to_datetime(df["placed_date"])
            df = (
                df.groupby(
                    [pd.Grouper(key="placed_date", freq="W-MON"), "account_type"]
                )["total_pieces"]
                .sum()
                .reset_index()
            )
            df.rename(columns={"placed_date": "week"}, inplace=True)
            df["week"] = df["week"].dt.strftime("%Y-%m-%d")
            df.sort_values(["week", "account_type"], inplace=True)

        return df
    except Exception as e:
        logger.error(f"Error fetching item pieces by week: {e}")
        return pd.DataFrame(columns=["week", "total_pieces", "account_type"])


def fetch_total_order_count(
    store_name=None, start_date=None, end_date=None, account_filter="All"
):
    """
    Retrieves the total number of orders matching the filters.
    """
    if not os.path.exists(DB_PATH):
        return 0

    orders_t = table(
        "orders",
        column("Order ID"),
        column("Placed"),
        column("Store Name"),
        column("Customer ID"),
        column("Store ID"),
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )

    stmt = select(
        func.count(func.distinct(orders_t.c["Order ID"])).label("count")
    ).select_from(
        orders_t.join(
            customers_t,
            and_(
                orders_t.c["Customer ID"] == customers_t.c["Customer ID"],
                orders_t.c["Store ID"] == customers_t.c["Store ID"],
            ),
        )
    )

    conditions = [orders_t.c.Placed.isnot(None)]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=orders_t.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=case(
            (customers_t.c["Business ID"].is_(None), "Retail"),
            (customers_t.c["Business ID"] == "", "Retail"),
            else_="Commercial",
        ),
    )

    stmt = stmt.where(and_(*conditions))

    try:
        return execute_query(stmt, is_scalar=True)
    except Exception as e:
        logger.error(f"Error fetching total order count: {e}")
        return 0


def fetch_top_items(
    store_name=None, start_date=None, end_date=None, account_filter="All", limit=20
):
    """
    Retrieves the most frequent items within orders for market basket analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["Item", "order_count"])

    items_t = table(
        "items",
        column("Item"),
        column("Order ID"),
        column("Store ID"),
        column("Customer ID"),
        column("Placed"),
    )
    orders_t = table(
        "orders", column("Order ID"), column("Store ID"), column("Store Name")
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )

    stmt = select(
        items_t.c.Item,
        func.count(func.distinct(items_t.c["Order ID"])).label("order_count"),
    ).select_from(
        items_t.join(
            orders_t,
            and_(
                items_t.c["Order ID"] == orders_t.c["Order ID"],
                items_t.c["Store ID"] == orders_t.c["Store ID"],
            ),
        ).join(
            customers_t,
            and_(
                items_t.c["Customer ID"] == customers_t.c["Customer ID"],
                items_t.c["Store ID"] == customers_t.c["Store ID"],
            ),
        )
    )

    conditions = [items_t.c.Placed.isnot(None), items_t.c.Item.isnot(None)]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=items_t.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=case(
            (customers_t.c["Business ID"].is_(None), "Retail"),
            (customers_t.c["Business ID"] == "", "Retail"),
            else_="Commercial",
        ),
    )

    stmt = (
        stmt.where(and_(*conditions))
        .group_by(items_t.c.Item)
        .order_by(desc("order_count"))
        .limit(limit)
    )

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching top items: {e}")
        return pd.DataFrame(columns=["Item", "order_count"])


def fetch_top_item_pairs(
    store_name=None, start_date=None, end_date=None, account_filter="All", limit=20
):
    """
    Retrieves the most frequent item pairs within orders for market basket analysis.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["item_pair", "pair_count"])

    items_t1 = table(
        "items",
        column("Item"),
        column("Order ID"),
        column("Store ID"),
        column("Customer ID"),
        column("Placed"),
    )
    items_t2 = table("items", column("Item"), column("Order ID"), column("Store ID"))

    orders_t = table(
        "orders", column("Order ID"), column("Store ID"), column("Store Name")
    )
    customers_t = table(
        "customers", column("Customer ID"), column("Store ID"), column("Business ID")
    )

    item_pair = (items_t1.c.Item + " + " + items_t2.c.Item).label("item_pair")

    stmt = select(
        item_pair,
        func.count(func.distinct(items_t1.c["Order ID"])).label("pair_count"),
    ).select_from(
        items_t1.join(
            items_t2,
            and_(
                items_t1.c["Order ID"] == items_t2.c["Order ID"],
                items_t1.c["Store ID"] == items_t2.c["Store ID"],
                items_t1.c.Item < items_t2.c.Item,
            ),
        )
        .join(
            orders_t,
            and_(
                items_t1.c["Order ID"] == orders_t.c["Order ID"],
                items_t1.c["Store ID"] == orders_t.c["Store ID"],
            ),
        )
        .join(
            customers_t,
            and_(
                items_t1.c["Customer ID"] == customers_t.c["Customer ID"],
                items_t1.c["Store ID"] == customers_t.c["Store ID"],
            ),
        )
    )

    conditions = [
        items_t1.c.Placed.isnot(None),
        items_t1.c.Item.isnot(None),
        items_t2.c.Item.isnot(None),
    ]
    conditions = build_common_conditions(
        conditions,
        store_name=store_name,
        store_col=orders_t.c["Store Name"],
        start_date=start_date,
        date_col=items_t1.c.Placed,
        end_date=end_date,
        account_filter=account_filter,
        account_col=case(
            (customers_t.c["Business ID"].is_(None), "Retail"),
            (customers_t.c["Business ID"] == "", "Retail"),
            else_="Commercial",
        ),
    )

    stmt = (
        stmt.where(and_(*conditions))
        .group_by(items_t1.c.Item, items_t2.c.Item)
        .order_by(desc("pair_count"))
        .limit(limit)
    )

    try:
        return execute_query(stmt)
    except Exception as e:
        logger.error(f"Error fetching top item pairs: {e}")
        return pd.DataFrame(columns=["item_pair", "pair_count"])
