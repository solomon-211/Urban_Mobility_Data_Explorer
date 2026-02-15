"""Database Schema and Connection Module

Defines normalized relational schema with zones (dimension) and trips (fact) tables.
Includes 4 indexes for query optimization.
"""

import sqlite3
import os

def get_connection():
    """Connect to SQLite database and return connection with row factory"""
    # Get the absolute path to the database file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "data", "mobility.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def create_tables():
    """Create normalized schema with proper relationships and indexes"""
    conn = get_connection()
    conn.executescript("""
        -- Dimension table for taxi zones
        CREATE TABLE IF NOT EXISTS zones (
            location_id INTEGER PRIMARY KEY,
            borough TEXT,
            zone_name TEXT,
            service_zone TEXT
        );

        -- Fact table for trip records with foreign keys
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pickup_datetime TEXT,
            dropoff_datetime TEXT,
            passenger_count INTEGER,
            trip_distance REAL,
            pu_location_id INTEGER,
            do_location_id INTEGER,
            fare_amount REAL,
            tip_amount REAL,
            total_amount REAL,
            payment_type INTEGER,
            trip_duration_minutes REAL,
            speed_mph REAL,
            fare_per_mile REAL,
            pickup_hour INTEGER,
            time_of_day TEXT,
            is_weekend INTEGER
        );

        -- Indexes to speed up common queries
        CREATE INDEX IF NOT EXISTS idx_pickup_datetime ON trips(pickup_datetime);
        CREATE INDEX IF NOT EXISTS idx_pu_location ON trips(pu_location_id);
        CREATE INDEX IF NOT EXISTS idx_do_location ON trips(do_location_id);
        CREATE INDEX IF NOT EXISTS idx_time_of_day ON trips(time_of_day);
    """)
    conn.commit()
    conn.close()
    print("Tables created")

if __name__ == "__main__":
    create_tables()
