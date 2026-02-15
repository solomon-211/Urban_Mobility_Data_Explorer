"""Data Cleaning Script for NYC Taxi Trip Data

This script performs 7-step data cleaning pipeline:
1. Remove duplicates
2. Drop missing critical fields
3. Remove impossible timestamps
4. Remove outliers
5. Validate location IDs
6. Remove unrealistic durations
7. Remove impossible speeds

Also engineers 5 derived features and generates transparency log.
"""

import pandas as pd
import os

# Get absolute paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
data_dir = os.path.join(project_root, "backend", "data")

# Load raw data - support both parquet and CSV
parquet_path = os.path.join(data_dir, "yellow_tripdata.parquet")
csv_path = os.path.join(data_dir, "yellow_tripdata.csv")

if os.path.exists(parquet_path):
    trips = pd.read_parquet(parquet_path)
elif os.path.exists(csv_path):
    trips = pd.read_csv(csv_path)
else:
    raise FileNotFoundError("Could not find yellow_tripdata.parquet or yellow_tripdata.csv")

zones = pd.read_csv(os.path.join(data_dir, "taxi_zone_lookup.csv"))

print(f"Raw trips loaded: {len(trips)}")

log = []  # Track all cleaning operations for transparency

# STEP 1: Drop duplicates
before = len(trips)
trips = trips.drop_duplicates()
log.append(f"Duplicates removed: {before - len(trips)}")

# STEP 2: Drop missing critical fields
# These fields are required for every calculation
before = len(trips)
trips = trips.dropna(subset=[
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "fare_amount",
    "trip_distance"
])
log.append(f"Rows dropped (missing critical fields): {before - len(trips)}")

# Fix timestamps - convert to datetime objects
trips["tpep_pickup_datetime"] = pd.to_datetime(trips["tpep_pickup_datetime"])
trips["tpep_dropoff_datetime"] = pd.to_datetime(trips["tpep_dropoff_datetime"])

# STEP 3: Remove impossible timestamps
# Dropoff must occur after pickup
before = len(trips)
trips = trips[trips["tpep_dropoff_datetime"] > trips["tpep_pickup_datetime"]]
log.append(f"Rows dropped (dropoff before pickup): {before - len(trips)}")

# STEP 4: Remove outliers
# Distance >100mi, fare >$500, passengers >6 are likely errors
before = len(trips)
trips = trips[
    (trips["trip_distance"] > 0) &
    (trips["trip_distance"] < 100) &
    (trips["fare_amount"] > 0) &
    (trips["fare_amount"] < 500) &
    (trips["passenger_count"] > 0) &
    (trips["passenger_count"] <= 6)
]
log.append(f"Rows dropped (outliers): {before - len(trips)}")

# STEP 5: Remove location IDs not in zone lookup
# Ensures referential integrity with zones table
valid_ids = set(zones["LocationID"].tolist())
before = len(trips)
trips = trips[
    trips["PULocationID"].isin(valid_ids) &
    trips["DOLocationID"].isin(valid_ids)
]
log.append(f"Rows dropped (invalid location IDs): {before - len(trips)}")

# FEATURE ENGINEERING

# FEATURE 1: Trip duration in minutes
# Justification: Reveals congestion patterns and rush hour delays
trips["trip_duration_minutes"] = (
    trips["tpep_dropoff_datetime"] - trips["tpep_pickup_datetime"]
).dt.total_seconds() / 60

# STEP 6: Remove trips with unrealistic duration
# <1 min likely system errors, >3 hours likely data entry errors
before = len(trips)
trips = trips[
    (trips["trip_duration_minutes"] > 1) &
    (trips["trip_duration_minutes"] < 180)
]
log.append(f"Rows dropped (bad duration): {before - len(trips)}")

# FEATURE 2: Speed in mph
# Justification: Shows traffic behavior by time of day and location
trips["speed_mph"] = (
    trips["trip_distance"] / (trips["trip_duration_minutes"] / 60)
)

# STEP 7: Remove physically impossible speeds
# >80 mph impossible in NYC traffic, indicates data errors
before = len(trips)
trips = trips[trips["speed_mph"] < 80]
log.append(f"Rows dropped (speed over 80mph): {before - len(trips)}")

# FEATURE 3: Fare per mile
# Justification: Reveals economic patterns and pricing efficiency by zone
trips["fare_per_mile"] = trips["fare_amount"] / trips["trip_distance"]

# FEATURE 4: Time of day bucket
# Justification: Categorizes trips for rush hour and demand pattern analysis
def time_of_day(hour):
    """Categorize hour into time period"""
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"

trips["pickup_hour"] = trips["tpep_pickup_datetime"].dt.hour
trips["time_of_day"] = trips["pickup_hour"].apply(time_of_day)

# FEATURE 5: Is weekend
# Justification: Weekend vs weekday patterns differ significantly for commuter analysis
trips["is_weekend"] = trips["tpep_pickup_datetime"].dt.dayofweek >= 5

# Save cleaned data
trips.to_parquet(os.path.join(data_dir, "cleaned_trips.parquet"), index=False)

# Save cleaning log for transparency
with open(os.path.join(data_dir, "cleaning_log.txt"), "w") as f:
    for entry in log:
        f.write(entry + "\n")
    f.write(f"\nFinal clean rows: {len(trips)}")

print("Cleaning complete!")
for entry in log:
    print(entry)
print(f"Final rows: {len(trips)}")
