import rasterio
import matplotlib.pyplot as plt

# Open the .tif file
tif_path = "flood_accum.tif"   
with rasterio.open(tif_path) as src:
    print(src.profile)        # metadata (CRS, shape, etc.)
    image = src.read(1)       # read the first band

# Plot it
plt.imshow(image, cmap='terrain')  # or 'Blues', 'viridis' etc.
plt.colorbar(label='Elevation (m)')
plt.title("DEM (Digital Elevation Model)")
plt.show()