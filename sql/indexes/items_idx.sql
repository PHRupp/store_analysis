-- Optimization for item-level analysis and order joins
CREATE INDEX IF NOT EXISTS idx_items_store_id ON items ("Store ID");

-- Composite indexes for store-specific item analysis
CREATE INDEX IF NOT EXISTS idx_items_store_customer ON items ("Store ID", "Customer ID");
CREATE INDEX IF NOT EXISTS idx_items_store_order ON items ("Store ID", "Order ID");
CREATE INDEX IF NOT EXISTS idx_items_store_order_placed ON items ("Store ID", "Order ID", "Placed");
CREATE INDEX IF NOT EXISTS idx_items_order_id ON items ("Order ID");
CREATE INDEX IF NOT EXISTS idx_items_customer_id ON items ("Customer ID");