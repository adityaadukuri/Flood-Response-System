#Flood Progression Simulation Model for Bangalore
#This module simulates how flood conditions evolve over time

import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import json
import os
import warnings
warnings.filterwarnings('ignore')

class FloodSimulation:
    """Advanced flood progression simulation for Bangalore"""
    
    def __init__(self, start_date=None, simulation_days=7):
        """Initialize flood simulation
        
        Args:
            start_date: Starting date for simulation (default: today)
            simulation_days: Number of days to simulate (default: 7)
        """
        self.start_date = start_date or datetime.now()
        self.simulation_days = simulation_days
        self.timesteps = simulation_days * 24  # Hourly timesteps
        
        # Bangalore region boundaries
        self.region = {
            'north': 13.2, 'south': 12.8,
            'east': 77.8, 'west': 77.3
        }
        
        # Grid resolution
        self.grid_size = 100
        self.lat = np.linspace(self.region['south'], self.region['north'], self.grid_size)
        self.lon = np.linspace(self.region['west'], self.region['east'], self.grid_size)
        
        # Initialize simulation data
        self.precipitation_forecast = None
        self.water_depth = None
        self.flood_extent = None
        self.simulation_results = {}
        
        print(f"🌊 Flood Simulation initialized for {simulation_days} days starting {self.start_date.strftime('%Y-%m-%d')}")
    
    def generate_weather_forecast(self):
        """Generate realistic weather forecast with monsoon patterns"""
        print("🌦️  Generating weather forecast...")
        
        # Create time series
        times = [self.start_date + timedelta(hours=h) for h in range(self.timesteps)]
        
        # Initialize precipitation array
        precipitation = np.zeros((self.timesteps, self.grid_size, self.grid_size))
        
        # Set random seed for reproducible results
        np.random.seed(int(self.start_date.timestamp()) % 1000)
        rng = np.random.default_rng(42)
        
        # Simulate different weather scenarios
        weather_scenarios = [
            {'name': 'Light Rain', 'intensity': 2.0, 'probability': 0.3, 'duration': 6},
            {'name': 'Moderate Rain', 'intensity': 8.0, 'probability': 0.4, 'duration': 12},
            {'name': 'Heavy Rain', 'intensity': 25.0, 'probability': 0.2, 'duration': 8},
            {'name': 'Very Heavy Rain', 'intensity': 50.0, 'probability': 0.08, 'duration': 4},
            {'name': 'Extreme Rain', 'intensity': 100.0, 'probability': 0.02, 'duration': 2}
        ]
        
        for t in range(self.timesteps):
            current_time = times[t]
            
            # Monsoon seasonality (higher rain probability June-September)
            month = current_time.month
            monsoon_factor = 1.0
            if 6 <= month <= 9:  # Monsoon season
                monsoon_factor = 2.5
            elif month in [5, 10]:  # Pre/post monsoon
                monsoon_factor = 1.5
            
            # Diurnal cycle (more rain in afternoon/evening)
            hour = current_time.hour
            diurnal_factor = 1.0
            if 14 <= hour <= 20:  # Afternoon thunderstorms
                diurnal_factor = 1.8
            elif 2 <= hour <= 6:   # Early morning drizzle
                diurnal_factor = 1.2
            
            # Generate multiple weather systems for strong spatial variation
            num_systems = rng.integers(2, 5)  # 2-4 weather systems per timestep for more variation
            
            for system in range(num_systems):
                # Generate weather event for this system
                event_probability = rng.random() * monsoon_factor * diurnal_factor
                
                for scenario in weather_scenarios:
                    if event_probability < scenario['probability']:
                        # Generate spatial rainfall pattern with enhanced variation
                        base_intensity = scenario['intensity']
                        
                        # Create realistic spatial distribution with multiple centers
                        center_i = rng.integers(5, self.grid_size - 5)
                        center_j = rng.integers(5, self.grid_size - 5)
                        
                        # Storm system characteristics with more variation
                        storm_radius = rng.uniform(15, 40)  # Larger storms
                        storm_intensity_variation = rng.uniform(0.2, 2.0)  # Wider intensity range
                        
                        # Create spatial patterns using multiple techniques
                        for i in range(self.grid_size):
                            for j in range(self.grid_size):
                                # Distance from storm center
                                distance = np.sqrt((i - center_i)**2 + (j - center_j)**2)
                                
                                # Create strong precipitation patterns
                                if distance < storm_radius:
                                    # Intensity decreases with distance (more gradual)
                                    intensity_factor = np.exp(-distance / (storm_radius / 2))
                                    
                                    # Enhanced terrain influence with multiple factors
                                    elevation_factor = 1.0 + 0.8 * np.sin(i * 2 * np.pi / self.grid_size) * np.cos(j * 2 * np.pi / self.grid_size)
                                    orographic_factor = 1.0 + 0.6 * np.sin(i * np.pi / 30) * np.cos(j * np.pi / 25)
                                    
                                    # Strong spatial noise for realistic variation  
                                    spatial_noise = rng.uniform(0.1, 2.5)  # Much wider range
                                    
                                    # Add wind direction effects
                                    wind_direction = rng.uniform(0, 2 * np.pi)
                                    wind_effect = 1.0 + 0.4 * np.cos(wind_direction + np.arctan2(j - center_j, i - center_i))
                                    
                                    # Combine all factors for strong spatial variation
                                    local_intensity = (base_intensity * intensity_factor * 
                                                     storm_intensity_variation * elevation_factor * 
                                                     orographic_factor * spatial_noise * wind_effect)
                                    
                                    # Add to existing precipitation (allows overlap)
                                    precipitation[t, i, j] += max(0, local_intensity)
                                
                                # Add background precipitation with spatial variation
                                elif rng.random() < 0.1:  # 10% chance of light background rain
                                    background_intensity = base_intensity * 0.1 * rng.uniform(0.1, 0.8)
                                    precipitation[t, i, j] += background_intensity
                        
                        break
        
        # Create xarray dataset
        self.precipitation_forecast = xr.Dataset(
            {
                'precipitation': (['time', 'latitude', 'longitude'], precipitation)
            },
            coords={
                'time': times,
                'latitude': self.lat,
                'longitude': self.lon
            },
            attrs={
                'title': 'Flood Simulation Weather Forecast',
                'description': f'{self.simulation_days}-day precipitation forecast for Bangalore',
                'units': 'mm/hour'
            }
        )
        
        print(f"✅ Weather forecast generated with {len(times)} hourly timesteps")
        return self.precipitation_forecast
    
    def simulate_hydrological_response(self):
        """Simulate flood progression using hydrological models"""
        print("💧 Simulating hydrological response...")
        
        if self.precipitation_forecast is None:
            raise ValueError("Weather forecast must be generated first")
        
        # Load terrain data
        try:
            import rasterio
            with rasterio.open('dem.tif') as src:
                elevation = src.read(1)
                # Resize to match grid
                from scipy import ndimage
                elevation = ndimage.zoom(elevation, 
                                       (self.grid_size / elevation.shape[0], 
                                        self.grid_size / elevation.shape[1]))
        except:
            # Generate synthetic elevation if file not available
            print("⚠️  DEM file not found, using synthetic elevation")
            x = np.linspace(0, 1, self.grid_size)
            y = np.linspace(0, 1, self.grid_size)
            X, Y = np.meshgrid(x, y)
            elevation = 900 + 50 * np.sin(2 * np.pi * X) * np.cos(2 * np.pi * Y)
        
        # Initialize water depth array
        water_depth = np.zeros((self.timesteps, self.grid_size, self.grid_size))
        flood_extent = np.zeros((self.timesteps, self.grid_size, self.grid_size))
        
        # Create spatially variable hydrological parameters for enhanced variation
        rng = np.random.default_rng(42)
        
        # Spatially variable infiltration (soil types)
        base_infiltration = 5.0
        infiltration_spatial = base_infiltration * (0.5 + rng.uniform(0, 1.5, (self.grid_size, self.grid_size)))
        
        # Spatially variable runoff coefficient (land use patterns)
        base_runoff = 0.7
        runoff_spatial = base_runoff * (0.3 + rng.uniform(0, 1.4, (self.grid_size, self.grid_size)))
        
        # Urban areas with higher runoff (create patches)
        for _ in range(10):  # Create 10 urban patches
            center_i = rng.integers(10, self.grid_size - 10)
            center_j = rng.integers(10, self.grid_size - 10)
            urban_radius = rng.integers(8, 15)
            
            for i in range(max(0, center_i - urban_radius), min(self.grid_size, center_i + urban_radius)):
                for j in range(max(0, center_j - urban_radius), min(self.grid_size, center_j + urban_radius)):
                    distance = np.sqrt((i - center_i)**2 + (j - center_j)**2)
                    if distance < urban_radius:
                        # Urban areas: low infiltration, high runoff
                        infiltration_spatial[i, j] *= 0.2
                        runoff_spatial[i, j] = min(0.95, runoff_spatial[i, j] * 1.8)
        
        evaporation_rate = 2.0  # mm/hour during day
        
        # Simulate each timestep
        for t in range(self.timesteps):
            current_time = self.precipitation_forecast.time[t].values
            current_precip = self.precipitation_forecast.precipitation[t].values
            
            # Previous water depth (or initialize to zero)
            if t == 0:
                prev_water = np.zeros_like(current_precip)
            else:
                prev_water = water_depth[t-1]
            
            # Calculate spatially variable infiltration (reduced when soil is saturated)
            soil_saturation = np.minimum(prev_water / 50.0, 1.0)  # Assume 50mm saturation
            actual_infiltration = infiltration_spatial * (1 - soil_saturation * 0.8)
            
            # Calculate evaporation (higher during day)
            hour = pd.to_datetime(current_time).hour
            if 6 <= hour <= 18:
                actual_evaporation = evaporation_rate
            else:
                actual_evaporation = evaporation_rate * 0.3
            
            # Water balance calculation with spatially variable runoff
            net_input = current_precip * runoff_spatial
            water_loss = np.minimum(actual_infiltration + actual_evaporation, prev_water + net_input)
            
            # Update water depth with realistic accumulation
            new_water = prev_water + net_input - water_loss
            new_water = np.maximum(new_water, 0)  # No negative water depth
            
            # Apply minimum threshold for water retention (spatially variable)
            retention_threshold = 0.5 + 0.5 * infiltration_spatial / base_infiltration  # Higher retention in permeable soils
            new_water = np.where(new_water < retention_threshold, 0, new_water)
            
            # Enhanced surface flow simulation for better spatial variation
            if t > 0:
                # Calculate slope-based flow with enhanced spatial effects
                _, _ = np.gradient(elevation + new_water)
                
                # Create depression areas that accumulate water
                depression_factor = rng.uniform(0.8, 1.2, (self.grid_size, self.grid_size))
                new_water *= depression_factor
                
                # Enhanced flow redistribution with spatial variation
                flow_factor = 0.15 + 0.1 * (runoff_spatial / base_runoff)  # Variable flow based on surface type
                
                # Create temporary array for flow calculations
                water_change = np.zeros_like(new_water)
                
                for i in range(1, self.grid_size - 1):
                    for j in range(1, self.grid_size - 1):
                        if new_water[i, j] > 3:  # Lower threshold for more flow
                            # Flow to neighboring cells based on elevation + water surface
                            neighbors = [
                                (i-1, j), (i+1, j), (i, j-1), (i, j+1),
                                (i-1, j-1), (i-1, j+1), (i+1, j-1), (i+1, j+1)  # Include diagonal flow
                            ]
                            
                            current_level = elevation[i, j] + new_water[i, j]
                            
                            for ni, nj in neighbors:
                                neighbor_level = elevation[ni, nj] + new_water[ni, nj]
                                
                                if current_level > neighbor_level:
                                    level_diff = current_level - neighbor_level
                                    flow_amount = min(
                                        new_water[i, j] * flow_factor[i, j] * 0.4,
                                        level_diff * 0.3
                                    )
                                    
                                    # Accumulate flow changes
                                    water_change[i, j] -= flow_amount
                                    water_change[ni, nj] += flow_amount * 0.8  # Some loss during flow
                
                # Apply flow changes
                new_water += water_change
                new_water = np.maximum(new_water, 0)  # No negative water
            
            water_depth[t] = new_water
            
            # Determine flood extent with multiple levels for better visualization
            flood_extent[t] = np.where(new_water > 20, 3,        # Severe flooding
                                      np.where(new_water > 10, 2,  # Moderate flooding  
                                              np.where(new_water > 5, 1, 0)))  # Light flooding
            
            if t % 24 == 0:  # Print progress daily
                day = t // 24 + 1
                max_depth = np.max(new_water)
                flooded_area = np.sum(flood_extent[t]) / (self.grid_size**2) * 100
                print(f"   Day {day}: Max water depth = {max_depth:.1f}mm, Flooded area = {flooded_area:.1f}%")
        
        self.water_depth = water_depth
        self.flood_extent = flood_extent
        
        print("✅ Hydrological simulation completed")
        return water_depth, flood_extent
    
    def analyze_flood_progression(self):
        """Analyze flood progression patterns and generate statistics"""
        print("📊 Analyzing flood progression...")
        
        if self.water_depth is None:
            raise ValueError("Hydrological simulation must be run first")
        
        # Calculate daily statistics
        daily_stats = []
        
        for day in range(self.simulation_days):
            day_start = day * 24
            day_end = (day + 1) * 24
            
            # Get daily data
            daily_water = self.water_depth[day_start:day_end]
            daily_flood = self.flood_extent[day_start:day_end]
            daily_precip = self.precipitation_forecast.precipitation[day_start:day_end]
            
            # Calculate statistics - convert DataArrays to numpy arrays first
            max_water_depth = float(np.max(daily_water))
            avg_water_depth = float(np.mean(daily_water[daily_water > 0]))
            flooded_area_km2 = float(np.sum(np.max(daily_flood, axis=0)) * (0.4 / self.grid_size)**2)  # Approximate area
            total_precipitation = float(np.sum(daily_precip.values if hasattr(daily_precip, 'values') else daily_precip))
            peak_intensity = float(np.max(daily_precip.values if hasattr(daily_precip, 'values') else daily_precip))
            
            # Risk assessment
            if max_water_depth < 50:
                risk_level = "Low"
            elif max_water_depth < 200:
                risk_level = "Moderate"
            elif max_water_depth < 500:
                risk_level = "High"
            else:
                risk_level = "Extreme"
            
            daily_stats.append({
                'day': day + 1,
                'date': (self.start_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                'max_water_depth_mm': round(max_water_depth, 1),
                'avg_water_depth_mm': round(avg_water_depth if not np.isnan(avg_water_depth) else 0, 1),
                'flooded_area_km2': round(flooded_area_km2, 2),
                'total_precipitation_mm': round(total_precipitation, 1),
                'peak_intensity_mm_h': round(peak_intensity, 1),
                'risk_level': risk_level
            })
        
        # Overall simulation summary
        max_overall_depth = np.max(self.water_depth)
        max_flooded_area = np.max([stat['flooded_area_km2'] for stat in daily_stats])
        total_rain = sum([stat['total_precipitation_mm'] for stat in daily_stats])
        
        simulation_summary = {
            'simulation_period': f"{self.start_date.strftime('%Y-%m-%d')} to {(self.start_date + timedelta(days=self.simulation_days)).strftime('%Y-%m-%d')}",
            'total_simulation_hours': self.timesteps,
            'max_water_depth_mm': round(max_overall_depth, 1),
            'max_flooded_area_km2': round(max_flooded_area, 2),
            'total_precipitation_mm': round(total_rain, 1),
            'grid_resolution': f"{self.grid_size}x{self.grid_size}",
            'daily_statistics': daily_stats
        }
        
        self.simulation_results = simulation_summary
        
        # Save results
        with open('flood_simulation_results.json', 'w') as f:
            json.dump(simulation_summary, f, indent=2)
        
        print("✅ Flood progression analysis completed")
        print(f"   📈 Peak water depth: {max_overall_depth:.1f}mm")
        print(f"   🗺️  Max flooded area: {max_flooded_area:.2f} km²")
        print(f"   🌧️  Total rainfall: {total_rain:.1f}mm")
        
        return simulation_summary
    
    def create_progression_visualization(self):
        """Create animated visualization of flood progression"""
        print("🎬 Creating flood progression animation...")
        
        if self.water_depth is None:
            raise ValueError("Simulation must be run first")
        
        # Create figure and subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Bangalore Flood Simulation - Progression Analysis', fontsize=16, fontweight='bold')
        
        # Custom colormap for flood depths
        colors = ['white', 'lightblue', 'blue', 'darkblue', 'purple']
        n_bins = 100
        flood_cmap = LinearSegmentedColormap.from_list('flood', colors, N=n_bins)
        
        # 1. Current flood map
        im1 = ax1.imshow(self.water_depth[0], cmap=flood_cmap, vmin=0, vmax=np.max(self.water_depth))
        ax1.set_title('Current Flood Depth (mm)')
        ax1.set_xlabel('Longitude (grid units)')
        ax1.set_ylabel('Latitude (grid units)')
        plt.colorbar(im1, ax=ax1, shrink=0.6)
        
        # 2. Precipitation forecast
        precip_frame = self.precipitation_forecast.precipitation[0]
        precip_data = precip_frame.values if hasattr(precip_frame, 'values') else precip_frame
        im2 = ax2.imshow(precip_data, cmap='Blues', vmin=0, vmax=np.max(precip_data))
        ax2.set_title('Precipitation Intensity (mm/h)')
        ax2.set_xlabel('Longitude (grid units)')
        ax2.set_ylabel('Latitude (grid units)')
        plt.colorbar(im2, ax=ax2, shrink=0.6)
        
        # 3. Time series plot
        times = range(min(72, self.timesteps))  # First 3 days
        max_depths = [float(np.max(self.water_depth[t])) for t in times]
        flooded_areas = [float(np.sum(self.flood_extent[t])) / (self.grid_size**2) * 100 for t in times]
        
        ax3.plot(times, max_depths, 'b-', label='Max Water Depth (mm)', linewidth=2)
        ax3.set_xlabel('Hours from start')
        ax3.set_ylabel('Max Water Depth (mm)', color='b')
        ax3.tick_params(axis='y', labelcolor='b')
        
        ax3_twin = ax3.twinx()
        ax3_twin.plot(times, flooded_areas, 'r-', label='Flooded Area (%)', linewidth=2)
        ax3_twin.set_ylabel('Flooded Area (%)', color='r')
        ax3_twin.tick_params(axis='y', labelcolor='r')
        ax3.set_title('Flood Progression Over Time')
        ax3.grid(True, alpha=0.3)
        
        # 4. Risk level statistics
        if hasattr(self, 'simulation_results') and self.simulation_results:
            daily_stats = self.simulation_results['daily_statistics']
            days = [stat['day'] for stat in daily_stats]
            risk_levels = [stat['risk_level'] for stat in daily_stats]
            
            # Convert risk levels to numeric for plotting
            risk_numeric = [{'Low': 1, 'Moderate': 2, 'High': 3, 'Extreme': 4}.get(r, 0) for r in risk_levels]
            
            ax4.bar(days, risk_numeric, color=['green', 'yellow', 'orange', 'red'][:len(days)])
            ax4.set_xlabel('Day')
            ax4.set_ylabel('Risk Level')
            ax4.set_title('Daily Flood Risk Levels')
            ax4.set_yticks([1, 2, 3, 4])
            ax4.set_yticklabels(['Low', 'Moderate', 'High', 'Extreme'])
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save static visualization
        plt.savefig('flood_progression_analysis.png', dpi=300, bbox_inches='tight')
        print("✅ Static visualization saved as 'flood_progression_analysis.png'")
        
        # Create animation for hourly progression
        self.create_animation()
        
        return fig
    
    def create_animation(self):
        """Create animated GIF of flood progression"""
        print("🎥 Creating animated flood progression...")
        
        # Create animation figure
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Setup colormap
        colors = ['white', 'lightblue', 'blue', 'darkblue', 'purple', 'red']
        flood_cmap = LinearSegmentedColormap.from_list('flood', colors, N=100)
        
        # Initialize plot
        max_depth = np.max(self.water_depth)
        im = ax.imshow(self.water_depth[0], cmap=flood_cmap, vmin=0, vmax=max_depth, animated=True)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Water Depth (mm)', fontsize=12)
        
        # Setup plot
        ax.set_title('Bangalore Flood Progression Simulation', fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitude (relative)', fontsize=12)
        ax.set_ylabel('Latitude (relative)', fontsize=12)
        
        # Add text annotations
        time_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, fontsize=12,
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
                          verticalalignment='top')
        
        stats_text = ax.text(0.02, 0.85, '', transform=ax.transAxes, fontsize=10,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8),
                           verticalalignment='top')
        
        def animate(frame):
            """Animation function"""
            # Update flood data
            im.set_array(self.water_depth[frame])
            
            # Update time
            current_time = self.start_date + timedelta(hours=frame)
            time_text.set_text(f'Time: {current_time.strftime("%Y-%m-%d %H:%M")}')
            
            # Update statistics
            max_depth_current = float(np.max(self.water_depth[frame]))
            flooded_area = float(np.sum(self.flood_extent[frame])) / (self.grid_size**2) * 100
            precip_data = self.precipitation_forecast.precipitation[frame]
            current_precip = float(np.max(precip_data.values if hasattr(precip_data, 'values') else precip_data))
            
            stats_text.set_text(f'Max Depth: {max_depth_current:.1f}mm\n'
                               f'Flooded Area: {flooded_area:.1f}%\n'
                               f'Precipitation: {current_precip:.1f}mm/h')
            
            return [im, time_text, stats_text]
        
        # Create animation (sample every 6 hours for manageable file size)
        frames = range(0, min(self.timesteps, 72), 6)  # Every 6 hours for 3 days
        anim = animation.FuncAnimation(fig, animate, frames=frames, 
                                     interval=800, blit=False, repeat=True)
        
        # Save animation
        try:
            anim.save('flood_progression_animation.gif', writer='pillow', fps=2, dpi=100)
            print("✅ Animation saved as 'flood_progression_animation.gif'")
        except Exception as e:
            print(f"⚠️  Could not save animation: {e}")
            print("   (Animation display still works in interactive mode)")
        
        plt.show()
        return anim
    
    def generate_alerts_and_warnings(self):
        """Generate flood alerts and warnings based on simulation results"""
        print("🚨 Generating flood alerts and warnings...")
        
        if not self.simulation_results:
            raise ValueError("Simulation analysis must be completed first")
        
        alerts = []
        warnings = []
        
        # Analyze each day for alerts
        for day_stat in self.simulation_results['daily_statistics']:
            day = day_stat['day']
            date = day_stat['date']
            risk_level = day_stat['risk_level']
            max_depth = day_stat['max_water_depth_mm']
            flooded_area = day_stat['flooded_area_km2']
            
            # Generate alerts based on risk level
            if risk_level == "Extreme":
                alerts.append({
                    'type': 'EXTREME FLOOD WARNING',
                    'day': day,
                    'date': date,
                    'severity': 'CRITICAL',
                    'message': f'Extreme flood conditions expected. Water depth may reach {max_depth}mm. '
                              f'Approximately {flooded_area} km² may be affected. IMMEDIATE EVACUATION advised.',
                    'actions': [
                        'Evacuate low-lying areas immediately',
                        'Avoid all travel unless absolutely necessary',
                        'Move to higher ground',
                        'Keep emergency supplies ready'
                    ]
                })
            
            elif risk_level == "High":
                alerts.append({
                    'type': 'SEVERE FLOOD ALERT',
                    'day': day,
                    'date': date,
                    'severity': 'HIGH',
                    'message': f'Severe flooding expected. Water depth up to {max_depth}mm. '
                              f'Area of {flooded_area} km² likely to be flooded.',
                    'actions': [
                        'Prepare for potential evacuation',
                        'Avoid flooded roads and areas',
                        'Keep vehicles in safe locations',
                        'Stock emergency supplies'
                    ]
                })
            
            elif risk_level == "Moderate":
                warnings.append({
                    'type': 'FLOOD WATCH',
                    'day': day,
                    'date': date,
                    'severity': 'MODERATE',
                    'message': f'Moderate flooding possible. Water depth up to {max_depth}mm expected.',
                    'actions': [
                        'Monitor weather conditions',
                        'Avoid low-lying areas',
                        'Be prepared for travel disruptions'
                    ]
                })
            
            elif max_depth > 10:  # Even low risk with some flooding
                warnings.append({
                    'type': 'FLOOD ADVISORY',
                    'day': day,
                    'date': date,
                    'severity': 'LOW',
                    'message': f'Minor flooding possible in some areas. Water depth up to {max_depth}mm.',
                    'actions': [
                        'Exercise caution in low-lying areas',
                        'Monitor local conditions'
                    ]
                })
        
        # Save alerts and warnings
        alert_data = {
            'generated_at': datetime.now().isoformat(),
            'simulation_period': self.simulation_results['simulation_period'],
            'alerts': alerts,
            'warnings': warnings,
            'summary': {
                'total_alerts': len(alerts),
                'total_warnings': len(warnings),
                'highest_risk_day': max(self.simulation_results['daily_statistics'], 
                                      key=lambda x: {'Low': 1, 'Moderate': 2, 'High': 3, 'Extreme': 4}[x['risk_level']])
            }
        }
        
        with open('flood_alerts_warnings.json', 'w') as f:
            json.dump(alert_data, f, indent=2)
        
        print(f"✅ Generated {len(alerts)} alerts and {len(warnings)} warnings")
        print("   📄 Saved to 'flood_alerts_warnings.json'")
        
        return alert_data
    
    def run_complete_simulation(self):
        """Run the complete flood simulation pipeline"""
        print("🌊 Starting Complete Flood Simulation Pipeline")
        print("=" * 60)
        
        try:
            # Step 1: Generate weather forecast
            self.generate_weather_forecast()
            
            # Step 2: Run hydrological simulation
            self.simulate_hydrological_response()
            
            # Step 3: Analyze results
            self.analyze_flood_progression()
            
            # Step 4: Create visualizations
            self.create_progression_visualization()
            
            # Step 5: Generate alerts
            self.generate_alerts_and_warnings()
            
            print("=" * 60)
            print("🎉 Flood Simulation Pipeline Completed Successfully!")
            print("\n📁 Generated Files:")
            print("   - flood_simulation_results.json (detailed statistics)")
            print("   - flood_alerts_warnings.json (alerts and warnings)")
            print("   - flood_progression_analysis.png (static visualization)")
            print("   - flood_progression_animation.gif (animated progression)")
            
            return True
            
        except Exception as e:
            print(f"❌ Simulation failed: {str(e)}")
            return False

def main():
    """Main execution function"""
    print("🌊 Bangalore Flood Progression Simulation")
    print("Starting simulation from today for the next 7 days...")
    
    # Create and run simulation
    simulation = FloodSimulation(
        start_date=datetime.now(),
        simulation_days=7
    )
    
    success = simulation.run_complete_simulation()
    
    if success:
        print("\n✅ All simulation outputs are ready!")
        print("🎯 Check the generated files for detailed analysis and warnings.")
    else:
        print("\n❌ Simulation encountered errors. Check the console output.")

if __name__ == "__main__":
    main()