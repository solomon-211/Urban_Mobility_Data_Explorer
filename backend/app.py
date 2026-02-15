"""Flask REST API for NYC Taxi Trip Data

Provides 7 endpoints for querying trip data with dynamic filtering.
Uses custom MinHeap algorithm for top-zones endpoint (no SQL ORDER BY).
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_connection
import json
import os

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

@app.route("/api/zones", methods=["GET"])
def get_zones():
    """Get all taxi zones with borough and zone name"""
    conn = get_connection()
    zones = conn.execute("SELECT * FROM zones").fetchall()
    conn.close()
    return jsonify([dict(z) for z in zones])

@app.route("/api/trips", methods=["GET"])
def get_trips():
    """Get filtered trip records with optional borough, hour, time_of_day filters"""
    conn = get_connection()

    # Optional filters from query params
    hour = request.args.get("hour")
    borough = request.args.get("borough")
    time_of_day = request.args.get("time_of_day")
    limit = request.args.get("limit", 500)

    # Build dynamic query with JOIN to get zone names
    query = """
        SELECT t.*, 
               p.zone_name as pickup_zone, p.borough as pickup_borough,
               d.zone_name as dropoff_zone, d.borough as dropoff_borough
        FROM trips t
        LEFT JOIN zones p ON t.pu_location_id = p.location_id
        LEFT JOIN zones d ON t.do_location_id = d.location_id
        WHERE 1=1
    """
    params = []

    if hour:
        query += " AND t.pickup_hour = ?"
        params.append(hour)
    if time_of_day:
        query += " AND t.time_of_day = ?"
        params.append(time_of_day)
    if borough:
        query += " AND p.borough = ?"
        params.append(borough)

    query += f" LIMIT ?"
    params.append(limit)

    trips = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(t) for t in trips])

@app.route("/api/insights/hourly", methods=["GET"])
def hourly_trips():
    """Get trip counts and average fare by hour with optional filters"""
    conn = get_connection()
    
    # Get filter parameters
    borough = request.args.get("borough")
    time_of_day = request.args.get("time_of_day")
    hour = request.args.get("hour")
    
    # Build query with filters
    query = """
        SELECT t.pickup_hour, COUNT(*) as trip_count,
               AVG(t.fare_amount) as avg_fare,
               AVG(t.trip_duration_minutes) as avg_duration
        FROM trips t
    """
    
    where_clauses = []
    params = []
    
    if borough or time_of_day or hour:
        query += " LEFT JOIN zones z ON t.pu_location_id = z.location_id WHERE 1=1"
        if borough:
            where_clauses.append(" AND z.borough = ?")
            params.append(borough)
        if time_of_day:
            where_clauses.append(" AND t.time_of_day = ?")
            params.append(time_of_day)
        if hour:
            where_clauses.append(" AND t.pickup_hour = ?")
            params.append(hour)
        query += "".join(where_clauses)
    
    query += " GROUP BY t.pickup_hour ORDER BY t.pickup_hour"
    
    data = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in data])

@app.route("/api/insights/top-zones", methods=["GET"])
def top_zones():
    """Get top 15 busiest zones using custom MinHeap algorithm (no SQL ORDER BY)"""
    from algorithms import find_busiest_zones
    
    conn = get_connection()
    
    # Get filter parameters
    borough = request.args.get("borough")
    time_of_day = request.args.get("time_of_day")
    hour = request.args.get("hour")
    
    # Build query WITHOUT ORDER BY - we'll sort manually with heap
    query = """
        SELECT t.pu_location_id, z.zone_name, z.borough,
               COUNT(*) as trip_count,
               AVG(t.fare_amount) as avg_fare
        FROM trips t
        JOIN zones z ON t.pu_location_id = z.location_id
        WHERE t.id % 10 = 0
    """
    
    params = []
    if borough:
        query += " AND z.borough = ?"
        params.append(borough)
    if time_of_day:
        query += " AND t.time_of_day = ?"
        params.append(time_of_day)
    if hour:
        query += " AND t.pickup_hour = ?"
        params.append(hour)
    
    query += " GROUP BY t.pu_location_id"
    
    data = conn.execute(query, params).fetchall()
    conn.close()
    
    # Convert to dictionary format for algorithm
    zones_dict = {}
    for row in data:
        zones_dict[row['pu_location_id']] = {
            'count': row['trip_count'],
            'zone_name': row['zone_name'],
            'borough': row['borough'],
            'avg_fare': row['avg_fare']
        }
    
    # Use custom heap algorithm instead of SQL ORDER BY
    top_zones_list = find_busiest_zones(zones_dict, k=15)
    
    # Format results
    results = []
    for count, zone_id, zone_name in top_zones_list:
        zone_data = zones_dict[zone_id]
        results.append({
            'zone_name': zone_name,
            'borough': zone_data['borough'],
            'trip_count': count,
            'avg_fare': zone_data['avg_fare']
        })
    
    return jsonify(results)

@app.route("/api/insights/borough-summary", methods=["GET"])
def borough_summary():
    """Get aggregate statistics by borough with optional filters"""
    conn = get_connection()
    
    # Get filter parameters
    borough = request.args.get("borough")
    time_of_day = request.args.get("time_of_day")
    hour = request.args.get("hour")
    
    # Build query with filters (10% sample for performance)
    query = """
        SELECT z.borough,
               COUNT(*) * 10 as total_trips,
               AVG(t.trip_distance) as avg_distance,
               AVG(t.fare_amount) as avg_fare,
               AVG(t.trip_duration_minutes) as avg_duration
        FROM trips t
        JOIN zones z ON t.pu_location_id = z.location_id
        WHERE t.id % 10 = 0
    """
    
    params = []
    if borough:
        query += " AND z.borough = ?"
        params.append(borough)
    if time_of_day:
        query += " AND t.time_of_day = ?"
        params.append(time_of_day)
    if hour:
        query += " AND t.pickup_hour = ?"
        params.append(hour)
    
    query += " GROUP BY z.borough"
    
    data = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in data])

@app.route("/api/geojson", methods=["GET"])
def get_geojson():
    """Get GeoJSON with trip counts for choropleth map visualization"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        geojson_path = os.path.join(current_dir, "data", "taxi_zones.geojson")
        
        with open(geojson_path, "r") as f:
            data = json.load(f)
        
        # Add trip counts to each zone feature
        conn = get_connection()
        counts = conn.execute("SELECT pu_location_id, COUNT(*) as count FROM trips GROUP BY pu_location_id").fetchall()
        conn.close()
        
        counts_dict = {row["pu_location_id"]: row["count"] for row in counts}
        
        for feature in data["features"]:
            loc_id = feature["properties"].get("LocationID")
            feature["properties"]["trip_count"] = counts_dict.get(loc_id, 0)
        
        return jsonify(data)
    except Exception as e:
        print(f"GeoJSON Error: {str(e)}")
        return jsonify({"error": str(e)}), 404

@app.route("/api/stats/summary", methods=["GET"])
def get_summary():
    """Get overall summary statistics for dashboard cards"""
    conn = get_connection()
    stats = conn.execute("""
        SELECT COUNT(*) as total_trips,
               AVG(fare_amount) as avg_fare,
               AVG(trip_distance) as avg_distance,
               AVG(speed_mph) as avg_speed
        FROM trips
    """).fetchone()
    conn.close()
    return jsonify(dict(stats))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
