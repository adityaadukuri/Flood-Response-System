#Flood Simulation Web Interface
#Extends the main API to include simulation endpoints and real-time updates

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import json
import os
from datetime import datetime, timedelta
import asyncio
import numpy as np
from typing import Dict, Any

# Import our simulation model
try:
    from flood_simulation import FloodSimulation
    SIMULATION_AVAILABLE = True
except ImportError:
    SIMULATION_AVAILABLE = False
    print("⚠️  Flood simulation module not available")

class SimulationManager:
    """Manages flood simulation runs and results"""
    
    def __init__(self):
        self.current_simulation = None
        self.simulation_status = "idle"  # idle, running, completed, error
        self.last_run = None
        self.results_cache = {}
    
    async def run_simulation_async(self, days=7):
        """Run flood simulation asynchronously"""
        if not SIMULATION_AVAILABLE:
            raise ValueError("Simulation module not available")
        
        self.simulation_status = "running"
        
        try:
            print(f"🌊 Starting {days}-day flood simulation...")
            
            # Create and run simulation
            self.current_simulation = FloodSimulation(
                start_date=datetime.now(),
                simulation_days=days
            )
            
            success = self.current_simulation.run_complete_simulation()
            
            if success:
                self.simulation_status = "completed"
                self.last_run = datetime.now()
                
                # Cache results
                if os.path.exists('flood_simulation_results.json'):
                    with open('flood_simulation_results.json', 'r') as f:
                        self.results_cache = json.load(f)
                
                print("✅ Simulation completed successfully!")
            else:
                self.simulation_status = "error"
                print("❌ Simulation failed")
            
        except Exception as e:
            self.simulation_status = "error"
            print(f"❌ Simulation error: {str(e)}")
    
    def get_status(self):
        """Get current simulation status"""
        return {
            "status": self.simulation_status,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "has_results": bool(self.results_cache)
        }

# Initialize simulation manager
sim_manager = SimulationManager()

def add_simulation_routes(app: FastAPI):
    """Add simulation routes to the FastAPI app"""
    
    @app.get("/simulation")
    async def simulation_dashboard():
        """Simulation dashboard page"""
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🌊 Flood Simulation Dashboard</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container { 
                    max-width: 1200px; margin: 0 auto; background: white; 
                    border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }
                .header { 
                    text-align: center; margin-bottom: 30px; 
                    color: #333; border-bottom: 2px solid #667eea; padding-bottom: 20px;
                }
                .controls { 
                    background: #f8f9fa; padding: 20px; border-radius: 10px; 
                    margin-bottom: 30px; border: 1px solid #e9ecef;
                }
                .status-panel { 
                    background: #e8f4fd; padding: 15px; border-radius: 8px; 
                    margin: 15px 0; border-left: 4px solid #007bff;
                }
                .button { 
                    background: #007bff; color: white; padding: 12px 24px; 
                    border: none; border-radius: 6px; cursor: pointer; 
                    font-size: 16px; margin: 5px;
                    transition: background 0.3s;
                }
                .button:hover { background: #0056b3; }
                .button:disabled { background: #6c757d; cursor: not-allowed; }
                .results-grid { 
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 20px; margin-top: 20px;
                }
                .result-card { 
                    background: white; border: 1px solid #dee2e6; border-radius: 8px; 
                    padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .metric { 
                    font-size: 24px; font-weight: bold; color: #007bff; 
                    margin-bottom: 5px;
                }
                .label { color: #6c757d; font-size: 14px; }
                .progress-bar { 
                    width: 100%; height: 20px; background: #e9ecef; 
                    border-radius: 10px; overflow: hidden; margin: 10px 0;
                }
                .progress-fill { 
                    height: 100%; background: linear-gradient(90deg, #28a745, #20c997); 
                    transition: width 0.3s;
                }
                .alert { 
                    padding: 12px; margin: 10px 0; border-radius: 6px; 
                    border-left: 4px solid;
                }
                .alert-danger { background: #f8d7da; border-color: #dc3545; color: #721c24; }
                .alert-warning { background: #fff3cd; border-color: #ffc107; color: #856404; }
                .alert-info { background: #d1ecf1; border-color: #17a2b8; color: #0c5460; }
                .hidden { display: none; }
                #progressContainer { margin: 20px 0; }
                
                /* Flood Animation Styles */
                @keyframes flood-pulse {
                    0% { transform: scale(1); opacity: 0.6; }
                    50% { transform: scale(1.1); opacity: 0.8; }
                    100% { transform: scale(1); opacity: 0.6; }
                }
                
                @keyframes flood-front-pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.3); }
                    100% { transform: scale(1); }
                }
                
                @keyframes storm-rotation {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .flood-pulse {
                    animation: flood-pulse 2s ease-in-out infinite;
                }
                
                .flood-front-marker {
                    animation: flood-front-pulse 1.5s ease-in-out infinite;
                }
                
                .storm-arrow {
                    color: #FF0000;
                    font-size: 16px;
                    text-shadow: 0 0 3px rgba(255,255,255,0.8);
                }
                
                .emergency-warning {
                    animation: flood-pulse 1s ease-in-out infinite;
                    filter: drop-shadow(0 0 5px rgba(255,0,0,0.8));
                }
                
                /* Enhanced legend */
                .legend-movement {
                    margin-top: 10px;
                    padding-top: 10px;
                    border-top: 1px solid #ddd;
                }
                
                .movement-indicator {
                    display: inline-block;
                    margin: 0 5px;
                    animation: flood-front-pulse 2s ease-in-out infinite;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌊 Bangalore Flood Simulation Dashboard</h1>
                    <p>Advanced 7-day flood progression modeling and analysis</p>
                </div>
                
                <div class="controls">
                    <h3>🎮 Simulation Controls</h3>
                    <div id="statusPanel" class="status-panel">
                        <strong>Status:</strong> <span id="statusText">Loading...</span><br>
                        <span id="lastRun"></span>
                    </div>
                    
                    <button class="button" onclick="startSimulation()" id="startBtn">
                        🚀 Start New Simulation (7 days)
                    </button>
                    <button class="button" onclick="loadResults()" id="loadBtn">
                        📊 Load Previous Results
                    </button>
                    <button class="button" onclick="downloadResults()" id="downloadBtn">
                        💾 Download Reports
                    </button>
                    <button class="button" onclick="openAnimatedMap()" id="animatedMapBtn">
                        🎬 View Animated Map
                    </button>
                    
                    <div id="progressContainer" class="hidden">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                        </div>
                        <div id="progressText">Initializing simulation...</div>
                    </div>
                </div>
                
                <div id="alertsSection" class="hidden">
                    <h3>🚨 Flood Alerts & Warnings</h3>
                    <div id="alertsContainer"></div>
                </div>
                
                <div id="resultsSection" class="hidden">
                    <h3>📊 Simulation Results</h3>
                    <div class="results-grid" id="resultsGrid">
                        <!-- Results will be populated here -->
                    </div>
                </div>
                
                <div id="visualizationSection" class="hidden">
                    <h3>📈 Visualizations</h3>
                    <div style="text-align: center; margin: 20px 0;">
                        <img id="analysisChart" src="" alt="Analysis Chart" style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    </div>
                </div>
            </div>
            
            <script>
                let simulationRunning = false;
                
                async function checkStatus() {
                    try {
                        const response = await fetch('/api/simulation/status');
                        const status = await response.json();
                        
                        document.getElementById('statusText').textContent = status.status;
                        
                        if (status.last_run) {
                            const lastRun = new Date(status.last_run);
                            document.getElementById('lastRun').innerHTML = 
                                `<small>Last run: ${lastRun.toLocaleString()}</small>`;
                        }
                        
                        // Update UI based on status
                        const startBtn = document.getElementById('startBtn');
                        const progressContainer = document.getElementById('progressContainer');
                        
                        if (status.status === 'running') {
                            startBtn.disabled = true;
                            startBtn.textContent = '⏳ Simulation Running...';
                            progressContainer.classList.remove('hidden');
                            simulationRunning = true;
                        } else {
                            startBtn.disabled = false;
                            startBtn.textContent = '🚀 Start New Simulation (7 days)';
                            progressContainer.classList.add('hidden');
                            simulationRunning = false;
                        }
                        
                        if (status.has_results) {
                            document.getElementById('loadBtn').disabled = false;
                            document.getElementById('downloadBtn').disabled = false;
                        }
                        
                    } catch (error) {
                        console.error('Error checking status:', error);
                        document.getElementById('statusText').textContent = 'Error';
                    }
                }
                
                async function startSimulation() {
                    if (simulationRunning) return;
                    
                    try {
                        const response = await fetch('/api/simulation/start', { method: 'POST' });
                        
                        if (response.ok) {
                            simulationRunning = true;
                            document.getElementById('progressContainer').classList.remove('hidden');
                            
                            // Poll for progress
                            const progressInterval = setInterval(async () => {
                                await checkStatus();
                                
                                if (!simulationRunning) {
                                    clearInterval(progressInterval);
                                    loadResults(); // Auto-load results when done
                                }
                            }, 2000);
                        } else {
                            alert('Failed to start simulation');
                        }
                    } catch (error) {
                        console.error('Error starting simulation:', error);
                        alert('Error starting simulation');
                    }
                }
                
                async function loadResults() {
                    try {
                        const response = await fetch('/api/simulation/results');
                        const results = await response.json();
                        
                        // Show results section
                        document.getElementById('resultsSection').classList.remove('hidden');
                        
                        // Populate results grid
                        const resultsGrid = document.getElementById('resultsGrid');
                        resultsGrid.innerHTML = `
                            <div class="result-card">
                                <div class="metric">${results.max_water_depth_mm}mm</div>
                                <div class="label">Peak Water Depth</div>
                            </div>
                            <div class="result-card">
                                <div class="metric">${results.max_flooded_area_km2} km²</div>
                                <div class="label">Maximum Flooded Area</div>
                            </div>
                            <div class="result-card">
                                <div class="metric">${results.total_precipitation_mm}mm</div>
                                <div class="label">Total Precipitation</div>
                            </div>
                            <div class="result-card">
                                <div class="metric">${results.daily_statistics.length}</div>
                                <div class="label">Days Simulated</div>
                            </div>
                        `;
                        
                        // Load alerts
                        loadAlerts();
                        
                        // Show visualization if available
                        if (document.getElementById('analysisChart')) {
                            document.getElementById('analysisChart').src = 
                                '/api/simulation/visualization?' + new Date().getTime();
                            document.getElementById('visualizationSection').classList.remove('hidden');
                        }
                        
                    } catch (error) {
                        console.error('Error loading results:', error);
                        alert('Error loading results');
                    }
                }
                
                async function loadAlerts() {
                    try {
                        const response = await fetch('/api/simulation/alerts');
                        const alertData = await response.json();
                        
                        if (alertData.alerts.length > 0 || alertData.warnings.length > 0) {
                            document.getElementById('alertsSection').classList.remove('hidden');
                            
                            let alertsHtml = '';
                            
                            alertData.alerts.forEach(alert => {
                                alertsHtml += `
                                    <div class="alert alert-danger">
                                        <strong>${alert.type}</strong> - Day ${alert.day} (${alert.date})<br>
                                        ${alert.message}
                                    </div>
                                `;
                            });
                            
                            alertData.warnings.forEach(warning => {
                                const alertClass = warning.severity === 'MODERATE' ? 'alert-warning' : 'alert-info';
                                alertsHtml += `
                                    <div class="alert ${alertClass}">
                                        <strong>${warning.type}</strong> - Day ${warning.day} (${warning.date})<br>
                                        ${warning.message}
                                    </div>
                                `;
                            });
                            
                            document.getElementById('alertsContainer').innerHTML = alertsHtml;
                        }
                        
                    } catch (error) {
                        console.error('Error loading alerts:', error);
                    }
                }
                
                function downloadResults() {
                    window.open('/api/simulation/download/results', '_blank');
                }
                
                function openAnimatedMap() {
                    window.open('/simulation/animated-map', '_blank');
                }
                
                // Initialize dashboard
                checkStatus();
                
                // Auto-refresh status every 10 seconds
                setInterval(checkStatus, 10000);
            </script>
        </body>
        </html>
        """)
    
    @app.get("/api/simulation/status")
    async def get_simulation_status():
        """Get current simulation status"""
        return sim_manager.get_status()
    
    @app.post("/api/simulation/start")
    async def start_simulation(background_tasks: BackgroundTasks):
        """Start a new flood simulation"""
        if sim_manager.simulation_status == "running":
            raise HTTPException(status_code=400, detail="Simulation already running")
        
        if not SIMULATION_AVAILABLE:
            raise HTTPException(status_code=503, detail="Simulation module not available")
        
        # Start simulation in background
        background_tasks.add_task(sim_manager.run_simulation_async, 7)
        
        return {"message": "Simulation started", "status": "running"}
    
    @app.get("/api/simulation/results")
    async def get_simulation_results():
        """Get simulation results"""
        if not sim_manager.results_cache:
            # Try to load from file
            if os.path.exists('flood_simulation_results.json'):
                with open('flood_simulation_results.json', 'r') as f:
                    sim_manager.results_cache = json.load(f)
            else:
                raise HTTPException(status_code=404, detail="No simulation results available")
        
        return sim_manager.results_cache
    
    @app.get("/api/simulation/alerts")
    async def get_simulation_alerts():
        """Get simulation alerts and warnings"""
        if not os.path.exists('flood_alerts_warnings.json'):
            raise HTTPException(status_code=404, detail="No alerts data available")
        
        with open('flood_alerts_warnings.json', 'r') as f:
            return json.load(f)
    
    @app.get("/api/simulation/visualization")
    async def get_simulation_visualization():
        """Get simulation visualization image"""
        if not os.path.exists('flood_progression_analysis.png'):
            raise HTTPException(status_code=404, detail="Visualization not available")
        
        return FileResponse('flood_progression_analysis.png', media_type='image/png')
    
    @app.get("/api/simulation/download/results")
    async def download_results():
        """Download simulation results as JSON"""
        if not os.path.exists('flood_simulation_results.json'):
            raise HTTPException(status_code=404, detail="Results file not available")
        
        return FileResponse(
            'flood_simulation_results.json',
            media_type='application/json',
            filename=f'flood_simulation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )

    @app.get("/api/simulation/daily-forecast")
    async def get_daily_forecast():
        """Get daily flood forecast for next 7 days"""
        if not sim_manager.results_cache:
            raise HTTPException(status_code=404, detail="No simulation results available")
        
        # Extract daily forecasts
        daily_stats = sim_manager.results_cache.get('daily_statistics', [])
        
        forecast = []
        for day_stat in daily_stats:
            forecast.append({
                'date': day_stat['date'],
                'day': day_stat['day'],
                'risk_level': day_stat['risk_level'],
                'max_water_depth_mm': day_stat['max_water_depth_mm'],
                'flooded_area_km2': day_stat['flooded_area_km2'],
                'precipitation_mm': day_stat['total_precipitation_mm'],
                'risk_score': {
                    'Low': 1, 'Moderate': 2, 'High': 3, 'Extreme': 4
                }.get(day_stat['risk_level'], 0)
            })
        
        return {
            'forecast_period': sim_manager.results_cache.get('simulation_period', ''),
            'generated_at': datetime.now().isoformat(),
            'daily_forecast': forecast
        }

    @app.get("/simulation/animated-map", response_class=HTMLResponse)
    async def animated_flood_map():
        """Interactive animated flood progression map"""
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🌊 Animated Flood Progression - Bangalore</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css" />
            <style>
                body { 
                    margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f0f2f5;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 15px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .controls {
                    background: white; padding: 15px; display: flex; justify-content: center; 
                    align-items: center; gap: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    flex-wrap: wrap;
                }
                .control-group {
                    display: flex; align-items: center; gap: 8px;
                    background: #f8f9fa; padding: 8px 15px; border-radius: 20px;
                    border: 1px solid #e9ecef;
                }
                .control-group label { 
                    font-weight: 500; color: #495057; margin-right: 5px; 
                }
                #map { 
                    height: calc(100vh - 140px); width: 100%; 
                }
                .time-display {
                    background: rgba(255,255,255,0.95); padding: 10px 20px; 
                    border-radius: 25px; position: absolute; top: 20px; right: 20px; 
                    z-index: 1000; font-weight: bold; color: #333;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }
                .legend {
                    background: rgba(255,255,255,0.95); padding: 15px; 
                    border-radius: 10px; position: absolute; bottom: 20px; left: 20px; 
                    z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    min-width: 200px;
                }
                .legend h4 { margin: 0 0 10px 0; color: #333; }
                .legend-item { 
                    display: flex; align-items: center; margin: 5px 0; 
                }
                .legend-color { 
                    width: 20px; height: 20px; margin-right: 8px; 
                    border-radius: 3px; border: 1px solid #ccc;
                }
                .play-btn { 
                    background: #28a745; color: white; border: none; 
                    padding: 8px 16px; border-radius: 20px; cursor: pointer;
                    font-weight: bold; transition: all 0.3s;
                }
                .play-btn:hover { background: #218838; transform: scale(1.05); }
                .pause-btn { background: #dc3545; }
                .pause-btn:hover { background: #c82333; }
                .slider-container {
                    flex: 1; min-width: 200px; max-width: 400px;
                }
                #timeSlider {
                    width: 100%; height: 8px; border-radius: 5px; 
                    background: #ddd; outline: none; cursor: pointer;
                }
                #timeSlider::-webkit-slider-thumb {
                    appearance: none; width: 20px; height: 20px; 
                    border-radius: 50%; background: #007bff; cursor: pointer;
                }
                .stats-panel {
                    background: rgba(255,255,255,0.95); padding: 15px; 
                    border-radius: 10px; position: absolute; top: 80px; right: 20px; 
                    z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    min-width: 250px;
                }
                .stats-panel h4 { margin: 0 0 10px 0; color: #333; }
                .stat-item {
                    display: flex; justify-content: space-between; 
                    margin: 5px 0; padding: 3px 0; border-bottom: 1px solid #eee;
                }
                .stat-label { color: #666; }
                .stat-value { font-weight: bold; color: #333; }
                .loading-overlay {
                    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.7); color: white; 
                    display: flex; align-items: center; justify-content: center;
                    z-index: 9999; font-size: 18px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌊 Animated Flood Progression Map - Bangalore</h1>
                <p>Real-time visualization of flood development across the city over 4 days</p>
            </div>
            
            <div class="controls">
                <div class="control-group">
                    <button id="playPauseBtn" class="play-btn" onclick="toggleAnimation()">
                        ▶️ Play
                    </button>
                </div>
                
                <div class="control-group">
                    <label>Speed:</label>
                    <select id="speedControl" onchange="updateSpeed()">
                        <option value="2000">Slow (2s)</option>
                        <option value="1000" selected>Normal (1s)</option>
                        <option value="500">Fast (0.5s)</option>
                        <option value="250">Very Fast (0.25s)</option>
                    </select>
                </div>
                
                <div class="control-group slider-container">
                    <label>Time:</label>
                    <input type="range" id="timeSlider" min="0" max="95" value="0" 
                           oninput="setTimeStep(this.value)">
                </div>
                
                <div class="control-group">
                    <label>View:</label>
                    <select id="viewControl" onchange="updateView()">
                        <option value="water" selected>🌊 Flood Movement</option>
                        <option value="precipitation">⛈️ Storm Systems</option>
                        <option value="risk">🚨 Risk Assessment</option>
                    </select>
                </div>
            </div>
            
            <div id="map"></div>
            
            <div class="time-display" id="timeDisplay">
                Day 1, Hour 0 (2025-10-26 00:00)
            </div>
            
            <div class="stats-panel">
                <h4>📊 Flood Progression Stats</h4>
                <div class="stat-item">
                    <span class="stat-label">Max Water Depth:</span>
                    <span class="stat-value" id="maxDepth">0 mm</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Flooded Area:</span>
                    <span class="stat-value" id="floodedArea">0%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Active Zones:</span>
                    <span class="stat-value" id="activeZones">0</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Expanding Fronts:</span>
                    <span class="stat-value" id="expandingFronts">0</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Precipitation Rate:</span>
                    <span class="stat-value" id="precipRate">0 mm/h</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Risk Status:</span>
                    <span class="stat-value" id="riskLevel">Low</span>
                </div>
            </div>
            
            <div class="legend">
                <h4>🗺️ Flood Movement Legend</h4>
                <div class="legend-item">
                    <div class="legend-color" style="background: #8B0000; border-radius: 50%;"></div>
                    <span>🔴 Severe Flood Zones</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #FF0000; border-radius: 50%;"></div>
                    <span>🟠 Moderate Flood Zones</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #FF6B6B; border-radius: 50%;"></div>
                    <span>🟡 Light Flood Areas</span>
                </div>
                <div class="legend-movement">
                    <div class="legend-item">
                        <span class="movement-indicator" style="color: #FF0000;">●</span>
                        <span>Flood Fronts (Expanding)</span>
                    </div>
                    <div class="legend-item">
                        <span style="color: #FF0000;">→</span>
                        <span>Movement Direction</span>
                    </div>
                    <div class="legend-item">
                        <span style="font-size: 16px;">🚨</span>
                        <span>Emergency Zones</span>
                    </div>
                    <div class="legend-item">
                        <span style="font-size: 16px;">⛈️</span>
                        <span>Active Storm Systems</span>
                    </div>
                </div>
            </div>
            
            <div id="loadingOverlay" class="loading-overlay">
                <div>
                    <div>🌊 Loading flood simulation data...</div>
                    <div style="margin-top: 10px; font-size: 14px;">This may take a few moments</div>
                </div>
            </div>
            
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>
            
            <script>
                // Initialize map
                const map = L.map('map').setView([13.0, 77.6], 11);
                
                // Add base layers
                const baseLayers = {
                    'OpenStreetMap': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '© OpenStreetMap contributors'
                    }),
                    'Satellite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                        attribution: '© Esri'
                    })
                };
                
                baseLayers['OpenStreetMap'].addTo(map);
                L.control.layers(baseLayers).addTo(map);
                
                // Animation variables
                let isPlaying = false;
                let currentTimeStep = 0;
                let animationInterval;
                let animationSpeed = 1000;
                let simulationData = null;
                let currentView = 'water';
                let overlayLayers = [];
                
                // Initialize the visualization
                async function initializeVisualization() {
                    try {
                        // Load simulation data
                        const response = await fetch('/api/simulation/animation-data');
                        simulationData = await response.json();
                        
                        if (!simulationData || !simulationData.timesteps) {
                            throw new Error('No simulation data available');
                        }
                        
                        // Update slider max value
                        const slider = document.getElementById('timeSlider');
                        slider.max = simulationData.timesteps.length - 1;
                        
                        // Hide loading overlay
                        document.getElementById('loadingOverlay').style.display = 'none';
                        
                        // Display first timestep
                        updateVisualization(0);
                        
                    } catch (error) {
                        console.error('Error loading simulation data:', error);
                        document.getElementById('loadingOverlay').innerHTML = 
                            '<div>❌ Error loading simulation data<br><small>Please run a simulation first</small></div>';
                    }
                }
                
                function updateVisualization(timeStep) {
                    if (!simulationData || !simulationData.timesteps[timeStep]) {
                        return;
                    }
                    
                    const data = simulationData.timesteps[timeStep];
                    currentTimeStep = timeStep;
                    
                    // Clear existing overlay layers
                    overlayLayers.forEach(layer => map.removeLayer(layer));
                    overlayLayers = [];
                    
                    // Update time display
                    const timeInfo = data.time_info;
                    document.getElementById('timeDisplay').textContent = 
                        `Day ${timeInfo.day}, Hour ${timeInfo.hour} (${timeInfo.datetime})`;
                    
                    // Update enhanced stats with flood movement info
                    document.getElementById('maxDepth').textContent = `${data.stats.max_water_depth.toFixed(1)} mm`;
                    document.getElementById('floodedArea').textContent = `${data.stats.flooded_area_percent.toFixed(1)}%`;
                    document.getElementById('precipRate').textContent = `${data.stats.max_precipitation.toFixed(1)} mm/h`;
                    
                    // Update flood movement stats
                    const activeZones = data.active_flood_zones ? data.active_flood_zones.length : 0;
                    const expandingFronts = data.flood_fronts ? data.flood_fronts.length : 0;
                    document.getElementById('activeZones').textContent = activeZones;
                    document.getElementById('expandingFronts').textContent = expandingFronts;
                    
                    // Enhanced risk level with status indicators
                    let riskStatus = data.stats.risk_level;
                    if (data.stats.risk_level === 'Low') riskStatus = 'Low 🟢';
                    else if (data.stats.risk_level === 'Moderate') riskStatus = 'Moderate 🟡';
                    else if (data.stats.risk_level === 'High') riskStatus = 'High 🟠';
                    else if (data.stats.risk_level === 'Extreme') riskStatus = 'Extreme 🔴';
                    
                    document.getElementById('riskLevel').textContent = riskStatus;
                    
                    // Add progression status
                    if (data.stats.progression_status) {
                        document.getElementById('riskLevel').innerHTML = 
                            `${riskStatus}<br><small>${data.stats.progression_status}</small>`;
                    }
                    
                    // Update slider
                    document.getElementById('timeSlider').value = timeStep;
                    
                    // Always show flood movement visualization
                    createFloodMovementVisualization(data);
                    
                    // Add additional layers based on current view
                    if (currentView === 'precipitation') {
                        createPrecipitationMovement(data);
                    } else if (currentView === 'risk') {
                        createRiskAssessmentLayer(data);
                    }
                }
                
                function createFloodMovementVisualization(data) {
                    // 1. Show active flood zones as pulsating red circles
                    if (data.active_flood_zones) {
                        data.active_flood_zones.forEach((zone, index) => {
                            const intensity = zone.intensity;
                            let color, radius;
                            
                            // Determine size and color based on flood severity
                            if (zone.type === 'severe') {
                                color = '#8B0000';  // Dark red
                                radius = 300 + intensity * 5;
                            } else if (zone.type === 'moderate') {
                                color = '#FF0000';  // Red
                                radius = 200 + intensity * 3;
                            } else {
                                color = '#FF6B6B';  // Light red
                                radius = 100 + intensity * 2;
                            }
                            
                            // Create pulsating circle
                            const circle = L.circle([zone.lat, zone.lon], {
                                radius: radius,
                                color: color,
                                fillColor: color,
                                fillOpacity: 0.6,
                                weight: 2,
                                className: 'flood-pulse'
                            });
                            
                            circle.bindTooltip(
                                `<strong>Active Flood Zone</strong><br>
                                 Severity: ${zone.type.toUpperCase()}<br>
                                 Water Depth: ${intensity.toFixed(1)}mm<br>
                                 Status: Flooded Area`
                            );
                            
                            circle.addTo(map);
                            overlayLayers.push(circle);
                            
                            // Add pulsing animation with CSS
                            setTimeout(() => {
                                if (circle._path) {
                                    circle._path.style.animation = `flood-pulse 2s ease-in-out infinite`;
                                }
                            }, index * 100); // Stagger animations
                        });
                    }
                    
                    // 2. Show flood fronts as moving red dots
                    if (data.flood_fronts) {
                        data.flood_fronts.forEach((front, index) => {
                            // Create moving marker for flood front
                            const marker = L.circleMarker([front.lat, front.lon], {
                                radius: 8 + Math.min(front.intensity / 5, 10),
                                color: '#FF0000',
                                fillColor: '#FF4444',
                                fillOpacity: 0.9,
                                weight: 3,
                                className: 'flood-front-marker'
                            });
                            
                            // Add movement trail effect
                            if (front.movement && (front.movement.lat !== 0 || front.movement.lon !== 0)) {
                                const endLat = front.lat + front.movement.lat * 10;  // Exaggerate movement
                                const endLon = front.lon + front.movement.lon * 10;
                                
                                // Create movement arrow/line
                                const movementLine = L.polyline([
                                    [front.lat, front.lon],
                                    [endLat, endLon]
                                ], {
                                    color: '#FF0000',
                                    weight: 3,
                                    opacity: 0.7,
                                    dashArray: '5, 10'
                                });
                                
                                movementLine.addTo(map);
                                overlayLayers.push(movementLine);
                            }
                            
                            marker.bindTooltip(
                                `<strong>🌊 Flood Front</strong><br>
                                 Intensity: ${front.intensity.toFixed(1)}mm<br>
                                 Status: Expanding<br>
                                 Movement: ${front.movement ? 'Active' : 'Stationary'}`
                            );
                            
                            marker.addTo(map);
                            overlayLayers.push(marker);
                            
                            // Animate marker appearance
                            setTimeout(() => {
                                if (marker._path) {
                                    marker._path.style.animation = `flood-front-pulse 1.5s ease-in-out infinite`;
                                }
                            }, index * 50);
                        });
                    }
                }
                
                function createPrecipitationMovement(data) {
                    // Show moving storm systems with directional arrows
                    if (data.movement_vectors) {
                        data.movement_vectors.forEach((vector, index) => {
                            if (vector.type === 'precipitation') {
                                const intensity = vector.intensity;
                                let color, radius;
                                
                                // Storm intensity visualization
                                if (intensity > 15) {
                                    color = '#8B0000';  // Dark red - extreme
                                    radius = 400;
                                } else if (intensity > 10) {
                                    color = '#FF0000';  // Red - heavy
                                    radius = 300;
                                } else if (intensity > 5) {
                                    color = '#FF6B6B';  // Light red - moderate
                                    radius = 200;
                                } else {
                                    color = '#FFB6C1';  // Pink - light
                                    radius = 150;
                                }
                                
                                // Create storm center
                                const stormCenter = L.circle([vector.lat, vector.lon], {
                                    radius: radius,
                                    color: color,
                                    fillColor: color,
                                    fillOpacity: 0.4,
                                    weight: 2,
                                    dashArray: '10, 5'
                                });
                                
                                // Add storm movement vector
                                if (vector.movement) {
                                    const endLat = vector.lat + vector.movement.lat * 50;  // Exaggerate for visibility
                                    const endLon = vector.lon + vector.movement.lon * 50;
                                    
                                    // Create movement arrow
                                    const arrow = L.polyline([
                                        [vector.lat, vector.lon],
                                        [endLat, endLon]
                                    ], {
                                        color: color,
                                        weight: 4,
                                        opacity: 0.8
                                    });
                                    
                                    // Add arrowhead
                                    const arrowHead = L.marker([endLat, endLon], {
                                        icon: L.divIcon({
                                            className: 'storm-arrow',
                                            html: '▶',
                                            iconSize: [20, 20],
                                            iconAnchor: [10, 10]
                                        })
                                    });
                                    
                                    arrow.addTo(map);
                                    arrowHead.addTo(map);
                                    overlayLayers.push(arrow);
                                    overlayLayers.push(arrowHead);
                                }
                                
                                stormCenter.bindTooltip(
                                    `<strong>🌩️ Storm System</strong><br>
                                     Intensity: ${intensity.toFixed(1)} mm/h<br>
                                     Status: Moving Storm<br>
                                     Type: ${intensity > 15 ? 'Extreme' : intensity > 10 ? 'Heavy' : 'Moderate'} Rain`
                                );
                                
                                stormCenter.addTo(map);
                                overlayLayers.push(stormCenter);
                                
                                // Add storm animation
                                setTimeout(() => {
                                    if (stormCenter._path) {
                                        stormCenter._path.style.animation = `storm-rotation 3s linear infinite`;
                                    }
                                }, index * 200);
                            }
                        });
                    }
                }
                
                function createRiskAssessmentLayer(data) {
                    // Show comprehensive risk assessment with movement patterns
                    createFloodMovementVisualization(data);
                    
                    // Add evacuation route indicators and risk zones
                    if (data.active_flood_zones && data.flood_fronts) {
                        // High-risk evacuation points
                        const highRiskAreas = data.active_flood_zones.filter(zone => zone.type === 'severe');
                        
                        highRiskAreas.forEach(zone => {
                            // Emergency warning marker
                            const warningMarker = L.marker([zone.lat, zone.lon], {
                                icon: L.divIcon({
                                    className: 'emergency-warning',
                                    html: '🚨',
                                    iconSize: [30, 30],
                                    iconAnchor: [15, 15]
                                })
                            });
                            
                            warningMarker.bindTooltip(
                                `<strong>🚨 EMERGENCY ZONE</strong><br>
                                 Water Depth: ${zone.intensity.toFixed(1)}mm<br>
                                 Status: Critical Flooding<br>
                                 Action: Immediate Evacuation Required`
                            );
                            
                            warningMarker.addTo(map);
                            overlayLayers.push(warningMarker);
                        });
                        
                        // Show flood progression risk
                        data.flood_fronts.forEach(front => {
                            if (front.intensity > 10) {
                                const riskZone = L.circle([front.lat, front.lon], {
                                    radius: 500,
                                    color: '#FF8C00',
                                    fillColor: '#FF8C00',
                                    fillOpacity: 0.3,
                                    weight: 2,
                                    dashArray: '15, 10'
                                });
                                
                                riskZone.bindTooltip('High Risk Expansion Zone');
                                riskZone.addTo(map);
                                overlayLayers.push(riskZone);
                            }
                        });
                    }
                }
                
                function getWaterDepthColor(depth) {
                    if (depth > 20) return '#0066cc';      // Deep blue - severe
                    if (depth > 10) return '#0099ff';      // Blue - moderate
                    if (depth > 5) return '#66ccff';       // Light blue - light
                    return '#ccf2ff';                       // Very light blue - minimal
                }
                
                function getPrecipitationColor(precip) {
                    if (precip > 15) return '#8B0000';     // Dark red - extreme
                    if (precip > 10) return '#FF0000';     // Red - heavy
                    if (precip > 5) return '#FF6B6B';      // Light red - moderate
                    return '#FFB6C1';                       // Pink - light
                }
                
                function toggleAnimation() {
                    const btn = document.getElementById('playPauseBtn');
                    
                    if (isPlaying) {
                        clearInterval(animationInterval);
                        isPlaying = false;
                        btn.textContent = '▶️ Play';
                        btn.className = 'play-btn';
                    } else {
                        isPlaying = true;
                        btn.textContent = '⏸️ Pause';
                        btn.className = 'play-btn pause-btn';
                        
                        animationInterval = setInterval(() => {
                            if (!simulationData) return;
                            
                            currentTimeStep++;
                            if (currentTimeStep >= simulationData.timesteps.length) {
                                currentTimeStep = 0;  // Loop animation
                            }
                            
                            updateVisualization(currentTimeStep);
                        }, animationSpeed);
                    }
                }
                
                function setTimeStep(value) {
                    if (isPlaying) {
                        toggleAnimation();  // Pause if playing
                    }
                    updateVisualization(parseInt(value));
                }
                
                function updateSpeed() {
                    const speed = parseInt(document.getElementById('speedControl').value);
                    animationSpeed = speed;
                    
                    if (isPlaying) {
                        clearInterval(animationInterval);
                        animationInterval = setInterval(() => {
                            if (!simulationData) return;
                            
                            currentTimeStep++;
                            if (currentTimeStep >= simulationData.timesteps.length) {
                                currentTimeStep = 0;
                            }
                            
                            updateVisualization(currentTimeStep);
                        }, animationSpeed);
                    }
                }
                
                function updateView() {
                    currentView = document.getElementById('viewControl').value;
                    updateVisualization(currentTimeStep);
                }
                
                // Initialize when page loads
                document.addEventListener('DOMContentLoaded', initializeVisualization);
            </script>
        </body>
        </html>
        """)

    @app.get("/api/simulation/animation-data")
    async def get_animation_data():
        """Get flood animation data for the interactive map"""
        if not sim_manager.current_simulation:
            # Try to run a quick 4-day simulation for animation
            sim_manager.current_simulation = FloodSimulation(
                start_date=datetime.now(),
                simulation_days=4
            )
            sim_manager.current_simulation.run_complete_simulation()
        
        simulation = sim_manager.current_simulation
        if not hasattr(simulation, 'precipitation_forecast') or not hasattr(simulation, 'water_depth'):
            raise HTTPException(status_code=404, detail="No animation data available - run simulation first")
        
        # Extract data for animation with flood movement tracking
        timesteps = []
        total_hours = min(96, len(simulation.water_depth))  # 4 days max
        
        # Bangalore region boundaries
        lat_min, lat_max = 12.8, 13.2
        lon_min, lon_max = 77.3, 77.8
        grid_size = simulation.grid_size
        
        # Track flood fronts and active flood zones
        previous_flooded = np.zeros((grid_size, grid_size))
        
        for hour in range(0, total_hours, 3):  # Every 3 hours for more detailed movement
            if hour < len(simulation.water_depth):
                current_time = simulation.start_date + timedelta(hours=hour)
                
                # Get current water depth and precipitation
                water_depth_2d = simulation.water_depth[hour]
                precipitation_2d = simulation.precipitation_forecast.precipitation[hour].values
                
                # Identify currently flooded areas (>2mm threshold)
                current_flooded = (water_depth_2d > 2).astype(int)
                
                # Calculate flood fronts (newly flooded areas)
                new_flood_areas = np.logical_and(current_flooded, ~previous_flooded.astype(bool))
                
                # Calculate flood movement vectors
                movement_vectors = []
                active_flood_zones = []
                flood_fronts = []
                
                # Generate flood movement data
                for i in range(1, grid_size - 1):
                    for j in range(1, grid_size - 1):
                        # Convert grid coordinates to lat/lon
                        lat = lat_min + (i / grid_size) * (lat_max - lat_min)
                        lon = lon_min + (j / grid_size) * (lon_max - lon_min)
                        
                        water_depth = water_depth_2d[i, j]
                        precip_intensity = precipitation_2d[i, j]
                        
                        # Active flood zones (significant water depth)
                        if water_depth > 5:
                            active_flood_zones.append({
                                'lat': lat,
                                'lon': lon,
                                'intensity': float(water_depth),
                                'type': 'severe' if water_depth > 20 else 'moderate' if water_depth > 10 else 'light'
                            })
                        
                        # Flood fronts (newly flooded areas)
                        if new_flood_areas[i, j]:
                            # Calculate movement direction by looking at surrounding areas
                            neighbors = [
                                (i-1, j-1), (i-1, j), (i-1, j+1),
                                (i, j-1),             (i, j+1),
                                (i+1, j-1), (i+1, j), (i+1, j+1)
                            ]
                            
                            # Find direction of flood propagation
                            max_neighbor_depth = 0
                            movement_dir = {'lat': 0, 'lon': 0}
                            
                            for ni, nj in neighbors:
                                if 0 <= ni < grid_size and 0 <= nj < grid_size:
                                    if previous_flooded[ni, nj] > max_neighbor_depth:
                                        max_neighbor_depth = previous_flooded[ni, nj]
                                        # Calculate movement direction
                                        movement_dir['lat'] = (ni - i) * 0.002  # Small movement step
                                        movement_dir['lon'] = (nj - j) * 0.002
                            
                            flood_fronts.append({
                                'lat': lat,
                                'lon': lon,
                                'intensity': float(water_depth),
                                'movement': movement_dir,
                                'age': 0  # New flood front
                            })
                        
                        # Precipitation zones (active weather systems)
                        if precip_intensity > 5:
                            # Calculate storm movement (simplified)
                            storm_movement = {
                                'lat': np.sin(hour * 0.1) * 0.001,  # Simulate storm movement
                                'lon': np.cos(hour * 0.1) * 0.001
                            }
                            
                            movement_vectors.append({
                                'lat': lat,
                                'lon': lon,
                                'intensity': float(precip_intensity),
                                'type': 'precipitation',
                                'movement': storm_movement
                            })
                
                # Calculate overall statistics
                max_water = float(np.max(water_depth_2d))
                flooded_cells = int(np.sum(water_depth_2d > 5))
                total_cells = water_depth_2d.size
                flooded_percent = (flooded_cells / total_cells) * 100
                max_precip = float(np.max(precipitation_2d))
                
                # Determine risk level and flood progression status
                if len(flood_fronts) > 50:
                    progression_status = "Rapidly Expanding"
                elif len(flood_fronts) > 20:
                    progression_status = "Expanding"
                elif len(active_flood_zones) > 100:
                    progression_status = "Stable High Risk"
                else:
                    progression_status = "Stable Low Risk"
                
                if max_water > 30 or max_precip > 20:
                    risk_level = "Extreme"
                elif max_water > 15 or max_precip > 10:
                    risk_level = "High"
                elif max_water > 5 or max_precip > 5:
                    risk_level = "Moderate"
                else:
                    risk_level = "Low"
                
                timestep_data = {
                    'time_info': {
                        'hour': hour,
                        'day': (hour // 24) + 1,
                        'datetime': current_time.strftime('%Y-%m-%d %H:%M')
                    },
                    'active_flood_zones': active_flood_zones,
                    'flood_fronts': flood_fronts,
                    'movement_vectors': movement_vectors,
                    'stats': {
                        'max_water_depth': max_water,
                        'flooded_area_percent': flooded_percent,
                        'max_precipitation': max_precip,
                        'risk_level': risk_level,
                        'active_zones': len(active_flood_zones),
                        'new_flood_areas': len(flood_fronts),
                        'progression_status': progression_status
                    }
                }
                
                timesteps.append(timestep_data)
                
                # Update previous flooded areas for next iteration
                previous_flooded = current_flooded.copy()
        
        return {
            'timesteps': timesteps,
            'simulation_info': {
                'start_date': simulation.start_date.isoformat(),
                'simulation_days': simulation.simulation_days,
                'grid_size': simulation.grid_size,
                'total_timesteps': len(timesteps)
            }
        }

# Function to integrate with main app
def setup_simulation_api(main_app: FastAPI):
    """Setup simulation routes in the main FastAPI app"""
    add_simulation_routes(main_app)
    
    # Add simulation link to main page
    @main_app.get("/", response_class=HTMLResponse)
    async def enhanced_root():
        """Enhanced main landing page with simulation link"""
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
                    .special { background: #dc3545; }
                    code { background: #f8f9fa; padding: 2px 6px; border-radius: 3px; }
                    .highlight { background: #fff3cd; border: 2px solid #ffc107; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🌊 Bangalore Flood Response System</h1>
                    <p>Advanced flood risk assessment and emergency response platform</p>
                </div>
                
                <div class="endpoint highlight">
                    <span class="method special">NEW</span>
                    <strong><a href="/simulation">🎯 /simulation</a></strong> - Interactive Flood Simulation Dashboard (7-day forecast)
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
                    <strong><a href="/api/simulation/daily-forecast">/api/simulation/daily-forecast</a></strong> - 7-day flood forecast
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
                    <span class="method post">POST</span>
                    <strong>/api/simulation/start</strong> - Start new flood simulation
                </div>
                
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <strong><a href="/health">/health</a></strong> - System health check
                </div>
                
                <p style="margin-top: 30px; color: #666;">
                    🎯 <strong>Quick Start:</strong> Visit <code>/simulation</code> for the 7-day flood progression forecast
                </p>
            </body>
        </html>
        """

if __name__ == "__main__":
    # For testing the simulation API independently
    app = FastAPI(title="Flood Simulation API")
    add_simulation_routes(app)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)