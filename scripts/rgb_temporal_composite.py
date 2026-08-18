"""
This script generates a multitemporal RGB composite GeoTIFF from a time series of SAR data (for each polarization).
It requires importing the load_time_series function and OUTPUT_DIR from nisar_change_detection.py
"""

# Libraries
import os
import xarray as xr
import rioxarray

#import the load_time_series function and OUTPUT_DIR from nisar_change_detection.py
from nisar_change_detection import load_time_series, OUTPUT_DIR

########### FUNCTIONS ###############################################

def normalize(da):
    """Calculates 2nd and 98th percentiles and applies normalization.
    This uses dask to avoid using too much memory.
    This normalization is important because it stretches the contrast of the image, 
    making it easier to see changes in the RGB composite."""

    vmin =da.quantile(0.02).compute()
    vmax =da.quantile(0.98).compute()
    
    normalized =(da-vmin)/(vmax- vmin)
    return normalized.clip(0, 1)


def export_rgb_composite(cube, polarization, epsg_code):
    """Exports a 3-band RGB composite GeoTIFF for a given polarization.
    The RGB composite is created by taking the first, middle, 
    and last time steps of the time series and normalizing them to enhance contrast.
    The resulting GeoTIFF is saved to the OUTPUT_DIR with a filename indicating the polarization used"""

    pol_data = cube[polarization] # gets the data for the given polarization
    
    # this ensures taking 3 time steps: first, middle, and last
    t_len =len(pol_data.time)
    t0_idx, t1_idx,t2_idx=0, t_len // 2, t_len - 1
    
    # the red is the first date, the green is the middle date, and the blue is the last date
    print(f"RED  (Date 1): {str(pol_data.time[t0_idx].values)[:10]}")
    print(f"GREEN (Date 2): {str(pol_data.time[t1_idx].values)[:10]}")
    print(f"BLUE  (Date 3): {str(pol_data.time[t2_idx].values)[:10]}")

    # this normalizes the data to enhance contrast and avoid saturation in the RGB composite
    red_band= normalize(pol_data.isel(time=t0_idx))
    green_band= normalize(pol_data.isel(time=t1_idx))
    blue_band =normalize(pol_data.isel(time=t2_idx))
    
    # this concatenates the three bands into a single xarray DataArray with a new dimension 'band'
    # the bands are assigned values 1, 2, and 3 for red, green, and blue respectively
    # xr.contact already has pre-defined bands
    rgb_composite= xr.concat([red_band, green_band, blue_band], dim='band')
    rgb_composite= rgb_composite.assign_coords(band=[1, 2, 3])
    
    rgb_composite =rgb_composite.compute() # compute using dask
    rgb_composite =rgb_composite.fillna(0.0) # this avoids non-values
    
    output_filename = os.path.join(OUTPUT_DIR, f"multitemporal_rgb_{polarization}.tif")

    # this writes the EPSG code to the GeoTIFF metadata - important when working in GIS
    if epsg_code:
        rgb_composite.rio.write_crs(f"EPSG:{epsg_code}", inplace=True)
 
    rgb_composite.rio.to_raster(output_filename) # this saves the composite as a GeoTIFF

    print("Files saved successfully.")

########### MAIN ###############################################

def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    cube, epsg_code=load_time_series()
    # create two RGB composites for the two polarizations: HVHV and HHHH
    export_rgb_composite(cube, "HVHV", epsg_code)
    export_rgb_composite(cube, "HHHH", epsg_code)



if __name__ == "__main__":
    main()

