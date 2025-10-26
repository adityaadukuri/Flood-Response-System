#Step 6: Serve via FastAPI + Titiler
from fastapi import FastAPI
from titiler.core.factory import TilerFactory

app = FastAPI(title="Flood Digital Twin")
cog_tiler = TilerFactory()
app.include_router(cog_tiler.router, prefix="/flood")

@app.get("/")
def root():
    return {"message": "Flood Digital Twin API running", "tiles": "/flood/tiles/{z}/{x}/{y}"}

#run with:
# uvicorn app:app --reload

#Step 7: Interactive Visualization (Folium)
import folium

m = folium.Map(location=[13.0, 77.6], zoom_start=10)
folium.raster_layers.TileLayer(
    tiles="http://127.0.0.1:8000/flood/tiles/{z}/{x}/{y}?url=/path/to/flood_accum_cog.tif",
    attr="ERA5 Flood Twin",
    name="Flood Map"
).add_to(m)

folium.GeoJson(buildings, name="Buildings").add_to(m)
folium.LayerControl().add_to(m)
m.save("flood_map.html")