# CODE EXPLANATION - NYC Urban Mobility Explorer

## BACKEND FILES

### 1. backend/algorithms.py

**Purpose**: Custom min-heap implementation for finding top K busiest zones without built-in sorting.

**Key Components**:

**MinHeap Class**:
- `__init__(self, k)`: Initializes heap with capacity k (15 zones)
- `self.items = []`: Stores tuples of (count, zone_id, name)
- `self.k = k`: Maximum heap size

**add(self, count, zone_id, name)**: 
- If heap not full: append item and bubble up
- If count > minimum: replace root and bubble down
- Maintains only top K elements

**_fix_up(self, i)**:
- Moves item up the heap to maintain min-heap property
- Compares with parent at index (i-1)//2
- Swaps if child < parent
- Continues until heap property restored

**_fix_down(self, i)**:
- Moves item down the heap
- Compares with children at 2*i+1 and 2*i+2
- Swaps with smallest child
- Continues until heap property restored

**get_sorted(self)**:
- Returns items sorted descending
- Uses manual bubble sort (no built-in sorted())
- Compares all pairs and swaps if needed

**find_busiest_zones(zones, k=15)**:
- Creates MinHeap of size k
- Iterates through all zones
- Adds each zone to heap
- Returns sorted top K zones

**Time Complexity**: O(n log k) where n=263 zones, k=15
**Space Complexity**: O(k) = O(15)

---

### 2. backend/database.py

**Purpose**: Database schema definition and connection management.

**get_connection()**:
- Creates SQLite connection to mobility.db
- Sets row_factory to sqlite3.Row for dict-like access
- Returns connection object

**create_tables()**:
- Creates zones table (dimension):
  - location_id: Primary key
  - borough: Text (Manhattan, Brooklyn, etc)
  - zone_name: Text (specific zone)
  - service_zone: Text (Yellow, Green, etc)

- Creates trips table (fact):
  - id: Auto-increment primary key
  - pickup_datetime, dropoff_datetime: Text (ISO format)
  - passenger_count: Integer
  - trip_distance: Real (miles)
  - pu_location_id, do_location_id: Foreign keys to zones
  - fare_amount, tip_amount, total_amount: Real (dollars)
  - payment_type: Integer (1=credit, 2=cash)
  - trip_duration_minutes: Real (derived)
  - speed_mph: Real (derived)
  - fare_per_mile: Real (derived)
  - pickup_hour: Integer (0-23)
  - time_of_day: Text (Morning/Afternoon/Evening/Night)
  - is_weekend: Integer (0 or 1)

- Creates 4 indexes:
  - idx_pickup_datetime: Speeds up time-based queries
  - idx_pu_location: Speeds up pickup location filters
  - idx_do_location: Speeds up dropoff location filters
  - idx_time_of_day: Speeds up time period filters

**Why Normalized Schema**:
- Zones table stores location data once (263 records)
- Trips table references zones via foreign keys
- Saves ~50MB vs denormalized (zone names in every trip)
- Enables efficient JOIN queries

---

### 3. backend/app.py

**Purpose**: Flask REST API with 7 endpoints for querying trip data.

**Imports**:
- Flask: Web framework
- CORS: Cross-origin resource sharing
- get_connection: Database access
- json, os: File and JSON handling

**app = Flask(__name__)**: Creates Flask application
**CORS(app)**: Enables frontend to call API from different port

**Endpoint 1: GET /api/zones**
- Returns all 263 taxi zones
- Query: SELECT * FROM zones
- Response: JSON array of zone objects

**Endpoint 2: GET /api/trips**
- Returns filtered trip records
- Query params: hour, borough, time_of_day, limit
- Builds dynamic SQL with WHERE clauses
- JOINs with zones to get zone names
- Default limit: 500 records
- Response: JSON array of trip objects

**Endpoint 3: GET /api/insights/hourly**
- Returns trip counts and avg fare by hour (0-23)
- Supports filtering by borough, time_of_day, hour
- Groups by pickup_hour
- Orders by pickup_hour
- Response: 24 objects (one per hour)

**Endpoint 4: GET /api/insights/top-zones**
- Returns top 15 busiest pickup zones
- Uses custom MinHeap algorithm (NO SQL ORDER BY)
- Samples 10% of trips (WHERE t.id % 10 = 0) for speed
- Fetches all zone counts from DB
- Passes to find_busiest_zones() function
- Response: 15 zone objects sorted by trip count

**Endpoint 5: GET /api/insights/borough-summary**
- Returns aggregate stats by borough
- Samples 10% of trips for performance
- Calculates: total_trips, avg_distance, avg_fare, avg_duration
- Groups by borough
- Response: 5 objects (one per borough)

**Endpoint 6: GET /api/geojson**
- Returns GeoJSON with trip counts for map
- Loads taxi_zones.geojson file
- Queries trip counts per zone
- Adds trip_count to each GeoJSON feature
- Response: GeoJSON FeatureCollection

**Endpoint 7: GET /api/stats/summary**
- Returns overall summary statistics
- Calculates: total_trips, avg_fare, avg_distance, avg_speed
- No grouping (aggregate across all trips)
- Response: Single object with 4 metrics

**app.run(debug=True, port=5000)**:
- Starts Flask server on port 5000
- Debug mode enables auto-reload on code changes

---

### 4. backend/scripts/clean_data.py

**Purpose**: 7-step data cleaning pipeline with feature engineering.

**Path Setup**:
- Gets script directory
- Calculates project root (2 levels up)
- Sets data_dir to backend/data/

**Data Loading**:
- Checks for yellow_tripdata.parquet first
- Falls back to yellow_tripdata.csv
- Raises error if neither exists
- Loads taxi_zone_lookup.csv

**Cleaning Steps**:

**Step 1: Remove Duplicates**
- Uses pandas drop_duplicates()
- Logs count removed

**Step 2: Drop Missing Critical Fields**
- Drops rows with NaN in:
  - tpep_pickup_datetime
  - tpep_dropoff_datetime
  - PULocationID
  - DOLocationID
  - fare_amount
  - trip_distance
- These fields required for all calculations

**Step 3: Fix Timestamps**
- Converts to datetime objects
- Removes impossible timestamps (dropoff before pickup)

**Step 4: Remove Outliers**
- Distance: 0 < distance < 100 miles
- Fare: 0 < fare < $500
- Passengers: 0 < count <= 6
- Filters physically impossible values

**Step 5: Validate Location IDs**
- Creates set of valid IDs from zone lookup
- Filters trips with invalid PULocationID or DOLocationID
- Ensures referential integrity

**Step 6: Remove Bad Durations**
- Calculates trip_duration_minutes
- Removes < 1 minute (system errors)
- Removes > 180 minutes (3 hours)

**Step 7: Remove Impossible Speeds**
- Calculates speed_mph
- Removes > 80 mph (impossible in NYC)

**Feature Engineering**:

**Feature 1: trip_duration_minutes**
- (dropoff - pickup) in seconds / 60
- Reveals congestion patterns

**Feature 2: speed_mph**
- distance / (duration / 60)
- Shows traffic behavior by time

**Feature 3: fare_per_mile**
- fare_amount / trip_distance
- Economic efficiency metric

**Feature 4: time_of_day**
- Morning: 5-12
- Afternoon: 12-17
- Evening: 17-21
- Night: 21-5
- Categorizes for rush hour analysis

**Feature 5: is_weekend**
- dayofweek >= 5 (Saturday=5, Sunday=6)
- Boolean flag for weekend trips

**Output**:
- Saves cleaned_trips.parquet
- Saves cleaning_log.txt with all removal counts
- Prints summary to console

---

### 5. backend/scripts/convert_zones.py

**Purpose**: Convert shapefile to web-compatible GeoJSON.

**Process**:
- Reads taxi_zones.shp using GeoPandas
- Reprojects to EPSG:4326 (WGS84 coordinate system)
- Saves as taxi_zones.geojson
- Prints count and sample data

**Why Needed**:
- Shapefiles are binary format
- GeoJSON is text-based, web-compatible
- Leaflet.js requires GeoJSON
- WGS84 is standard for web maps

---

### 6. backend/scripts/insert_db.py

**Purpose**: Load cleaned data into SQLite database.

**Process**:

**Step 1**: Call create_tables() to set up schema

**Step 2**: Load zones
- Reads taxi_zone_lookup.csv
- Renames columns to match schema
- Inserts into zones table (replaces if exists)

**Step 3**: Load trips
- Reads cleaned_trips.parquet
- Selects only needed columns
- Renames to match schema
- Inserts in 50,000-row chunks
- Prints progress every chunk

**Why Chunking**:
- 7.4M rows would consume 4GB+ RAM
- Chunking keeps memory usage low
- Progress tracking shows it's working

**Time**: ~10-15 minutes for 7.4M records


## FRONTEND FILES

### 7. frontend/index.html

**Purpose**: Dashboard structure and layout.

**Head Section**:
- Sets UTF-8 encoding
- Responsive viewport for mobile
- Links to style.css
- Loads Leaflet CSS (for maps)
- Loads Leaflet JS library
- Loads Chart.js library

**Header**:
- Title: NYC Urban Mobility Explorer
- Subtitle: Real-time analysis description

**Filters Section**:
- Borough dropdown: 5 NYC boroughs + "All"
- Time of Day dropdown: 4 periods + "All"
- Hour dropdown: Populated by JavaScript (0-23)
- Apply Filters button: Triggers chart reload
- Reset button: Clears all filters

**Summary Stats Cards**:
- 4 cards displaying:
  - Total Trips
  - Average Fare
  - Average Distance
  - Average Speed
- Values populated by JavaScript from API

**Map Section**:
- H2 title
- div#map: Container for Leaflet map
- Insight caption explaining the visualization

**Charts Section**:
- 4 chart containers, each with:
  - H2 title
  - canvas element for Chart.js
  - Insight caption with interpretation

**Chart 1: Trips by Hour**
- Bar chart showing 24-hour distribution
- Reveals rush hour patterns

**Chart 2: Average Fare by Hour**
- Line chart showing fare trends
- Shows late-night premium

**Chart 3: Top 15 Pickup Zones**
- Horizontal bar chart
- Uses custom heap algorithm data

**Chart 4: Borough Comparison**
- Vertical bar chart
- Shows Manhattan dominance

**Footer**:
- Data source attribution
- Technology stack mention

**Script Tag**:
- Loads app.js (must be last for DOM access)

---

### 8. frontend/app.js

**Purpose**: Dashboard interactivity and data visualization.

**Constants**:
- API_BASE = 'http://localhost:5000/api'
- Base URL for all API calls

**Global Variables**:
- charts = {}: Stores Chart.js instances
- map: Stores Leaflet map instance

**DOMContentLoaded Event**:
- Fires when HTML fully loaded
- Calls initialization functions:
  - populateHourFilter()
  - initMap()
  - loadSummaryStats()
  - loadHourlyChart()
  - loadZonesChart()
  - loadBoroughChart()
- Attaches event listeners to buttons

**populateHourFilter()**:
- Loops 0-23
- Creates option elements
- Adds to hourFilter select
- Formats as "0:00", "1:00", etc.

**initMap()**:
- Creates Leaflet map centered on NYC (40.7128, -74.0060)
- Zoom level 11
- Adds OpenStreetMap tile layer
- Fetches /api/geojson
- Creates GeoJSON layer with:
  - Color-coded by trip count (getColor function)
  - Tooltips showing zone, borough, trip count
  - 8-level color gradient (yellow to dark red)

**getColor(count)**:
- Returns color based on trip volume
- >10000: Dark red (#800026)
- >5000: Red (#BD0026)
- >2000: Orange-red (#E31A1C)
- >1000: Orange (#FC4E2A)
- >500: Light orange (#FD8D3C)
- >200: Yellow-orange (#FEB24C)
- >100: Light yellow (#FED976)
- <=100: Pale yellow (#FFEDA0)

**loadSummaryStats()**:
- Fetches /api/stats/summary
- Updates 4 stat card values:
  - totalTrips: Formatted with commas
  - avgFare: Formatted as $X.XX
  - avgDistance: Formatted as X.XX mi
  - avgSpeed: Formatted as X.X mph

**loadHourlyChart(borough, timeOfDay, hour)**:
- Builds URL with filter params
- Fetches /api/insights/hourly
- Destroys old chart if exists
- Creates bar chart with:
  - X-axis: Hours (0:00 - 23:00)
  - Y-axis: Trip count
  - Green bars
- Calls loadFareChart() with same data

**loadFareChart(hourlyData)**:
- Uses data from hourly endpoint
- Creates line chart with:
  - X-axis: Hours
  - Y-axis: Average fare ($)
  - Yellow line with fill
  - Smooth curve (tension: 0.4)

**loadZonesChart(borough, timeOfDay, hour)**:
- Builds URL with filter params
- Fetches /api/insights/top-zones
- Creates horizontal bar chart with:
  - Y-axis: Zone names
  - X-axis: Trip count
  - Green bars
  - Top 15 zones only

**loadBoroughChart(borough, timeOfDay, hour)**:
- Builds URL with filter params
- Fetches /api/insights/borough-summary
- Creates vertical bar chart with:
  - X-axis: Borough names
  - Y-axis: Total trips
  - 5 different colors (one per borough)

**applyFilters()**:
- Gets values from 3 dropdowns
- Shows alert with loading message
- Calls all chart load functions with filters
- Charts reload with filtered data

**resetFilters()**:
- Sets all dropdowns to empty string
- Reloads all charts without filters
- Returns to default view

**Error Handling**:
- All fetch calls have .catch() blocks
- Logs errors to console
- Prevents app crash on API failure

---

### 9. frontend/style.css

**Purpose**: Visual styling and layout.

**Global Styles**:
- Resets margin, padding, box-sizing
- Sets default font: Segoe UI
- Green gradient background (#10b981 to #059669)
- Min-height: 100vh (full viewport)

**Header**:
- White background with transparency
- Centered text
- Green title color
- Box shadow for depth

**Filters Section**:
- White background
- Flexbox layout (wraps on small screens)
- Centered items
- Border radius for rounded corners
- Box shadow

**Filter Groups**:
- Vertical flex layout
- Label above select
- Select boxes with:
  - Padding for comfort
  - Border that changes on focus
  - Transition animation
  - Min-width for consistency

**Buttons**:
- Green background (#10b981)
- White text
- Rounded corners
- Hover effect (darker green)
- Reset button: Yellow (#eab308)
- Cursor pointer

**Summary Stats**:
- Flexbox row layout
- 4 equal-width cards
- White background
- Hover effect (lifts up 5px)
- Green numbers
- Gray labels

**Dashboard Container**:
- Max-width: 1400px
- Centered with auto margins
- Grid layout with gap

**Map Section**:
- White background
- Rounded corners
- Map height: 500px
- Insight box with green left border

**Charts Section**:
- Grid layout (2 columns on large screens)
- Auto-fit for responsiveness
- Min-width: 500px per chart

**Chart Containers**:
- White background
- Padding and rounded corners
- Green titles
- Max-height: 300px for canvas
- Insight box below each chart

**Insight Boxes**:
- Light gray background
- Green left border (4px)
- Padding for readability
- Smaller font size

**Footer**:
- White background
- Centered text
- Gray color
- Margin-top for spacing

**Media Queries**:
- @media (max-width: 768px):
  - Charts stack vertically (1 column)
  - Filters stack vertically
  - Smaller header font

**Responsive Design**:
- Flexbox and Grid for layout
- Wrapping for small screens
- Min-widths prevent squishing
- Mobile-friendly controls

---

## DOCUMENTATION FILES

### 10. docs/TECHNICAL_REPORT.md

**Purpose**: Comprehensive technical documentation for grading.

**Section 1: Problem Framing**
- Dataset overview (7.4M records)
- Actual cleaning statistics from cleaning_log.txt
- 4 data challenges identified
- Assumptions documented
- Unexpected observation about speed

**Section 2: System Architecture**
- ASCII diagram showing data flow
- Technology stack justification
- 3 key trade-offs explained:
  - Sampling for performance
  - Server-side vs client-side filtering
  - Normalized vs denormalized schema

**Section 3: Algorithm**
- Pseudo-code for min-heap
- Time complexity: O(n log k)
- Space complexity: O(k)
- Comparison with SQL ORDER BY
- Explanation of why it's better

**Section 4: Three Insights**
- Insight 1: Evening rush hour dominance
  - SQL query shown
  - Finding: 6-7 PM peak
  - Interpretation: Office departure patterns
  
- Insight 2: Late night premium
  - SQL query shown
  - Finding: 50-67% higher fares 2-5 AM
  - Interpretation: Longer distances, less transit
  
- Insight 3: Manhattan concentration
  - SQL query shown
  - Finding: 90%+ of trips
  - Interpretation: Short frequent rides

**Section 5: Reflection**
- Technical challenges (performance, memory, spatial data)
- Team challenges (coordination, timeline)
- Future improvements (PostgreSQL, Redis, ML, Kafka)
- Production considerations (monitoring, scaling)

**Purpose for Grading**:
- Demonstrates design thinking
- Shows engineering decisions
- Proves algorithmic understanding
- Provides meaningful insights
- Reflects on learning

---

### 11. docs/CODE_EXPLANATION.md (This File)

**Purpose**: Detailed code walkthrough for understanding implementation.

**Covers**:
- Every backend file with line-by-line explanation
- Every frontend file with component breakdown
- Documentation files with section summaries
- Why each design decision was made
- How components interact

**Use Cases**:
- Code review
- Onboarding new developers
- Understanding data flow
- Debugging issues
- Learning from implementation

---

## DATA FLOW SUMMARY

**1. Data Acquisition**:
- User downloads yellow_tripdata.parquet from NYC TLC
- User downloads taxi_zone_lookup.csv
- User downloads taxi_zones.zip (shapefiles)

**2. Data Processing**:
- convert_zones.py: Shapefile → GeoJSON
- clean_data.py: Raw data → Cleaned data (7 steps + 5 features)
- insert_db.py: Cleaned data → SQLite database

**3. Backend API**:
- app.py serves 7 REST endpoints
- Queries SQLite database
- Returns JSON responses
- Uses custom algorithm for top-zones

**4. Frontend Display**:
- index.html structures the page
- app.js fetches data from API
- Chart.js renders 4 charts
- Leaflet.js renders map
- style.css makes it beautiful

**5. User Interaction**:
- User selects filters
- JavaScript calls API with params
- Backend queries filtered data
- Frontend updates all visualizations
- User sees insights

---

## KEY DESIGN PATTERNS

**1. Separation of Concerns**:
- Backend: Data processing and API
- Frontend: Visualization and interaction
- Database: Data storage
- Each layer independent

**2. RESTful API**:
- Stateless endpoints
- Standard HTTP methods
- JSON responses
- Clear URL structure

**3. Responsive Design**:
- Mobile-first CSS
- Flexbox and Grid layouts
- Media queries for breakpoints
- Touch-friendly controls

**4. Performance Optimization**:
- Database indexes
- Query sampling (10%)
- Chunked data insertion
- Efficient algorithms (O(n log k))

**5. Error Handling**:
- Try-catch blocks
- Console logging
- Graceful degradation
- User-friendly messages

---

## TESTING CHECKLIST

**Backend**:
- [ ] All 7 API endpoints return data
- [ ] Filters work correctly
- [ ] Database queries are fast (<5s)
- [ ] Custom algorithm returns top 15 zones
- [ ] No SQL errors in console

**Frontend**:
- [ ] All 4 charts display
- [ ] Map loads with colored zones
- [ ] Filters update all visualizations
- [ ] Reset button works
- [ ] Summary stats show correct values
- [ ] No JavaScript errors in console

**Data**:
- [ ] Cleaning log shows all 7 steps
- [ ] Database has 7.4M records
- [ ] GeoJSON has 263 zones
- [ ] All derived features present

**Documentation**:
- [ ] README has setup instructions
- [ ] Technical report has 5 sections
- [ ] Code has comments
- [ ] Video link in README

---

## TROUBLESHOOTING GUIDE

**Problem**: Charts not loading
**Solution**: Check backend is running on port 5000

**Problem**: Map not displaying
**Solution**: Verify taxi_zones.geojson exists

**Problem**: Database errors
**Solution**: Re-run insert_db.py

**Problem**: Slow queries
**Solution**: Check indexes exist, use sampling

**Problem**: Memory errors
**Solution**: Reduce chunk size in insert_db.py

**Problem**: CORS errors
**Solution**: Ensure flask-cors installed

---

## DEPLOYMENT NOTES

**For Production**:
1. Use PostgreSQL instead of SQLite
2. Add Redis for caching
3. Use Gunicorn for Flask
4. Add authentication
5. Use CDN for static files
6. Add monitoring (Sentry, DataDog)
7. Set up CI/CD pipeline
8. Use environment variables for config
9. Add rate limiting
10. Enable HTTPS

**For Academic Submission**:
1. Ensure all files committed to Git
2. Large files excluded via .gitignore
3. README has data download links
4. Video uploaded and linked
5. Technical report complete
6. Code has comments
7. Project runs on fresh clone

---

END OF CODE EXPLANATION
