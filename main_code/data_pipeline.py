#Step 1: Generate Fake Climate Data (ERA5-like precipitation)
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
import os

def generate_fake_precipitation_data():
    """Generate realistic fake precipitation data for Bangalore region"""
    # Bangalore coordinates
    north, south = 13.2, 12.8
    east, west = 77.8, 77.3
    
    # Create coordinate arrays
    lat = np.linspace(south, north, 50)
    lon = np.linspace(west, east, 50)
    
    # Create time array (3 days, hourly data)
    start_date = datetime(2023, 7, 1)
    times = [start_date + timedelta(hours=h) for h in range(72)]
    
    # Generate realistic precipitation patterns
    np.random.seed(42)  # For reproducible results
    
    # Create base precipitation with spatial patterns
    precipitation = np.zeros((len(times), len(lat), len(lon)))
    
    for t in range(len(times)):
        # Simulate weather patterns with some spatial correlation
        base_rain = np.random.exponential(0.5, (len(lat), len(lon)))
        
        # Add monsoon-like patterns (higher rain in certain areas)
        center_lat_idx = len(lat) // 2
        center_lon_idx = len(lon) // 2
        
        for i in range(len(lat)):
            for j in range(len(lon)):
                # Distance from city center (higher rain probability)
                dist = np.sqrt((i - center_lat_idx)**2 + (j - center_lon_idx)**2)
                rain_factor = 1 + 0.5 * np.exp(-dist/10)
                
                # Time-based intensity (simulate storm periods)
                time_factor = 1 + 2 * np.sin(t * np.pi / 24) if t % 24 > 12 else 0.3
                
                precipitation[t, i, j] = base_rain[i, j] * rain_factor * time_factor
                
                # Simulate extreme rainfall events
                if np.random.random() < 0.1:  # 10% chance of heavy rain
                    precipitation[t, i, j] *= 5
    
    # Convert to mm/hour (typical ERA5 units are m/hour)
    precipitation = precipitation / 1000  # Convert to meters for ERA5 format
    
    # Create xarray Dataset
    ds = xr.Dataset(
        {
            'tp': (['valid_time', 'latitude', 'longitude'], precipitation)
        },
        coords={
            'valid_time': times,
            'latitude': lat,
            'longitude': lon
        },
        attrs={
            'title': 'Fake ERA5-like precipitation data for Bangalore',
            'source': 'Generated for flood response system demo'
        }
    )
    
    return ds

# Generate and save fake precipitation data
print("Generating fake precipitation data...")
fake_ds = generate_fake_precipitation_data()
fake_ds.to_netcdf("era5_flood.nc")
print("✅ Fake precipitation data saved as 'era5_flood.nc'")


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

#Step 3: Generate Fake Terrain and OSM Data
import rasterio
from rasterio.transform import from_bounds
from rasterio.enums import Resampling
import geopandas as gpd
from shapely.geometry import Polygon, Point
import pandas as pd

def generate_fake_terrain_data():
    """Generate fake DEM data for Bangalore region"""
    # Bangalore coordinates
    north, south = 13.2, 12.8
    east, west = 77.8, 77.3
    
    # Create elevation data (Bangalore is on Deccan plateau, ~900m elevation)
    height, width = 100, 100
    
    # Generate realistic elevation with some terrain features
    np.random.seed(42)
    rng = np.random.default_rng(42)
    
    # Base elevation around 900m
    base_elevation = 900
    
    # Create elevation grid with realistic terrain
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    X, Y = np.meshgrid(x, y)
    
    # Add terrain features
    elevation_data = base_elevation + 50 * np.sin(2 * np.pi * X) * np.cos(2 * np.pi * Y)
    elevation_data += rng.normal(0, 10, (height, width))  # Add noise
    
    # Add some hills and valleys
    for _ in range(5):
        hill_x = rng.uniform(0, 1)
        hill_y = rng.uniform(0, 1)
        hill_strength = rng.uniform(20, 80)
        hill_radius = rng.uniform(0.1, 0.3)
        
        hill_mask = ((X - hill_x)**2 + (Y - hill_y)**2) < hill_radius**2
        elevation_data += hill_mask * hill_strength
    
    # Define geospatial properties
    transform = from_bounds(west, south, east, north, width, height)
    
    # Save as GeoTIFF
    with rasterio.open(
        "dem.tif",
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=elevation_data.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(elevation_data, 1)
    
    print("✅ Fake DEM file generated and saved as dem.tif")
    return elevation_data

def generate_fake_osm_data():
    """Generate fake buildings and roads data for Bangalore"""
    # Bangalore coordinates
    north, south = 13.2, 12.8
    east, west = 77.8, 77.3
    
    np.random.seed(42)
    rng = np.random.default_rng(42)
    
    # Generate fake buildings
    buildings_list = []
    for i in range(200):  # Generate 200 buildings
        # Random location within bounds
        center_lat = rng.uniform(south, north)
        center_lon = rng.uniform(west, east)
        
        # Building size (in degrees, very small)
        width = rng.uniform(0.001, 0.005)
        height = rng.uniform(0.001, 0.005)
        
        # Create rectangular building
        building = Polygon([
            (center_lon - width/2, center_lat - height/2),
            (center_lon + width/2, center_lat - height/2),
            (center_lon + width/2, center_lat + height/2),
            (center_lon - width/2, center_lat + height/2)
        ])
        
        buildings_list.append({
            'geometry': building,
            'building': rng.choice(['residential', 'commercial', 'industrial']),
            'levels': int(rng.uniform(1, 10))
        })
    
    buildings_gdf = gpd.GeoDataFrame(buildings_list, crs='EPSG:4326')
    
    # Generate fake roads (simplified as points along major routes)
    roads_list = []
    for i in range(50):  # Generate 50 road segments
        # Create road as line segments
        start_lat = rng.uniform(south, north)
        start_lon = rng.uniform(west, east)
        end_lat = start_lat + rng.uniform(-0.02, 0.02)
        end_lon = start_lon + rng.uniform(-0.02, 0.02)
        
        road = Point(start_lon, start_lat).buffer(0.001)  # Simple road representation
        
        roads_list.append({
            'geometry': road,
            'highway': rng.choice(['primary', 'secondary', 'residential']),
            'name': f'Road_{i}'
        })
    
    roads_gdf = gpd.GeoDataFrame(roads_list, crs='EPSG:4326')
    
    print("✅ Fake OSM data (buildings and roads) generated")
    return buildings_gdf, roads_gdf

# Generate fake terrain and OSM data
elevation_data = generate_fake_terrain_data()
buildings, roads = generate_fake_osm_data()

#Step 4: Enhanced Flood Risk Assessment
def compute_enhanced_flood_risk():
    """Compute comprehensive flood risk considering multiple factors"""
    
    with rasterio.open("flood_accum.tif") as rain_src, rasterio.open("dem.tif") as dem_src:
        rain_data = rain_src.read(1)
        dem_data = dem_src.read(1, out_shape=rain_data.shape, resampling=Resampling.bilinear)
        transform = rain_src.transform
        crs = rain_src.crs
    
    print("📊 Computing enhanced flood risk factors...")
    
    # 1. Terrain slope analysis
    grad_y, grad_x = np.gradient(dem_data)
    slope = np.sqrt(grad_x**2 + grad_y**2)
    slope_normalized = (slope - np.min(slope)) / (np.max(slope) - np.min(slope))
    
    # 2. Flow accumulation (simplified watershed analysis)
    flow_accumulation = np.zeros_like(dem_data)
    height, width = dem_data.shape
    
    for i in range(1, height-1):
        for j in range(1, width-1):
            # Water flows to lowest neighboring cell
            neighbors = [
                dem_data[i-1:i+2, j-1:j+2].flatten()
            ]
            if dem_data[i, j] <= np.min(neighbors):
                flow_accumulation[i, j] += 1
    
    # 3. Distance to water bodies (simulated)
    np.random.seed(42)
    rng = np.random.default_rng(42)
    
    # Simulate water bodies (lakes, rivers)
    water_bodies = []
    for _ in range(5):
        water_y = int(rng.uniform(10, height-10))
        water_x = int(rng.uniform(10, width-10))
        water_bodies.append((water_y, water_x))
    
    # Distance to nearest water body
    distance_to_water = np.zeros_like(dem_data)
    for i in range(height):
        for j in range(width):
            min_dist = float('inf')
            for wy, wx in water_bodies:
                dist = np.sqrt((i - wy)**2 + (j - wx)**2)
                min_dist = min(min_dist, dist)
            distance_to_water[i, j] = min_dist
    
    # Normalize distance (closer to water = higher risk)
    distance_normalized = 1 - (distance_to_water / np.max(distance_to_water))
    
    # 4. Urban density factor (based on building data)
    urban_density = np.zeros_like(dem_data)
    
    # Convert building polygons to raster
    for idx, building in buildings.iterrows():
        # Get building bounds
        bounds = building.geometry.bounds
        minx, miny, maxx, maxy = bounds
        
        # Convert to pixel coordinates
        from rasterio.transform import rowcol
        row1, col1 = rowcol(transform, minx, maxy)
        row2, col2 = rowcol(transform, maxx, miny)
        
        # Ensure coordinates are within bounds
        row1 = max(0, min(row1, height-1))
        row2 = max(0, min(row2, height-1))
        col1 = max(0, min(col1, width-1))
        col2 = max(0, min(col2, width-1))
        
        if row1 < height and col1 < width:
            urban_density[min(row1, row2):max(row1, row2)+1, 
                        min(col1, col2):max(col1, col2)+1] += 1
    
    urban_density_normalized = urban_density / (np.max(urban_density) + 1)
    
    # 5. Comprehensive flood risk calculation
    # Weights for different factors
    w_rain = 0.4      # Precipitation weight
    w_slope = 0.2     # Terrain slope weight  
    w_flow = 0.15     # Flow accumulation weight
    w_distance = 0.15 # Distance to water weight
    w_urban = 0.1     # Urban density weight
    
    # Normalize rainfall data
    rain_normalized = (rain_data - np.min(rain_data)) / (np.max(rain_data) - np.min(rain_data))
    
    # Calculate composite flood risk
    flood_risk = (w_rain * rain_normalized + 
                 w_slope * (1 - slope_normalized) +  # Lower slope = higher risk
                 w_flow * (flow_accumulation / np.max(flow_accumulation)) +
                 w_distance * distance_normalized +
                 w_urban * urban_density_normalized)
    
    # Apply thresholds for risk categories
    risk_categories = np.zeros_like(flood_risk)
    risk_categories[flood_risk < 0.3] = 1  # Low risk
    risk_categories[(flood_risk >= 0.3) & (flood_risk < 0.6)] = 2  # Medium risk
    risk_categories[(flood_risk >= 0.6) & (flood_risk < 0.8)] = 3  # High risk
    risk_categories[flood_risk >= 0.8] = 4  # Very high risk
    
    # Save results
    np.save("flood_risk.npy", flood_risk)
    np.save("flood_risk_categories.npy", risk_categories)
    
    # Save as GeoTIFF for visualization
    with rasterio.open(
        "flood_risk_map.tif",
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=flood_risk.dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(flood_risk, 1)
    
    print("✅ Enhanced flood risk analysis completed!")
    print(f"   - Risk levels: Low: {np.sum(risk_categories==1)} pixels")
    print(f"                 Medium: {np.sum(risk_categories==2)} pixels") 
    print(f"                 High: {np.sum(risk_categories==3)} pixels")
    print(f"                 Very High: {np.sum(risk_categories==4)} pixels")
    
    return flood_risk, risk_categories

# Compute enhanced flood risk
flood_risk, risk_categories = compute_enhanced_flood_risk()

def assess_building_flood_risk(buildings_gdf, flood_risk_array, transform):
    """Assess flood risk for individual buildings"""
    print("🏢 Assessing flood risk for individual buildings...")
    
    building_risks = []
    
    for idx, building in buildings_gdf.iterrows():
        # Get building centroid
        centroid = building.geometry.centroid
        
        # Convert geographic coordinates to pixel coordinates
        try:
            from rasterio.transform import rowcol
            row, col = rowcol(transform, centroid.x, centroid.y)
            
            # Ensure coordinates are within bounds
            if 0 <= row < flood_risk_array.shape[0] and 0 <= col < flood_risk_array.shape[1]:
                risk_value = flood_risk_array[row, col]
                
                # Categorize risk
                if risk_value < 0.3:
                    risk_level = "Low"
                elif risk_value < 0.6:
                    risk_level = "Medium" 
                elif risk_value < 0.8:
                    risk_level = "High"
                else:
                    risk_level = "Very High"
                
                building_risks.append({
                    'building_id': idx,
                    'building_type': building.get('building', 'unknown'),
                    'levels': building.get('levels', 1),
                    'longitude': centroid.x,
                    'latitude': centroid.y,
                    'flood_risk_score': risk_value,
                    'risk_category': risk_level
                })
            else:
                building_risks.append({
                    'building_id': idx,
                    'building_type': building.get('building', 'unknown'),
                    'levels': building.get('levels', 1),
                    'longitude': centroid.x,
                    'latitude': centroid.y,
                    'flood_risk_score': 0.0,
                    'risk_category': "No Data"
                })
        except Exception as e:
            print(f"Error processing building {idx}: {e}")
            continue
    
    # Create DataFrame with results
    building_risk_df = pd.DataFrame(building_risks)
    building_risk_df.to_csv("building_flood_risk_assessment.csv", index=False)
    
    # Print summary statistics
    if not building_risk_df.empty:
        risk_summary = building_risk_df['risk_category'].value_counts()
        print("🏢 Building Flood Risk Summary:")
        for category, count in risk_summary.items():
            print(f"   - {category}: {count} buildings")
    
    return building_risk_df

# Assess building-specific flood risk
with rasterio.open("flood_risk_map.tif") as src:
    transform = src.transform

building_risk_assessment = assess_building_flood_risk(buildings, flood_risk, transform)

#Step 5: Serve as Cloud-Optimized GeoTIFF (COG)
#Convert to COG for web display:
def create_cog_files():
    """Create Cloud-Optimized GeoTIFF files for web display"""
    print("🌐 Creating Cloud-Optimized GeoTIFF files...")
    
    try:
        from rio_cogeo.cogeo import cog_translate
        from rio_cogeo.profiles import cog_profiles
        
        # Convert flood accumulation to COG
        cog_translate(
            "flood_accum.tif",
            "flood_accum_cog.tif", 
            cog_profiles.get("deflate"),
            in_memory=False
        )
        
        # Convert flood risk map to COG
        cog_translate(
            "flood_risk_map.tif",
            "flood_risk_cog.tif",
            cog_profiles.get("deflate"),
            in_memory=False
        )
        
        print("✅ COG files created successfully!")
        
    except ImportError:
        print("⚠️ rio-cogeo not available, using regular GeoTIFF files")
        import shutil
        shutil.copy("flood_accum.tif", "flood_accum_cog.tif")
        shutil.copy("flood_risk_map.tif", "flood_risk_cog.tif")

create_cog_files()

print("\n🎉 Flood Response System Data Pipeline Complete!")
print("📁 Generated Files:")
print("   - era5_flood.nc (fake precipitation data)")
print("   - dem.tif (fake elevation data)")
print("   - flood_accum.tif (accumulated precipitation)")
print("   - flood_risk_map.tif (comprehensive flood risk)")
print("   - flood_risk.npy (flood risk array)")
print("   - flood_risk_categories.npy (categorized risk)")
print("   - building_flood_risk_assessment.csv (building-level assessment)")
print("   - *_cog.tif (web-optimized versions)")
print("\n🎯 Next: Run serve_api.py to start the web service!")

