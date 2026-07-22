"""
This scripts generates an RGB composite using a hybrid technique that combines:
- Red = Median(HH), representing bare surface
- Green = Median(HV), representing vegetation
- Blue = Standard Deviation(HV), representing texture/change of vegetation

The median was taken among the available time series.
"""

import os
import xarray as xr
import rioxarray

# get functions and data from main scripts and rgb_composite.py
from nisar_change_detection import load_time_series, clip_cube_to_shapefile, OUTPUT_DIR, STUDY_AREA
from rgb_composite import normalize

def export_hybrid_rgb(datacube, epsg_code):
    """
    Export a hybrid RGB composite using median HH, median HV, and standard deviation HV."""

    print("Calculating median HH (red)")
    red_raw =datacube["HHHH"].median(dim='time')
    print("Calculating median HV (green)")
    green_raw= datacube["HVHV"].median(dim ='time')
    print("Calculating standard deviation HV (blue)")
    blue_raw =datacube["HVHV"].std(dim ='time')
    
    print("Normalizing bands")
    red_band=normalize(red_raw)
    green_band =normalize(green_raw)
    blue_band= normalize(blue_raw)
    
    print("Stacking bands")
    rgb_composite= xr.concat([red_band, green_band, blue_band], dim ='band')
    rgb_composite= rgb_composite.assign_coords(band= [1, 2, 3])
    
    print("Computing composite")
    rgb_composite =rgb_composite.compute()
    rgb_composite =rgb_composite.fillna(0.0)
    
    output_filename =os.path.join(OUTPUT_DIR, "hybrid_rgb_medHH_medHV_stdHV.tif")
    if epsg_code:
        rgb_composite.rio.write_crs(f"EPSG:{epsg_code}", inplace =True)
        
    rgb_composite.rio.to_raster(output_filename)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    #load the datacube
    datacube, epsg_code =load_time_series()
    datacube = clip_cube_to_shapefile(datacube, STUDY_AREA, epsg_code=32724) # clip the cube to the study area using the shapefile
    # export the hybrid composite
    export_hybrid_rgb(datacube, epsg_code)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
