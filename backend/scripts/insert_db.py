"""Database Insertion Script

Loads cleaned trip data and zone lookup into SQLite database.
Inserts data in 50,000-row chunks to manage memory efficiently.
"""

import pandas as pd
import sys
import os

# Get the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.append(project_root)

from backend.database import get_connection, create_tables

# First create the tables if they don't exist
create_tables()

conn = get_connection()

data_dir = os.path.join(project_root, "backend", "data")

# Load the zone lookup data - this is our dimension table
zones = pd.read_csv(os.path.join(data_dir, "taxi_zone_lookup.csv"))
zones.columns = ["location_id", "borough", "zone_name", "service_zone"]
zones.to_sql("zones", conn, if_exists="replace", index=False)
print(f"Loaded {len(zones)} zones")

# Now load the cleaned trip data - this is our fact table
trips = pd.read_parquet(os.path.join(data_dir, "cleaned_trips.parquet"))

# Select only the columns we need for the database
cols = ["tpep_pickup_datetime", "tpep_dropoff_datetime", "passenger_count", "trip_distance",
        "PULocationID", "DOLocationID", "fare_amount", "tip_amount", "total_amount",
        "payment_type", "trip_duration_minutes", "speed_mph", "fare_per_mile",
        "pickup_hour", "time_of_day", "is_weekend"]

trips = trips[cols]

# Rename columns to match our database schema
trips.columns = ["pickup_datetime", "dropoff_datetime", "passenger_count", "trip_distance",
                 "pu_location_id", "do_location_id", "fare_amount", "tip_amount", "total_amount",
                 "payment_type", "trip_duration_minutes", "speed_mph", "fare_per_mile",
                 "pickup_hour", "time_of_day", "is_weekend"]

# Insert data in chunks to avoid memory issues with large datasets
chunk_size = 50000
for i in range(0, len(trips), chunk_size):
    chunk = trips.iloc[i:i+chunk_size]
    chunk.to_sql("trips", conn, if_exists="append", index=False)
    print(f"Inserted {min(i+chunk_size, len(trips))}/{len(trips)}")

conn.close()
print("Done!")
