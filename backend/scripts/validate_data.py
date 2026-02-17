"""Data Validation & Quality Report Script

This script checks the integrity and quality of the cleaned dataset
before it gets loaded into the database. It catches any remaining issues
that might have slipped through the cleaning pipeline and produces a
human-readable summary of the data's overall health.

Checks performed:
  - Column presence (all expected fields are there)
  - Null / missing value counts per column
  - Numeric range validation (distance, fare, speed, duration)
  - Categorical value verification (time_of_day, is_weekend)
  - Referential integrity against the zone lookup table
  - Basic statistical profile (mean, median, std for core fields)

Output: backend/data/validation_report.txt

Author: Darlene Ayinkamiye
"""

import pandas as pd
import os
import sys
from datetime import datetime

# ---------- paths ----------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
data_dir = os.path.join(project_root, "backend", "data")

CLEANED_PATH = os.path.join(data_dir, "cleaned_trips.parquet")
ZONES_PATH = os.path.join(data_dir, "taxi_zone_lookup.csv")
REPORT_PATH = os.path.join(data_dir, "validation_report.txt")

# ---------- helpers --------------------------------------------------------

def write_section(file_handle, title, content_lines):
    """Write a titled section to the report file."""
    file_handle.write("\n" + "=" * 60 + "\n")
    file_handle.write(f"  {title}\n")
    file_handle.write("=" * 60 + "\n")
    for line in content_lines:
        file_handle.write(line + "\n")


def check_columns(df):
    """Verify that every expected column exists in the dataframe."""
    expected = [
        "tpep_pickup_datetime", "tpep_dropoff_datetime",
        "PULocationID", "DOLocationID",
        "trip_distance", "fare_amount", "tip_amount", "total_amount",
        "passenger_count", "payment_type",
        "trip_duration_minutes", "speed_mph", "fare_per_mile",
        "pickup_hour", "time_of_day", "is_weekend"
    ]
    present = []
    missing = []
    for col in expected:
        if col in df.columns:
            present.append(col)
        else:
            missing.append(col)
    return present, missing


def check_nulls(df):
    """Return per-column null counts and percentages."""
    total = len(df)
    lines = []
    any_nulls = False
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        if null_count > 0:
            pct = (null_count / total) * 100
            lines.append(f"  {col:35s}  {null_count:>10,}  ({pct:.2f}%)")
            any_nulls = True
    if not any_nulls:
        lines.append("  No null values found — data looks clean!")
    return lines


def check_numeric_ranges(df):
    """Flag any values that fall outside reasonable physical limits."""
    checks = {
        "trip_distance": (0, 100, "miles"),
        "fare_amount": (0, 500, "dollars"),
        "speed_mph": (0, 80, "mph"),
        "trip_duration_minutes": (1, 180, "minutes"),
        "passenger_count": (1, 6, "passengers"),
    }
    lines = []
    all_ok = True
    for col, (low, high, unit) in checks.items():
        if col not in df.columns:
            continue
        below = int((df[col] <= low).sum())
        above = int((df[col] >= high).sum())
        if below > 0 or above > 0:
            lines.append(f"  {col}: {below} rows <= {low} {unit}, "
                         f"{above} rows >= {high} {unit}")
            all_ok = False
    if all_ok:
        lines.append("  All numeric columns within expected ranges.")
    return lines


def check_categoricals(df):
    """Make sure categorical columns only contain valid values."""
    lines = []
    valid_tod = {"Morning", "Afternoon", "Evening", "Night"}
    valid_weekend = {True, False, 0, 1}

    if "time_of_day" in df.columns:
        actual = set(df["time_of_day"].dropna().unique())
        unexpected = actual - valid_tod
        if unexpected:
            lines.append(f"  time_of_day has unexpected values: {unexpected}")
        else:
            lines.append(f"  time_of_day OK — values: {sorted(actual)}")

    if "is_weekend" in df.columns:
        actual = set(df["is_weekend"].dropna().unique())
        if actual - valid_weekend:
            lines.append(f"  is_weekend has unexpected values: {actual}")
        else:
            lines.append(f"  is_weekend OK — values: {sorted(actual)}")

    if "pickup_hour" in df.columns:
        h_min = int(df["pickup_hour"].min())
        h_max = int(df["pickup_hour"].max())
        if h_min < 0 or h_max > 23:
            lines.append(f"  pickup_hour out of range: min={h_min}, max={h_max}")
        else:
            lines.append(f"  pickup_hour OK — range {h_min} to {h_max}")

    return lines


def check_referential_integrity(df, zones_df):
    """Ensure every location ID in trips exists in the zone lookup."""
    valid_ids = set(zones_df["LocationID"].tolist())
    lines = []
    for col in ["PULocationID", "DOLocationID"]:
        if col not in df.columns:
            continue
        trip_ids = set(df[col].dropna().astype(int).unique())
        orphans = trip_ids - valid_ids
        if orphans:
            lines.append(f"  {col}: {len(orphans)} orphan IDs not in zone "
                         f"lookup -> {sorted(orphans)[:10]}...")
        else:
            lines.append(f"  {col}: all {len(trip_ids)} unique IDs are valid")
    return lines


def compute_stats(df):
    """Compute basic descriptive statistics for core numeric fields."""
    fields = ["trip_distance", "fare_amount", "tip_amount",
              "trip_duration_minutes", "speed_mph", "fare_per_mile"]
    lines = []
    header = f"  {'Column':30s} {'Mean':>10s} {'Median':>10s} {'Std':>10s}"
    lines.append(header)
    lines.append("  " + "-" * 62)
    for col in fields:
        if col not in df.columns:
            continue
        mean_val = df[col].mean()
        med_val = df[col].median()
        std_val = df[col].std()
        lines.append(f"  {col:30s} {mean_val:10.2f} {med_val:10.2f} {std_val:10.2f}")
    return lines


# ---------- main -----------------------------------------------------------

def run_validation():
    """Run all validation checks and write the report."""
    print("Starting data validation...\n")

    if not os.path.exists(CLEANED_PATH):
        print(f"ERROR: cleaned data file not found at {CLEANED_PATH}")
        print("Run clean_data.py first.")
        sys.exit(1)

    trips = pd.read_parquet(CLEANED_PATH)
    zones = pd.read_csv(ZONES_PATH)

    print(f"Loaded {len(trips):,} cleaned trip records")
    print(f"Loaded {len(zones)} zone records\n")

    with open(REPORT_PATH, "w") as f:
        # header
        f.write("NYC TAXI DATA — VALIDATION REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Records checked: {len(trips):,}\n")

        # 1 — columns
        present, missing = check_columns(trips)
        col_lines = [f"  Present: {len(present)}/{len(present)+len(missing)}"]
        if missing:
            col_lines.append(f"  MISSING: {missing}")
        write_section(f, "COLUMN PRESENCE CHECK", col_lines)

        # 2 — nulls
        null_lines = check_nulls(trips)
        write_section(f, "NULL VALUE CHECK", null_lines)

        # 3 — numeric ranges
        range_lines = check_numeric_ranges(trips)
        write_section(f, "NUMERIC RANGE CHECK", range_lines)

        # 4 — categoricals
        cat_lines = check_categoricals(trips)
        write_section(f, "CATEGORICAL VALUE CHECK", cat_lines)

        # 5 — referential integrity
        ref_lines = check_referential_integrity(trips, zones)
        write_section(f, "REFERENTIAL INTEGRITY CHECK", ref_lines)

        # 6 — descriptive stats
        stat_lines = compute_stats(trips)
        write_section(f, "DESCRIPTIVE STATISTICS", stat_lines)

        f.write("\n" + "=" * 60 + "\n")
        f.write("  VALIDATION COMPLETE\n")
        f.write("=" * 60 + "\n")

    print(f"Report saved to: {REPORT_PATH}")
    print("Done!\n")

    # also print it to the console so the user can see it right away
    with open(REPORT_PATH, "r") as f:
        print(f.read())


if __name__ == "__main__":
    run_validation()
