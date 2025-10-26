#Enhanced Flood Response System API Server
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
import json
import os
from typing import List, Dict, Any
import folium
from folium import plugins
import geopandas as gpd

# Try to import titiler for advanced tile serving
try:
    from titiler.core.factory import TilerFactory
    TITILER_AVAILABLE = True
except ImportError:
    TITILER_AVAILABLE = False
    print("⚠️ Titiler not available, using basic file serving")

app = FastAPI(
    title="🌊 Bangalore Flood Response System",
    description="Real-time flood risk assessment and building-level analysis for Bangalore",
    version="1.0.0"
)

# Configuration
BANGALORE_CENTER = [13.0, 77.6]
DATA_FILES = {
    'flood_risk': 'flood_risk.npy',
    'risk_categories': 'flood_risk_categories.npy', 
    'buildings': 'building_flood_risk_assessment.csv',
    'flood_cog': 'flood_risk_cog.tif',
    'precip_cog': 'flood_accum_cog.tif'
}

# Add tile server if available
if TITILER_AVAILABLE:
    cog_tiler = TilerFactory()
    app.include_router(cog_tiler.router, prefix="/tiles")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main landing page with system overview"""
    return """
    <html>
        <head>
            <title>🌊 Bangalore Flood Response System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f0f8ff; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
                .endpoint { background: white; padding: 15px; margin: 10px 0; 
                          border-left: 4px solid #667eea; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .method { display: inline-block; padding: 4px 8px; border-radius: 4px; 
                         color: white; font-size: 12px; margin-right: 10px; }
                .get { background: #28a745; }
                .post { background: #007bff; }
                code { background: #f8f9fa; padding: 2px 6px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌊 Bangalore Flood Response System</h1>
                <p>Advanced flood risk assessment and emergency response platform</p>
            </div>
            
            <div class="endpoint" style="background: #fff3cd; border-left: 4px solid #ffc107;">
                <span class="method get" style="background: #dc3545;">NEW</span>
                <strong><a href="/simulation">🌊 /simulation</a></strong> - 7-Day Flood Progression Simulation Dashboard
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong><a href="/map">/map</a></strong> - Interactive flood risk map
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong><a href="/api/flood-summary">/api/flood-summary</a></strong> - Overall flood risk statistics
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong><a href="/api/buildings/high-risk">/api/buildings/high-risk</a></strong> - Buildings at high flood risk
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong><a href="/api/buildings/search?risk_level=High">/api/buildings/search</a></strong> - Search buildings by risk level
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong><a href="/health">/health</a></strong> - System health check
            </div>
            
            <p style="margin-top: 30px; color: #666;">
                🎯 <strong>Quick Start:</strong> Visit <code>/simulation</code> for 7-day flood forecasting or <code>/map</code> for current risk visualization
            </p>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    missing_files = []
    for name, filepath in DATA_FILES.items():
        if not os.path.exists(filepath):
            missing_files.append(filepath)
    
    status = "healthy" if not missing_files else "degraded"
    
    return {
        "status": status,
        "message": "Flood Response System is operational",
        "missing_files": missing_files,
        "titiler_available": TITILER_AVAILABLE
    }

@app.get("/api/flood-summary")
async def flood_summary():
    """Get overall flood risk summary statistics"""
    try:
        # Load risk categories
        if not os.path.exists(DATA_FILES['risk_categories']):
            raise HTTPException(status_code=404, detail="Risk data not found. Run data_pipeline.py first.")
        
        risk_categories = np.load(DATA_FILES['risk_categories'])
        
        # Load building assessment
        buildings_df = None
        if os.path.exists(DATA_FILES['buildings']):
            buildings_df = pd.read_csv(DATA_FILES['buildings'])
        
        summary = {
            "region": "Bangalore, Karnataka",
            "last_updated": "2023-07-03T12:00:00Z",
            "area_analysis": {
                "low_risk_pixels": int(np.sum(risk_categories == 1)),
                "medium_risk_pixels": int(np.sum(risk_categories == 2)),
                "high_risk_pixels": int(np.sum(risk_categories == 3)),
                "very_high_risk_pixels": int(np.sum(risk_categories == 4)),
                "total_pixels": int(risk_categories.size)
            }
        }
        
        if buildings_df is not None:
            building_summary = buildings_df['risk_category'].value_counts().to_dict()
            summary["building_analysis"] = {
                "total_buildings": len(buildings_df),
                "risk_distribution": building_summary,
                "average_risk_score": float(buildings_df['flood_risk_score'].mean()),
                "buildings_at_high_risk": int(len(buildings_df[buildings_df['risk_category'].isin(['High', 'Very High'])]))
            }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.get("/api/buildings/high-risk")
async def high_risk_buildings():
    """Get list of buildings at high or very high flood risk"""
    try:
        if not os.path.exists(DATA_FILES['buildings']):
            raise HTTPException(status_code=404, detail="Building data not found")
        
        buildings_df = pd.read_csv(DATA_FILES['buildings'])
        high_risk = buildings_df[buildings_df['risk_category'].isin(['High', 'Very High'])]
        
        return {
            "count": len(high_risk),
            "buildings": high_risk.to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching high-risk buildings: {str(e)}")

@app.get("/api/buildings/search")
async def search_buildings(
    risk_level: str = None,
    building_type: str = None,
    min_risk_score: float = None,
    max_risk_score: float = None
):
    """Search buildings by various criteria"""
    try:
        if not os.path.exists(DATA_FILES['buildings']):
            raise HTTPException(status_code=404, detail="Building data not found")
        
        buildings_df = pd.read_csv(DATA_FILES['buildings'])
        
        # Apply filters
        filtered_df = buildings_df.copy()
        
        if risk_level:
            filtered_df = filtered_df[filtered_df['risk_category'] == risk_level]
        
        if building_type:
            filtered_df = filtered_df[filtered_df['building_type'] == building_type]
        
        if min_risk_score is not None:
            filtered_df = filtered_df[filtered_df['flood_risk_score'] >= min_risk_score]
        
        if max_risk_score is not None:
            filtered_df = filtered_df[filtered_df['flood_risk_score'] <= max_risk_score]
        
        return {
            "query": {
                "risk_level": risk_level,
                "building_type": building_type,
                "min_risk_score": min_risk_score,
                "max_risk_score": max_risk_score
            },
            "count": len(filtered_df),
            "buildings": filtered_df.to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching buildings: {str(e)}")

@app.get("/map", response_class=HTMLResponse)
async def interactive_map():
    """Generate interactive flood risk map"""
    try:
        # Create base map centered on Bangalore
        m = folium.Map(
            location=BANGALORE_CENTER,
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add title
        title_html = '''
        <h3 align="center" style="font-size:20px; color: #2E86C1;"><b>🌊 Bangalore Flood Risk Assessment</b></h3>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Load and display buildings if available
        if os.path.exists(DATA_FILES['buildings']):
            buildings_df = pd.read_csv(DATA_FILES['buildings'])
            
            # Color mapping for risk levels
            risk_colors = {
                'Low': 'green',
                'Medium': 'orange', 
                'High': 'red',
                'Very High': 'darkred',
                'No Data': 'gray'
            }
            
            # Add building markers
            for _, building in buildings_df.iterrows():
                color = risk_colors.get(building['risk_category'], 'blue')
                
                # Create popup content
                popup_content = f"""
                <div style="width: 200px;">
                    <b>Building {building['building_id']}</b><br>
                    <b>Type:</b> {building['building_type']}<br>
                    <b>Levels:</b> {building['levels']}<br>
                    <b>Risk Level:</b> <span style="color: {color}; font-weight: bold;">{building['risk_category']}</span><br>
                    <b>Risk Score:</b> {building['flood_risk_score']:.3f}<br>
                    <b>Coordinates:</b> {building['latitude']:.4f}, {building['longitude']:.4f}
                </div>
                """
                
                folium.CircleMarker(
                    location=[building['latitude'], building['longitude']],
                    radius=5,
                    popup=folium.Popup(popup_content, max_width=250),
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7,
                    weight=2
                ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                   bottom: 50px; left: 50px; width: 150px; height: 120px; 
                   background-color: white; border:2px solid grey; z-index:9999; 
                   font-size:14px; padding: 10px">
        <p><b>Flood Risk Levels</b></p>
        <p><i class="fa fa-circle" style="color:green"></i> Low Risk</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Medium Risk</p>
        <p><i class="fa fa-circle" style="color:red"></i> High Risk</p>
        <p><i class="fa fa-circle" style="color:darkred"></i> Very High Risk</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add measurement tool
        plugins.MeasureControl().add_to(m)
        
        # Add fullscreen option
        plugins.Fullscreen().add_to(m)
        
        return m._repr_html_()
        
    except Exception as e:
        return f"<h2>Error generating map: {str(e)}</h2><p>Please ensure data_pipeline.py has been run first.</p>"

# Try to integrate simulation features
try:
    from simulation_api import setup_simulation_api
    setup_simulation_api(app)
    SIMULATION_INTEGRATED = True
    print("✅ Flood simulation features integrated")
except ImportError:
    SIMULATION_INTEGRATED = False
    print("⚠️  Simulation features not available")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Bangalore Flood Response System...")
    print("📍 Access the system at: http://localhost:8000")
    print("🗺️  Interactive map at: http://localhost:8000/map")
    if SIMULATION_INTEGRATED:
        print("🌊 Flood simulation at: http://localhost:8000/simulation")
    print("📡 API documentation at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)