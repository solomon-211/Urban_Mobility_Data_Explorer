# NYC Urban Mobility Explorer - Technical Documentation

## 1. Problem Framing and Dataset Analysis

### Dataset Overview
This project analyzes NYC Yellow Taxi trip data from the NYC Taxi & Limousine Commission (TLC). The dataset contains trip-level records including pickup/dropoff timestamps, locations, distances, fares, and payment information.

**Raw Dataset Statistics:**
- Initial trip records: 7,667,792
- Final clean records: 7,440,334
- Data removal rate: 2.97%

### Data Challenges and Cleaning Pipeline

**Challenge 1: Temporal Anomalies**
- Removed 6,294 trips where dropoff occurred before pickup
- These represent data entry errors or system clock issues

**Challenge 2: Physical Impossibilities**
- Removed 171,015 outlier trips with:
  - Distance > 100 miles (likely inter-city trips or errors)
  - Fare > $500 (data entry errors)
  - Passenger count > 6 or ≤ 0 (vehicle capacity violations)

**Challenge 3: Unrealistic Trip Characteristics**
- Removed 49,746 trips with duration < 1 minute or > 3 hours
- Removed 403 trips with speed > 80 mph (physically impossible in NYC traffic)

**Challenge 4: Data Integrity**
- No duplicates found (0 removed)
- No missing critical fields (0 removed)
- All location IDs validated against zone lookup table

### Assumptions Made
1. Trips under 1 minute are likely system errors, not real passenger trips
2. Speed limit of 80 mph accounts for highway segments while filtering errors
3. Fare amounts over $500 are data entry errors, not legitimate long-distance trips
4. Weekend is defined as Saturday and Sunday (dayofweek >= 5)

### Unexpected Observation
**Discovery**: Only 403 trips (0.005%) exceeded 80 mph, suggesting NYC taxi speeds are heavily constrained by traffic congestion. The average speed across all trips is approximately 11.7 mph, indicating severe urban congestion. This influenced our decision to create a "speed_mph" derived feature to analyze traffic patterns by time of day.

---

## 2. System Architecture and Design Decisions

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│  (HTML/CSS/JavaScript + Chart.js + Leaflet.js)             │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Requests
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    FLASK REST API (Python)                   │
│  • 7 API Endpoints                                          │
│  • Custom MinHeap Algorithm (algorithms.py)                 │
│  • CORS enabled for cross-origin requests                   │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL Queries
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   SQLite DATABASE                            │
│  • zones table (263 records) - Dimension                    │
│  • trips table (7.4M records) - Fact                        │
│  • 4 indexes for query optimization                         │
└────────────────────────┬────────────────────────────────────┘
                         │ File I/O
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      DATA FILES                              │
│  • yellow_tripdata.parquet (raw)                            │
│  • taxi_zone_lookup.csv                                     │
│  • taxi_zones.geojson (converted from shapefile)            │
│  • cleaned_trips.parquet (processed)                        │
│  • mobility.db (SQLite database)                            │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack Justification

**Backend: Flask (Python)**
- Chosen for: Rapid development, excellent data science library integration (Pandas, GeoPandas)
- Trade-off: Single-threaded by default (acceptable for academic project, would use Gunicorn in production)

**Database: SQLite**
- Chosen for: Zero configuration, file-based, sufficient for 7.4M records, excellent for development
- Trade-off: Not suitable for concurrent writes (acceptable for read-heavy analytics dashboard)
- Production alternative: PostgreSQL with PostGIS for spatial queries

**Frontend: Vanilla JavaScript + Chart.js + Leaflet.js**
- Chosen for: No build process, lightweight, direct DOM manipulation
- Trade-off: Less maintainable than React/Vue for larger applications
- Benefit: Fast loading, no framework overhead

**Data Processing: Pandas + GeoPandas**
- Chosen for: Industry-standard data manipulation, built-in parquet support, spatial data handling
- Trade-off: Memory intensive for very large datasets
- Benefit: Rapid prototyping and feature engineering

### Key Design Trade-offs

**Trade-off 1: Sampling for Performance**
In `/api/insights/top-zones` and `/api/insights/borough-summary`, we sample 10% of trips (`WHERE t.id % 10 = 0`) to reduce query time from 30+ seconds to 2-3 seconds. This provides statistically valid results while maintaining dashboard responsiveness.

**Trade-off 2: Client-side vs Server-side Filtering**
Filters are applied server-side via SQL WHERE clauses rather than fetching all data and filtering in JavaScript. This reduces network payload but increases database load. For 7.4M records, server-side filtering is essential.

**Trade-off 3: Normalized vs Denormalized Schema**
We use a normalized schema (separate zones and trips tables) rather than denormalizing zone names into the trips table. This saves ~50MB of storage but requires JOIN operations. For analytics queries, the JOIN overhead is acceptable.

---

## 3. Algorithmic Logic and Data Structures

### Custom Algorithm: Top-K Zone Selection using Min-Heap

**Problem**: Find the 15 busiest taxi pickup zones from 263 total zones without using built-in sorting functions.

**Solution**: Implement a min-heap data structure that maintains only the top K elements.

### Pseudo-code
```
FUNCTION find_busiest_zones(zones_dict, k):
    heap = MinHeap(k)
    
    FOR EACH zone IN zones_dict:
        count = zone.trip_count
        zone_id = zone.id
        zone_name = zone.name
        
        IF heap.size < k:
            heap.insert(count, zone_id, zone_name)
            bubble_up(heap.size - 1)
        ELSE IF count > heap.minimum:
            heap.replace_root(count, zone_id, zone_name)
            bubble_down(0)
    
    RETURN heap.get_sorted_descending()

FUNCTION bubble_up(index):
    WHILE index > 0:
        parent = (index - 1) / 2
        IF heap[index] < heap[parent]:
            SWAP(heap[index], heap[parent])
            index = parent
        ELSE:
            BREAK

FUNCTION bubble_down(index):
    WHILE TRUE:
        smallest = index
        left = 2 * index + 1
        right = 2 * index + 2
        
        IF left < heap.size AND heap[left] < heap[smallest]:
            smallest = left
        IF right < heap.size AND heap[right] < heap[smallest]:
            smallest = right
        
        IF smallest != index:
            SWAP(heap[index], heap[smallest])
            index = smallest
        ELSE:
            BREAK
```

### Complexity Analysis

**Time Complexity: O(n log k)**
- n = total number of zones (263)
- k = number of top zones to find (15)
- For each of n zones: O(log k) heap operation
- Total: n × log k = 263 × log₂(15) ≈ 263 × 3.9 ≈ 1,026 operations

**Space Complexity: O(k)**
- Heap stores only k elements (15 zones)
- Constant additional space for variables
- Total: O(15) = O(k)

**Comparison with SQL ORDER BY:**
- SQL ORDER BY uses comparison sort: O(n log n) = 263 × log₂(263) ≈ 263 × 8.04 ≈ 2,114 operations
- Our heap approach: O(n log k) = 263 × log₂(15) ≈ 1,026 operations
- **Performance gain: ~2x faster** (more significant as n increases)

### Why This Matters
When k << n (15 << 263), maintaining a small heap of size k is more efficient than sorting all n elements. This principle scales to larger datasets where the performance difference becomes critical.

---

## 4. Insights and Interpretation

### Insight 1: Evening Rush Hour Dominates Trip Volume

**Derivation Method:**
```sql
SELECT pickup_hour, COUNT(*) as trip_count
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour
```

**Visualization:** Bar chart showing trip counts by hour (0-23)

**Finding:** Peak trip volume occurs at 6-7 PM (evening rush hour) with approximately 450,000+ trips, representing 6% of daily trips. Secondary peak at 9 AM (morning commute) with ~380,000 trips.

**Urban Mobility Interpretation:**
This pattern reveals NYC's commuter behavior. The evening peak is 18% higher than the morning peak, suggesting:
1. More dispersed morning departure times (flexible work start times)
2. Concentrated evening departure times (standard 5-6 PM office closures)
3. Evening social activities (restaurants, entertainment) supplement commuter demand

**Actionable Insight:** Taxi fleet operators should deploy 20% more vehicles during 5-8 PM window to meet demand and reduce wait times.

---

### Insight 2: Late Night Premium Pricing Effect

**Derivation Method:**
```sql
SELECT pickup_hour, AVG(fare_amount) as avg_fare
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour
```

**Visualization:** Line chart showing average fare by hour

**Finding:** Average fare increases from $12 (daytime) to $18-20 (2-5 AM), a 50-67% premium during late night hours.

**Urban Mobility Interpretation:**
Late night fare premiums are driven by:
1. Longer trip distances (fewer short trips, more airport/outer borough travel)
2. Reduced public transit availability (subway reduced service 12-6 AM)
3. Supply-demand imbalance (fewer taxis operating, consistent demand from nightlife)

**Economic Insight:** Late night trips are more profitable per trip but lower volume. Drivers face trade-off between high per-trip earnings and total trip count.

---

### Insight 3: Manhattan Concentration and Fare Efficiency

**Derivation Method:**
```sql
SELECT z.borough, 
       COUNT(*) as total_trips,
       AVG(fare_amount) as avg_fare,
       AVG(trip_distance) as avg_distance,
       AVG(fare_amount / trip_distance) as fare_per_mile
FROM trips t
JOIN zones z ON t.pu_location_id = z.location_id
GROUP BY z.borough
```

**Visualization:** Bar chart comparing boroughs by trip volume

**Finding:** 
- Manhattan: 90%+ of all trips, $12 avg fare, 2.5 mi avg distance, $4.80/mile
- Queens: 5% of trips, $16 avg fare, 4.2 mi avg distance, $3.81/mile
- Brooklyn: 3% of trips, $14 avg fare, 3.8 mi avg distance, $3.68/mile

**Urban Mobility Interpretation:**
Manhattan's dominance reveals:
1. High-density urban core generates short, frequent trips
2. Higher fare-per-mile in Manhattan due to traffic congestion (time-based fare component)
3. Outer boroughs have longer distances but lower per-mile rates (faster highway speeds)

**City Planning Insight:** Manhattan's taxi dependency suggests need for alternative transit solutions. Outer boroughs are underserved, indicating opportunity for ride-sharing expansion or improved public transit connections.

---

## 5. Reflection and Future Work

### Technical Challenges

**Challenge 1: Database Performance**
With 7.4M records, initial queries took 30-60 seconds. Solution: Added indexes on pickup_datetime, pu_location_id, do_location_id, and time_of_day. Result: Query time reduced to 2-5 seconds. Learning: Index selection is critical for large datasets.

**Challenge 2: Memory Management**
Loading entire dataset into Pandas consumed 4GB+ RAM. Solution: Implemented chunked insertion (50,000 rows at a time) in insert_db.py. Learning: Always consider memory constraints when processing large files.

**Challenge 3: Spatial Data Conversion**
Shapefile to GeoJSON conversion required understanding coordinate reference systems (CRS). Solution: Used GeoPandas to reproject to EPSG:4326 (WGS84) for web compatibility. Learning: Spatial data requires careful CRS management.

### Team Challenges
- Coordinating data cleaning decisions required clear documentation of assumptions
- Balancing feature completeness with project timeline
- Ensuring consistent code style across multiple files

### Improvements for Production System

**Scalability:**
1. Migrate to PostgreSQL with connection pooling for concurrent users
2. Implement Redis caching for frequently accessed queries (hourly stats, zone lookup)
3. Add pagination to API endpoints to limit response size
4. Use Apache Spark for processing datasets > 100M records

**Features:**
1. Real-time data ingestion pipeline using Apache Kafka
2. Predictive analytics: forecast demand by location and time using ML models
3. User authentication and personalized dashboards
4. Export functionality (CSV, PDF reports)
5. Mobile-responsive design for tablet/phone access

**Monitoring:**
1. Add logging framework (Python logging module) for debugging
2. Implement API rate limiting to prevent abuse
3. Add health check endpoints for system monitoring
4. Track query performance metrics and set up alerts

**Data Quality:**
1. Automated data validation pipeline with anomaly detection
2. Version control for data cleaning rules
3. A/B testing framework for comparing cleaning strategies

### Next Steps
If this were a real-world product:
1. **Month 1:** Deploy to AWS EC2 with RDS PostgreSQL backend
2. **Month 2:** Implement user authentication and role-based access
3. **Month 3:** Add predictive demand forecasting using historical patterns
4. **Month 4:** Build mobile app for drivers showing high-demand zones
5. **Month 6:** Integrate with real-time traffic data for dynamic routing

---

## Conclusion

This project demonstrates end-to-end data engineering and full-stack development skills:
- Data cleaning with transparency and justification
- Custom algorithm implementation without built-in functions
- Normalized database design with proper indexing
- RESTful API development with filtering capabilities
- Interactive data visualization with meaningful insights

The system successfully processes 7.4M trip records and provides actionable insights into NYC urban mobility patterns, revealing commuter behavior, pricing dynamics, and geographic concentration that inform city planning and transportation policy decisions.

---

**Data Source:** NYC Taxi & Limousine Commission (TLC)  
**Project Repository:** [GitHub Link]  
**Video Walkthrough:** [YouTube Link - To Be Added]

---

*This documentation was prepared as part of an academic assignment demonstrating full-stack development, data engineering, and analytical thinking skills.*
