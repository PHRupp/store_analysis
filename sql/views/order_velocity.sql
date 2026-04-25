CREATE VIEW IF NOT EXISTS order_velocity AS
SELECT
    "Store ID",
    "Customer ID",
    "Order ID",
    "Total",
    "Placed",
    "Payment Type",
    "days since last order"
FROM (
    SELECT
        "Store ID",
        "Customer ID",
        "Order ID",
        "Total",
        "Placed",
        "Payment Type",
        (julianday("Placed") - julianday(LAG("Placed") OVER (PARTITION BY "Customer ID", "Store ID" ORDER BY "Placed"))) AS "days since last order"
    FROM
        orders
)
WHERE
    "days since last order" IS NULL 
    OR FLOOR("days since last order") > 0;
