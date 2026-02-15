"""Shapefile to GeoJSON Conversion Script

Converts taxi_zones.shp to web-compatible GeoJSON format.
Reprojects to EPSG:4326 (WGS84) for Leaflet.js compatibility.
"""

import geopandas as gpd
import os

# Get the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
data_dir = os.path.join(project_root, "backend", "data")

shp_path = os.path.join(data_dir, "taxi_zones.shp")
geojson_path = os.path.join(data_dir, "taxi_zones.geojson")

# Read shapefile and convert to GeoJSON
gdf = gpd.read_file(shp_path)
gdf = gdf.to_crs(epsg=4326)  # Reproject to WGS84 for web maps
gdf.to_file(geojson_path, driver="GeoJSON")

print(f"Done! {len(gdf)} zones converted")
print(gdf[["LocationID", "zone", "borough"]].head())
