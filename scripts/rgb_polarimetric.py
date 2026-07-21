"""
This script generates an RGB composite using the polarizations as:
- Red = Median(HH),
- Green = Median(HV),
- Blue = Ratio(HH/HV)
"""
# libraries and functions from other scripts
import os
import xarray as xr
import rioxarray
from nisar_change_detection import load_time_series, OUTPUT_DIR
from rgb_composite import normalize


def export_polarimetric_rgb(datacube, epsg_code):
  """
  Export a polarimetric RGB composite using median HH, median HV, and ratio HH/HV"""

  print("Calculating median HH (red)")
  red_raw = datacube["HHHH"].median(dim='time')
  print("Calculating median HV (green)")
  green_raw= datacube["HVHV"].median(dim='time')
  print("Calculating HH/HV (blue)")
  blue_raw = red_raw / green_raw.where(green_raw > 0, 1e-5) # prevents division by 0

  print("Normalizing bands")
  red_band=normalize(red_raw)
  green_band =normalize(green_raw)
  blue_band= normalize(blue_raw)
    
  print("Stacking bands")
  rgb_composite = xr.concat([red_band, green_band, blue_band], dim='band')
  rgb_composite = rgb_composite.assign_coords(band=[1, 2, 3])

  # initially all the bands were named 'HHHH' in ArcGIS, this solves it
  rgb_composite.name = "Polarimetric_Composite"
  rgb_composite.attrs["long_name"] = ["Median_HH", "Median_HV", "Ratio_HH/HV"]
  
  print("Computing composite")
  rgb_composite = rgb_composite.compute()
  rgb_composite = rgb_composite.fillna(0.0)

  output_filename = os.path.join(OUTPUT_DIR, "polarimetric_rgb_HH_HV_ratio.tif")
  if epsg_code:
     rgb_composite.rio.write_crs(f"EPSG:{epsg_code}", inplace=True)

  rgb_composite.rio.to_raster(output_filename)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # load the datacube
    datacube, epsg_code = load_time_series()
    # export the hybrid composite
    export_polarimetric_rgb(datacube, epsg_code)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
