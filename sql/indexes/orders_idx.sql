-- Optimization for order history and velocity calculations
CREATE INDEX IF NOT EXISTS idx_orders_store_id ON orders ("Store ID");

-- Composite indexes for store-specific order and customer filtering
CREATE INDEX IF NOT EXISTS idx_orders_store_customer ON orders ("Store ID", "Customer ID");
CREATE INDEX IF NOT EXISTS idx_orders_store_order ON orders ("Store ID", "Order ID");
CREATE INDEX IF NOT EXISTS idx_orders_store_order_placed ON orders ("Store ID", "Order ID", "Placed");
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders ("Customer ID");
CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders ("Order ID");