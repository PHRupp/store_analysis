CREATE VIEW IF NOT EXISTS store_lookup AS
SELECT DISTINCT 
    "Store ID", 
    "Store Name"
FROM orders
WHERE "Store ID" IS NOT NULL AND "Store Name" IS NOT NULL;