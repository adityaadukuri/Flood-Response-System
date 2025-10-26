"""
#Step 1: Get Open Climate Data
#We'll use ERA5 precipitation

import cdsapi

# Initialize the CDS API client
c = cdsapi.Client()

# Download ERA5 reanalysis data
# This example downloads temperature data for a specific region and time period
c.retrieve(
    'reanalysis-era5-single-levels',  # ERA5 dataset
    {
        'product_type': 'reanalysis',
        'variable': 'total_precipitation',   # 🌧️ rainfall
        'year': '2023',
        'month': ['07'],                     # Example: July 2023
        'day': ['01', '02', '03'],           # Few days sample
        'time': [f"{h:02d}:00" for h in range(24)],  # Hourly data
        'area': [13.2, 77.3, 12.8, 77.8],    # [North, West, South, East]
        'format': 'netcdf',                  # NetCDF file format
    },
    'era5_flood.nc'                          # Output file for rainfall
)

print("Download complete! Data saved as 'era5_flood.nc'")


#Step 2: Load and Process Data with xarray
import xarray as xr
import rioxarray

ds = xr.open_dataset("era5_flood.nc")
rain = ds["tp"] * 1000  # Convert m to mm

# Accumulate precipitation over 3 days
rain_accum = rain.sum(dim="valid_time")

# Reproject for GeoTIFF export
rain_accum = rain_accum.rio.write_crs("EPSG:4326")
rain_accum.rio.to_raster("flood_accum.tif")

#Step 3: Overlay with Terrain and OSM Data
#Get terrain (DEM):
import elevation

# Clip a DEM for your region (Bangalore example)
elevation.clip(
    bounds=(77.3, 12.8, 77.8, 13.2),  # west, south, east, north
    output="dem.tif"
)

print("✅ DEM file downloaded and saved as dem.tif")


#Get roads and buildings (OSMnx):
import osmnx as ox
north, south, east, west = 13.2, 12.8, 77.8, 77.3
buildings = ox.features_from_bbox(north, south, east, west, tags={"building": True})
roads = ox.features_from_bbox(north, south, east, west, tags={"highway": True})

#Step 4: Compute Flood-Prone Zones
#Combine precipitation and terrain slope to estimate where water accumulates.
import rasterio
from rasterio.enums import Resampling
import numpy as np

with rasterio.open("flood_accum.tif") as rain_src, rasterio.open("dem.tif") as dem_src:
    rain_data = rain_src.read(1)
    dem_data = dem_src.read(1, out_shape=rain_data.shape, resampling=Resampling.bilinear)

# Compute slope (simplified)
slope = np.gradient(dem_data)[0] ** 2 + np.gradient(dem_data)[1] ** 2
slope = np.sqrt(slope)

# Flood index = rainfall / slope
flood_risk = rain_data / (slope + 0.1)
np.save("flood_risk.npy", flood_risk)

#Step 5: Serve as Cloud-Optimized GeoTIFF (COG)
#Convert to COG for web display:
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

cog_translate(
    "flood_accum.tif",
    "flood_accum_cog.tif",
    cog_profiles.get("deflate"),
    in_memory=False
)

