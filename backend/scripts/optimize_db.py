import sqlite3
import os

# Get database path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
db_path = os.path.join(project_root, "backend", "data", "mobility.db")

print(f"Optimizing database: {db_path}")
print("This may take a few minutes...\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add composite indexes for faster JOINs and aggregations
print("Creating indexes...")

try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pu_location_id ON trips(pu_location_id)")
    print("✓ Index on trips.pu_location_id")
except Exception as e:
    print(f"  Already exists: idx_pu_location_id")

try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pickup_hour ON trips(pickup_hour)")
    print("✓ Index on trips.pickup_hour")
except Exception as e:
    print(f"  Already exists: idx_pickup_hour")

conn.commit()

# Run ANALYZE to update query planner statistics
print("\nAnalyzing database for query optimization...")
cursor.execute("ANALYZE")
conn.commit()

print("\n✅ Database optimized!")

# Show stats
count = cursor.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
print(f"\nTotal trips: {count:,}")

conn.close()
print("\nRestart Flask server for changes to take effect.")
