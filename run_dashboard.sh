#!/bin/bash

DATA_DIR="G:\My Drive\LBA\MLX Admin\Analysis"
DB_FILE="business_data.db"

# Running load_db.py with CSV files from the DATA_DIR
python dashboard.py \
    --database="$DATA_DIR/$DB_FILE"
