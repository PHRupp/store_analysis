-- Optimization for customer lookups and joins

-- Composite index for store-specific customer lookups and joins
CREATE INDEX IF NOT EXISTS idx_customers_store_customer ON customers ("Store ID", "Customer ID");
CREATE INDEX IF NOT EXISTS idx_customers_store_id ON customers ("Store ID");
CREATE INDEX IF NOT EXISTS idx_customers_customer_id ON customers ("Customer ID");