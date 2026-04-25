#!/bin/bash

DATA_DIR="G:\My Drive\LBA\MLX Admin\Analysis"
DB_FILE="business_data.db"

# remove the previous data
echo 'deleting old database'
rm -rf $DATA_DIR/$DB_FILE

# Running load_db.py with CSV files from the DATA_DIR
python load_db.py \
    --customers="$DATA_DIR/CC-Customers_2022-12-08-2026-04-25.csv" \
    --orders="$DATA_DIR/CC-Orders-08122022-25042026.csv" \
    --old_pos_orders="$DATA_DIR/HC_OldPOS_Orders_final.csv" \
    --items="$DATA_DIR/CC-Items-Sales_2022-12-08-2026-04-25.csv" \
    --database="$DATA_DIR/$DB_FILE"
