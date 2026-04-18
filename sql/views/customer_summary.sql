CREATE VIEW IF NOT EXISTS customer_order_summary AS
SELECT
    c."Store ID",
    c."Customer ID",
    c."Name",
    SUM(o."Total") AS total_spend,
    COUNT(o."Order ID") AS order_count,
    MIN(o."Placed") AS first_order_date,
    MAX(o."Placed") AS last_order_date
FROM
    customers c
JOIN
    orders o ON c."Customer ID" = o."Customer ID" AND c."Store ID" = o."Store ID"
GROUP BY
    c."Store ID",
    c."Customer ID",
    c."Name";