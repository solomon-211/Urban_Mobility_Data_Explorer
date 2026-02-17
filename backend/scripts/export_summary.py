"""Export Summary Script

Exports key aggregated statistics from the database into small CSV files
that can be used for the technical documentation, charts in the PDF
report, or quick offline review without needing to spin up the full
backend server.

Exports generated (in backend/data/exports/):
  1. hourly_summary.csv   — trip count, avg fare, avg speed per hour
  2. borough_summary.csv  — trip count, avg fare, avg distance per borough
  3. zone_top20.csv       — the 20 busiest pickup zones
  4. daily_pattern.csv    — weekday vs weekend comparison
  5. cleaning_stats.csv   — a snapshot of cleaning log numbers

Author: Darlene Ayinkamiye
"""

import sqlite3
import csv
import os
import sys
from datetime import datetime

# ---------- paths ----------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.append(project_root)

DB_PATH = os.path.join(project_root, "backend", "data", "mobility.db")
EXPORT_DIR = os.path.join(project_root, "backend", "data", "exports")
CLEANING_LOG = os.path.join(project_root, "backend", "data", "cleaning_log.txt")


def get_db():
    """Open a connection to the database."""
    if not os.path.exists(DB_PATH):
        print(f"ERROR: database not found at {DB_PATH}")
        print("Run insert_db.py first.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def write_csv(filename, headers, rows):
    """Write a list of row-dicts to a CSV file inside the export folder."""
    path = os.path.join(EXPORT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row[h] for h in headers])
    print(f"  Saved {filename}  ({len(rows)} rows)")


# ---------- export functions -----------------------------------------------

def export_hourly(conn):
    """Hourly trip counts, average fare, average speed."""
    data = conn.execute("""
        SELECT pickup_hour,
               COUNT(*)                       AS trip_count,
               ROUND(AVG(fare_amount), 2)     AS avg_fare,
               ROUND(AVG(trip_distance), 2)   AS avg_distance,
               ROUND(AVG(trip_duration_minutes), 2) AS avg_duration,
               ROUND(AVG(speed_mph), 2)       AS avg_speed
        FROM trips
        GROUP BY pickup_hour
        ORDER BY pickup_hour
    """).fetchall()

    headers = ["pickup_hour", "trip_count", "avg_fare",
               "avg_distance", "avg_duration", "avg_speed"]
    write_csv("hourly_summary.csv", headers, [dict(r) for r in data])


def export_borough(conn):
    """Per-borough aggregate statistics."""
    data = conn.execute("""
        SELECT z.borough,
               COUNT(*)                       AS trip_count,
               ROUND(AVG(t.fare_amount), 2)   AS avg_fare,
               ROUND(AVG(t.trip_distance), 2) AS avg_distance,
               ROUND(AVG(t.fare_per_mile), 2) AS avg_fare_per_mile,
               ROUND(AVG(t.speed_mph), 2)     AS avg_speed
        FROM trips t
        JOIN zones z ON t.pu_location_id = z.location_id
        GROUP BY z.borough
        ORDER BY trip_count DESC
    """).fetchall()

    headers = ["borough", "trip_count", "avg_fare",
               "avg_distance", "avg_fare_per_mile", "avg_speed"]
    write_csv("borough_summary.csv", headers, [dict(r) for r in data])


def export_top_zones(conn):
    """Top 20 busiest pickup zones."""
    data = conn.execute("""
        SELECT z.zone_name, z.borough,
               COUNT(*)                       AS trip_count,
               ROUND(AVG(t.fare_amount), 2)   AS avg_fare
        FROM trips t
        JOIN zones z ON t.pu_location_id = z.location_id
        GROUP BY t.pu_location_id
        ORDER BY trip_count DESC
        LIMIT 20
    """).fetchall()

    headers = ["zone_name", "borough", "trip_count", "avg_fare"]
    write_csv("zone_top20.csv", headers, [dict(r) for r in data])


def export_daily_pattern(conn):
    """Weekday versus weekend comparison."""
    data = conn.execute("""
        SELECT
            CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
            COUNT(*)                          AS trip_count,
            ROUND(AVG(fare_amount), 2)        AS avg_fare,
            ROUND(AVG(trip_distance), 2)      AS avg_distance,
            ROUND(AVG(speed_mph), 2)          AS avg_speed
        FROM trips
        GROUP BY day_type
    """).fetchall()

    headers = ["day_type", "trip_count", "avg_fare", "avg_distance", "avg_speed"]
    write_csv("daily_pattern.csv", headers, [dict(r) for r in data])


def export_cleaning_stats():
    """Parse the cleaning log and save a structured CSV version."""
    if not os.path.exists(CLEANING_LOG):
        print("  Skipping cleaning_stats.csv — cleaning_log.txt not found")
        return

    entries = []
    with open(CLEANING_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # each line looks like: "Duplicates removed: 1234"
            # or "Final clean rows: 5678"
            if ":" in line:
                parts = line.split(":", 1)
                step = parts[0].strip()
                value = parts[1].strip()
                entries.append({"step": step, "value": value})

    if entries:
        path = os.path.join(EXPORT_DIR, "cleaning_stats.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["step", "value"])
            for e in entries:
                writer.writerow([e["step"], e["value"]])
        print(f"  Saved cleaning_stats.csv  ({len(entries)} rows)")


# ---------- main -----------------------------------------------------------

def run_exports():
    """Run all exports."""
    print("Exporting summary data...\n")

    # make sure the export directory exists
    os.makedirs(EXPORT_DIR, exist_ok=True)

    conn = get_db()

    export_hourly(conn)
    export_borough(conn)
    export_top_zones(conn)
    export_daily_pattern(conn)
    export_cleaning_stats()

    conn.close()

    print(f"\nAll exports saved to: {EXPORT_DIR}")
    print("You can open these CSVs in Excel or Google Sheets for reports.")
    print("Done!")


if __name__ == "__main__":
    run_exports()
