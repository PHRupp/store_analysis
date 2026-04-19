CREATE VIEW IF NOT EXISTS customer_order_summary AS
WITH order_metrics AS (
    SELECT
        "Store ID",
        "Store Name",
        "Customer ID",
        SUM("Total") AS total_spend,
        AVG("Total") AS avg_spend,
        COUNT("Order ID") AS order_count,
        MIN("Placed") AS first_order_date,
        MAX("Placed") AS last_order_date
    FROM orders
    GROUP BY "Store ID", "Store Name", "Customer ID"
),
velocity_metrics AS (
    SELECT
        "Store ID",
        "Customer ID",
        AVG("days since last order") AS mean_days_between_orders
    FROM order_velocity
    GROUP BY "Store ID", "Customer ID"
),
median_calculation AS (
    SELECT 
        "Store ID", 
        "Customer ID", 
        AVG("days since last order") as median_days_between_orders
    FROM (
        SELECT 
            "Store ID", 
            "Customer ID", 
            "days since last order",
            ROW_NUMBER() OVER (PARTITION BY "Store ID", "Customer ID" ORDER BY "days since last order") as rn,
            COUNT(*) OVER (PARTITION BY "Store ID", "Customer ID") as total
        FROM order_velocity
    )
    WHERE rn BETWEEN total / 2.0 AND total / 2.0 + 1
    GROUP BY "Store ID", "Customer ID"
),
median_spend_calculation AS (
    SELECT 
        "Store ID", 
        "Customer ID", 
        AVG("Total") as median_spend
    FROM (
        SELECT 
            "Store ID", 
            "Customer ID", 
            "Total",
            ROW_NUMBER() OVER (PARTITION BY "Store ID", "Customer ID" ORDER BY "Total") as rn,
            COUNT(*) OVER (PARTITION BY "Store ID", "Customer ID") as total_cnt
        FROM orders
    )
    WHERE rn BETWEEN total_cnt / 2.0 AND total_cnt / 2.0 + 1
    GROUP BY "Store ID", "Customer ID"
)
SELECT
    c."Store ID",
    om."Store Name",
    c."Customer ID",
    c."Name",
    c."Discount",
    om.total_spend,
    om.avg_spend,
    ms.median_spend,
    om.order_count,
    CASE 
        WHEN c."Business ID" IS NULL OR c."Business ID" = '' THEN 'Retail' 
        ELSE 'Commercial' 
    END as account_type,
    CASE 
        WHEN om.order_count <= 1 THEN '1) One Time'
        WHEN om.order_count = 2 THEN '2) Second'
        WHEN om.order_count = 3 THEN '3) Third'
        WHEN om.order_count <= 10 THEN '4) Comfortable'
        WHEN om.order_count <= 20 THEN '5) Regular'
        WHEN om.order_count <= 50 THEN '6) Super Regular'
        ELSE '7) Big Dawgs'
    END AS "Customer Category",
    om.first_order_date,
    om.last_order_date,
    (julianday('now') - julianday(om.last_order_date)) AS "days since last order",
    vm.mean_days_between_orders,
    mm.median_days_between_orders
FROM
    customers c
JOIN order_metrics om ON c."Customer ID" = om."Customer ID" AND c."Store ID" = om."Store ID"
LEFT JOIN velocity_metrics vm ON c."Customer ID" = vm."Customer ID" AND c."Store ID" = vm."Store ID"
LEFT JOIN median_calculation mm ON c."Customer ID" = mm."Customer ID" AND c."Store ID" = mm."Store ID"
LEFT JOIN median_spend_calculation ms ON c."Customer ID" = ms."Customer ID" AND c."Store ID" = ms."Store ID";