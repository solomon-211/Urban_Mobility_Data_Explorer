"""Trip Pattern Analysis Script

Queries the SQLite database to derive meaningful urban mobility insights
and prints a console report. This is useful for understanding the data
before building visualisations and for the documentation / technical
report section of the assignment.

Analyses performed:
  1. Peak vs off-peak hour comparison
  2. Borough-level trip breakdown
  3. Weekend vs weekday behaviour
  4. Time-of-day demand distribution
  5. Fare-efficiency analysis (fare per mile by borough)
  6. Speed patterns across hours (congestion proxy)

Output: printed to console and saved to backend/data/analysis_report.txt

Author: Darlene Ayinkamiye
"""

import sqlite3
import os
import sys
from datetime import datetime

# ---------- paths ----------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.append(project_root)

DB_PATH = os.path.join(project_root, "backend", "data", "mobility.db")
REPORT_PATH = os.path.join(project_root, "backend", "data", "analysis_report.txt")


def get_db():
    """Open a read-only connection to the mobility database."""
    if not os.path.exists(DB_PATH):
        print(f"ERROR: database not found at {DB_PATH}")
        print("Run insert_db.py first to create the database.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def section(title):
    """Return a formatted section header string."""
    border = "=" * 60
    return f"\n{border}\n  {title}\n{border}"


# ---------- analysis functions ---------------------------------------------

def overall_summary(conn):
    """Total trips, average fare, distance, duration, speed."""
    row = conn.execute("""
        SELECT COUNT(*)                    AS total_trips,
               ROUND(AVG(fare_amount), 2)  AS avg_fare,
               ROUND(AVG(trip_distance), 2) AS avg_distance,
               ROUND(AVG(trip_duration_minutes), 2) AS avg_duration,
               ROUND(AVG(speed_mph), 2)    AS avg_speed
        FROM trips
    """).fetchone()

    lines = [section("OVERALL SUMMARY")]
    lines.append(f"  Total trips in DB  : {row['total_trips']:>12,}")
    lines.append(f"  Average fare       : ${row['avg_fare']:>10}")
    lines.append(f"  Average distance   : {row['avg_distance']:>10} mi")
    lines.append(f"  Average duration   : {row['avg_duration']:>10} min")
    lines.append(f"  Average speed      : {row['avg_speed']:>10} mph")
    return lines


def peak_vs_offpeak(conn):
    """Compare rush-hour trips (7-9 AM, 5-7 PM) against the rest."""
    rows = conn.execute("""
        SELECT
            CASE
                WHEN pickup_hour BETWEEN 7 AND 9  THEN 'Morning Rush'
                WHEN pickup_hour BETWEEN 17 AND 19 THEN 'Evening Rush'
                ELSE 'Off-Peak'
            END AS period,
            COUNT(*)                          AS trips,
            ROUND(AVG(fare_amount), 2)        AS avg_fare,
            ROUND(AVG(trip_duration_minutes), 2) AS avg_duration,
            ROUND(AVG(speed_mph), 2)          AS avg_speed
        FROM trips
        GROUP BY period
        ORDER BY trips DESC
    """).fetchall()

    lines = [section("PEAK vs OFF-PEAK COMPARISON")]
    header = f"  {'Period':<18} {'Trips':>12} {'Avg Fare':>10} {'Avg Dur':>10} {'Avg Spd':>10}"
    lines.append(header)
    lines.append("  " + "-" * 62)
    for r in rows:
        lines.append(
            f"  {r['period']:<18} {r['trips']:>12,} "
            f"${r['avg_fare']:>8} {r['avg_duration']:>8} min "
            f"{r['avg_speed']:>6} mph"
        )
    return lines


def borough_breakdown(conn):
    """Trip volume and averages per borough."""
    rows = conn.execute("""
        SELECT z.borough,
               COUNT(*)                        AS trips,
               ROUND(AVG(t.fare_amount), 2)    AS avg_fare,
               ROUND(AVG(t.trip_distance), 2)  AS avg_dist,
               ROUND(AVG(t.fare_per_mile), 2)  AS avg_fpm
        FROM trips t
        JOIN zones z ON t.pu_location_id = z.location_id
        GROUP BY z.borough
        ORDER BY trips DESC
    """).fetchall()

    lines = [section("BOROUGH BREAKDOWN")]
    header = f"  {'Borough':<20} {'Trips':>12} {'Avg Fare':>10} {'Avg Dist':>10} {'Fare/Mi':>10}"
    lines.append(header)
    lines.append("  " + "-" * 64)
    for r in rows:
        lines.append(
            f"  {r['borough'] or 'Unknown':<20} {r['trips']:>12,} "
            f"${r['avg_fare']:>8} {r['avg_dist']:>8} mi "
            f"${r['avg_fpm']:>7}"
        )
    return lines


def weekday_vs_weekend(conn):
    """Compare weekday and weekend trip patterns."""
    rows = conn.execute("""
        SELECT
            CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
            COUNT(*)                          AS trips,
            ROUND(AVG(fare_amount), 2)        AS avg_fare,
            ROUND(AVG(trip_distance), 2)      AS avg_dist,
            ROUND(AVG(speed_mph), 2)          AS avg_speed
        FROM trips
        GROUP BY day_type
    """).fetchall()

    lines = [section("WEEKDAY vs WEEKEND")]
    header = f"  {'Type':<12} {'Trips':>12} {'Avg Fare':>10} {'Avg Dist':>10} {'Avg Speed':>10}"
    lines.append(header)
    lines.append("  " + "-" * 56)
    for r in rows:
        lines.append(
            f"  {r['day_type']:<12} {r['trips']:>12,} "
            f"${r['avg_fare']:>8} {r['avg_dist']:>8} mi "
            f"{r['avg_speed']:>7} mph"
        )
    return lines


def time_of_day_demand(conn):
    """Show trip distribution across time-of-day buckets."""
    rows = conn.execute("""
        SELECT time_of_day,
               COUNT(*)                     AS trips,
               ROUND(AVG(fare_amount), 2)   AS avg_fare,
               ROUND(AVG(speed_mph), 2)     AS avg_speed
        FROM trips
        GROUP BY time_of_day
        ORDER BY trips DESC
    """).fetchall()

    lines = [section("TIME-OF-DAY DEMAND")]
    header = f"  {'Period':<14} {'Trips':>12} {'Avg Fare':>10} {'Avg Speed':>10}"
    lines.append(header)
    lines.append("  " + "-" * 48)
    for r in rows:
        lines.append(
            f"  {r['time_of_day']:<14} {r['trips']:>12,} "
            f"${r['avg_fare']:>8} {r['avg_speed']:>7} mph"
        )
    return lines


def hourly_speed_profile(conn):
    """Average speed per hour — acts as a congestion proxy."""
    rows = conn.execute("""
        SELECT pickup_hour,
               COUNT(*) AS trips,
               ROUND(AVG(speed_mph), 2) AS avg_speed
        FROM trips
        GROUP BY pickup_hour
        ORDER BY pickup_hour
    """).fetchall()

    lines = [section("HOURLY SPEED PROFILE (congestion proxy)")]
    header = f"  {'Hour':<8} {'Trips':>12} {'Avg Speed':>10}"
    lines.append(header)
    lines.append("  " + "-" * 32)
    for r in rows:
        bar_len = int(r["avg_speed"] or 0)
        bar = "#" * min(bar_len, 40)
        lines.append(
            f"  {r['pickup_hour']:>2}:00   {r['trips']:>12,} "
            f"{r['avg_speed']:>7} mph  {bar}"
        )
    return lines


# ---------- main -----------------------------------------------------------

def run_analysis():
    """Run every analysis and write the combined report."""
    print("Connecting to mobility database...\n")
    conn = get_db()

    all_lines = []
    all_lines.append("NYC TAXI TRIP — PATTERN ANALYSIS REPORT")
    all_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_lines += overall_summary(conn)
    all_lines += peak_vs_offpeak(conn)
    all_lines += borough_breakdown(conn)
    all_lines += weekday_vs_weekend(conn)
    all_lines += time_of_day_demand(conn)
    all_lines += hourly_speed_profile(conn)

    conn.close()

    # save to file
    with open(REPORT_PATH, "w") as f:
        for line in all_lines:
            f.write(line + "\n")

    # also print to console
    for line in all_lines:
        print(line)

    print(f"\nReport saved to: {REPORT_PATH}")
    print("Done!")


if __name__ == "__main__":
    run_analysis()
