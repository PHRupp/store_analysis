#!/bin/bash

# remove the previous data
echo 'deleting old database'
rm -rf business_data.db

# Running main.py with customers and orders CSV files from the Downloads folder
python load_db.py --customers="$HOME/Downloads/customers.csv" --orders="$HOME/Downloads/orders.csv" --items="$HOME/Downloads/items.csv"
