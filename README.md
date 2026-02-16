# NYC Urban Mobility Data Explorer

**Video Walkthrough:** [Add your video link here]

A full-stack web application analyzing NYC taxi trip patterns using real-world data from the NYC Taxi & Limousine Commission.

## Features

- **Data Cleaning Pipeline**: 7-step cleaning with transparency logging
- **Feature Engineering**: 5 derived features (duration, speed, fare_per_mile, time_of_day, is_weekend)
- **Custom Algorithm**: Min-heap implementation for top-K zone selection (O(n log k) complexity)
- **Normalized Database**: SQLite with proper indexing and relationships
- **RESTful API**: 7 endpoints for querying trip data
- **Interactive Dashboard**: Real-time filtering with charts and maps
- **Spatial Visualization**: Choropleth map showing trip distribution
- **Technical Documentation**: Comprehensive report with architecture and insights

## Project Structure

```
Urban_Mobility_Data_Explorer/
├── backend/
│   ├── data/
│   │   ├── yellow_tripdata.csv (download separately)
│   │   ├── taxi_zone_lookup.csv
│   │   ├── taxi_zones.shp/dbf/shx/prj
│   │   ├── taxi_zones.geojson (generated)
│   │   ├── cleaned_trips.parquet (generated)
│   │   ├── cleaning_log.txt (generated)
│   │   └── mobility.db (generated)
│   ├── scripts/
│   │   ├── convert_zones.py
│   │   ├── clean_data.py
│   │   └── insert_db.py
│   ├── algorithms.py
│   ├── app.py
│   ├── database.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docs/
│   └── TECHNICAL_REPORT.md
├── .gitignore
├── README.md
└── VIDEO_SCRIPT.md
```

## Prerequisites

- Python 3.8+
- pip package manager
- Modern web browser

## Data Setup

**Large data files are NOT included in this repository.**

### Required Files:

1. **Yellow Taxi Trip Data** (`yellow_tripdata.csv`)
   - Download: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
   - Select January 2024 (or any month from 2023/2024)
   - Place in `backend/data/`
   - File size: ~647MB

2. **Taxi Zone Lookup** (`taxi_zone_lookup.csv`)
   - Download: https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
   - Place in `backend/data/`

3. **Taxi Zones Shapefile** (`.shp`, `.dbf`, `.shx`, `.prj`)
   - Download: https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip
   - Extract all files to `backend/data/`

### Quick Download:

```bash
# Download zone lookup
curl -o backend/data/taxi_zone_lookup.csv https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv

# Download and extract shapefiles
curl -o taxi_zones.zip https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip
unzip taxi_zones.zip -d backend/data/
```

Manually download the trip data CSV file from NYC TLC website and place it in `backend/data/`.

## Installation & Setup

### 1. Install Dependencies

```bash
cd Urban_Mobility_Data_Explorer
pip install flask flask-cors pandas geopandas pyarrow
```

### 2. Convert Shapefile to GeoJSON

```bash
python backend/scripts/convert_zones.py
```

Generates `backend/data/taxi_zones.geojson`

### 3. Clean the Data

```bash
python backend/scripts/clean_data.py
```

Generates:
- `backend/data/cleaned_trips.parquet`
- `backend/data/cleaning_log.txt`

### 4. Create Database

```bash
python backend/scripts/insert_db.py
```

Generates `backend/data/mobility.db` (~10-15 minutes)

### 5. Start Backend API

```bash
cd backend
python app.py
```

Server runs on http://localhost:5000

### 6. Open Frontend

```bash
cd frontend
python -m http.server 8000
```

Navigate to http://localhost:8000

## API Endpoints

- `GET /api/zones` - Get all taxi zones
- `GET /api/trips` - Get filtered trip records (params: borough, hour, time_of_day, limit)
- `GET /api/insights/hourly` - Trip counts and average fare by hour
- `GET /api/insights/top-zones` - Top 15 pickup zones
- `GET /api/insights/borough-summary` - Aggregate statistics by borough
- `GET /api/geojson` - GeoJSON with trip counts for map visualization
- `GET /api/stats/summary` - Overall summary statistics

## Data Cleaning Pipeline

7-step pipeline:
1. Remove duplicates
2. Drop missing critical fields (location, datetime, fare, distance)
3. Remove impossible timestamps (dropoff before pickup)
4. Remove outliers (distance, fare, passenger count)
5. Validate location IDs against zone lookup
6. Remove unrealistic trip durations (<1 min or >3 hours)
7. Remove impossible speeds (>80 mph)

**Derived Features:**
- `trip_duration_minutes` - Reveals congestion patterns
- `speed_mph` - Shows traffic behavior by time
- `fare_per_mile` - Reveals economic patterns
- `time_of_day` - Categorizes trips (Morning/Afternoon/Evening/Night)
- `is_weekend` - Boolean flag for weekend trips

## Database Design

**Normalized Schema:**
- `zones` table: Dimension table with location metadata
- `trips` table: Fact table with foreign keys to zones

**Indexes:**
- `pickup_datetime` - For time-based queries
- `pu_location_id` - For pickup location filtering
- `do_location_id` - For dropoff location filtering
- `time_of_day` - For time period filtering

## Technology Stack

**Backend:**
- Python 3.8+
- Flask (API server)
- Pandas (data processing)
- GeoPandas (spatial data)
- SQLite (database)
- Custom MinHeap algorithm (no built-in sorting)

**Frontend:**
- HTML5/CSS3
- Vanilla JavaScript
- Chart.js (visualizations)
- Leaflet.js (maps)

## Documentation

See [docs/TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md) for:
- Problem framing and dataset analysis
- System architecture diagram
- Algorithm implementation and complexity analysis
- Three key insights with interpretations
- Reflection and future improvements

## Troubleshooting

**ModuleNotFoundError**
```bash
pip install flask flask-cors pandas geopandas pyarrow
```

**Database not found**
```bash
python backend/scripts/insert_db.py
```

**CORS errors**
- Ensure flask-cors is installed
- Backend must be running on port 5000

**Map not loading**
- Check that `taxi_zones.geojson` exists in `backend/data/`

**Charts not displaying**
- Verify backend API is running: http://localhost:5000/api/stats/summary

## Pushing to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git push -u origin main
```

The `.gitignore` file excludes large data files automatically.

## Data Source

NYC Taxi & Limousine Commission (TLC)  
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

## License

Educational project for academic purposes.