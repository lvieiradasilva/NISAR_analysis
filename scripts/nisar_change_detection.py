#!/usr/bin/env python3
"""
NISAR SAR Dual-Polarization Change Detection Pipeline
The goal of this script is to process a time-series of NISAR SAR data and generate a change detection mask 
based on the coefficient of variation (CV) of the HV and HH polarization channels.
The script performs the following steps:
1. Load the time-series data from valid HDF5 files in the specified input directory.
2. Compute the CV and variance for both HV and HH polarization channels.
3. Generate a combined change detection mask based on a dual threshold classifier applied to the CV maps of HV and HH polarizations.
4. Export the combined mask to a GeoTIFF file.

Developed by Leticia Vieira using the NISAR Cookbook as a reference.
"""

import os
import glob
import argparse
import subprocess
import numpy as np
import xarray as xr
import rioxarray
import h5py
import pandas as pd
import re
import geopandas as gpd
from shapely.geometry import mapping
import warnings

warnings.filterwarnings('ignore') # ignore rioxarray warnings

## GLOBAL VARIABLES
INPUT_DIR = r"C:\Users\letii\Desktop\NISAR\initial_test\GCOV_data"
OUTPUT_DIR = r"C:\Users\letii\Desktop\NISAR\initial_test\test_outputs"
STUDY_AREA = r"C:\Users\letii\Desktop\NISAR\araripe_plateau\apa_chapada_araripe\study_Area_Clip.shp" # clipping shapefile for the study area
GROUP_PATH = "/science/LSAR/GCOV/grids/frequencyA" #according to how NISAR data is structured in HDF5
CACHE_FILE = os.path.join(OUTPUT_DIR, 'clipped_datacube.nc') # this is the netcdf file path
#################### DATA SETUP FUNCTIONS ##########################################################
def validate_hdf5_files():
    """
    Validates the presence of .h5 files in the input directory and checks for corruption.
    Returns a list of valid file paths.
    """

    search_path = os.path.join(INPUT_DIR, "*.h5")
    hdf5_file_paths = sorted(glob.glob(search_path))

    valid_files = [] #list to store the valid files
    for file in hdf5_file_paths:
        try:
            with h5py.File(file, 'r') as f:
                valid_files.append(file)
        # if cannot open, the file is corrupted, so we skip it and print a warning
        except OSError:
            print(f"CORRUPTED FILE DETECTED: {os.path.basename(file)}")

    if not valid_files:
        raise FileNotFoundError(f"No valid .h5 files found in {INPUT_DIR}")
    
    return valid_files

def extract_timestamps(file_paths):
    """ Extracts timestamps from the filenames of the provided HDF5 file paths.
    Assumes filenames contain timestamps in the format YYYYMMDDTHHMMSS (as described in NISAR documentation)."""

    times =[] #list to store the extracted timestamps
    #loop through the file paths and extract timestamps using regex l
    for path in file_paths:
        match= re.search(r'\d{8}T\d{6}', path) # search for the timestamp pattern in the filename
        if match:
            times.append(pd.to_datetime(match.group(), format ='%Y%m%dT%H%M%S'))
        else:
            raise ValueError(f"Could not parse date from {path}")
    return times


def load_time_series():
    """ Loads the time-series data from valid HDF5 files, 
    ensuring proper dimension naming and coordinate mapping.
    Clips the data early and caches the output as a NetCDF file to speed up processing.
    Returns an xarray Dataset representing the time-series cube and the native EPSG code.
    """
    os.makedir(OUTPUT_DIR, exist_ok=True)

    # if the file already exists, do this:
    if os.path.exists(CACHE_FILE):
        print(f'Found cached file. Loading {os.path.basename(CACHE_FILE)}')
        cube= xr.open_dataset(CACHE_FILE, chunks={'x': 1024, 'y': 1024})
        epsg_code= cube.attrs.get('epsg_code') # get the saved epsg code
        cube= cube.rio.set_spatial_dims(x_dim='x', y_dim='y') # tells rioxarray the spatial dimensions
        cube.rio.write_crs(f'EPSG:{epsg_code}', inplace=True)
        
        return cube, epsg_code
    
    valid_files = validate_hdf5_files() # get the valid files from the input directory

    print(f"Located {len(valid_files)} valid NISAR files.")

    times=extract_timestamps(valid_files) # get the timestamps from the valid files
    
    datasets =[]
    epsg_code =None
    gdf =gdp.read_files(STUDY_AREA) # use geopandas to read the study area
    
    # loop through the valid files and open them as xarray datasets, 
    # ensuring proper dimension naming and coordinate mapping
    for file_path in valid_files:
        print(f'Loading and clipping:{os.path.basename(file_path)}')
        ds =xr.open_dataset(
            file_path, 
            engine="h5netcdf", 
            group =GROUP_PATH, 
            phony_dims="sort" 
        )
        
        #get the native EPSG projection code from the HDF5 metadata
        # do it only once - all files should have the same projection
        if epsg_code is None and 'projection' in ds:
            epsg_code= int(ds['projection'].values.item()) #gets tthe epsg code and converts to an integer
            gdf = gdf.to_crs(f'EPSG:{epsg_code}')
        
        # rename dimensions to spatial dimensions (x and y) for georeferencing consistency
        dims = list(ds.dims)
        if len(dims) >= 2 and 'y' not in dims and 'x' not in dims:
            ds = ds.rename({dims[0]: 'y', dims[1]: 'x'})
            
        # assign coordinates based on the name they have in the dataset
        if 'yCoordinates' in ds and 'xCoordinates' in ds:
            ds = ds.assign_coords(y=ds['yCoordinates'], x=ds['xCoordinates'])

        # this keeps only the spatial variables (x and y) from the ds
        spatial_vars = [var for var in ds.data_vars if 'x' in ds[var].dims]
        ds_spatial=ds[spatial_vars]
        ds_spatial= ds_spatial.rio.set_spatial_dims(x_dim='x', y_dim='y')
        ds_spatial.rio.write_crs(f'EPSG:{epsg_code}', inplace=True)

        # clip the ds to the shapefile of the study area to optimize calculations
        ds_clipped= ds_spatial.rio.clip(gdf.geometry.apply(mapping), gdf.crs, drop=True)
        ds_clipped = ds_clipped.chunk({'y':1024, 'x':1024}) # chunked daset to save memory

        datasets.append(ds_clipped)

    # now that all the datasets are loaded, assign a new time dim based on the extracted timestamp
    for i in range(len(datasets)):
        datasets[i]=datasets[i].assign_coords(time =times[i])
        
    print("Stacking datasets into a datacube")

    # concatenate along the time dimension and sort by time including projection code
    final_cube = xr.concat(datasets, dim='time').sortby('time')
    final_cube.attrs['epsg_code']=epsg_code
    final_cube.to_netcdf(CACHE_FILE, engine='h5netcdf')
    print(f'NetCDF file saved: {CACHE_FILE}')
    
    return final_cube, epsg_code

################### COMPUTATION FUNCTIONS ##########################################################

def compute_metrics(time_series_cube, polarization, sample_step=50):
    """ Computes the coefficient of variation (CV) and variance for the specified polarization channel.
    Returns a 'lazy' CV map: a sampled CV array, and a sampled variance array for plotting"""

    print(f"Extracting polarization:\n{polarization}")

    pol_data = time_series_cube[polarization]
    
    mean_map = pol_data.mean(dim='time')
    var_map =pol_data.var(dim='time')
    std_map= pol_data.std(dim='time')
    cv_lazy =std_map / xr.where(mean_map != 0, mean_map,np.nan) #avoids division by zero
    
    # this is the sampled version of the CV and variance maps for plotting purposes
    cv_sample=cv_lazy[::sample_step, ::sample_step].compute().values.ravel() #gets the values and flattens the array
    cv_sample = np.asarray(cv_sample[np.isfinite(cv_sample)], dtype=np.float64) #make sure the array is finite and convert to float64
    
    # same thing as above but for variance
    var_sample= var_map[::sample_step, ::sample_step].compute().values.ravel()
    var_sample= np.asarray(var_sample[np.isfinite(var_sample)], dtype=np.float64)
    
    return cv_lazy,cv_sample,var_sample

def generate_combined_mask(cv_hv_lazy, cv_hh_lazy, cv_hv_sample, cv_hh_sample, percentage_cutoff):
    """ Generates a combined mask based on the dual threshold classifier applied to the CV maps of HV and HH polarizations.
    Returns a combined mask where:
    - 0: No change detected
    - 1: Change detected in HH
    - 2: Change detected in HV
    - 3: Change detected in both
    """

    #calculate the thresholds for HV and HH based on the specified percentage cutoff
    thresh_hv = np.percentile(cv_hv_sample, 100 - percentage_cutoff)
    thresh_hh = np.percentile(cv_hh_sample, 100 - percentage_cutoff)

    print(f"HV Threshold: {thresh_hv:.4f} | HH Threshold: {thresh_hh:.4f}")
    
    # create binary masks for HV and HH based on the thresholds
    # in these individual masks, 1 indicates change detected, and 0 indicates no change
    mask_hv =(cv_hv_lazy >= thresh_hv).astype('uint8')
    mask_hh =(cv_hh_lazy >= thresh_hh).astype('uint8')
    
    # this is the combined mask, the hv polarization is multiplied by 2 to differentiate it from the 
    # hh polarization in the combined mask
    combined_mask = mask_hh + (mask_hv * 2)
    
    # handle NaN values in the CV maps by setting the corresponding pixels in the combined mask to 255 (nodata)
    #also make it uint8 to save space and be compatible with geotiff export
    combined_mask =xr.where(np.isnan(cv_hv_lazy) | np.isnan(cv_hh_lazy), 255,combined_mask).astype('uint8')

    return combined_mask

def export_to_geotiff(mask, epsg_code, output_filepath):
    """ Exports the combined mask to a GeoTIFF file with the specified EPSG code."""
    
    #use the epsg code obtained
    if epsg_code:
        mask.rio.write_crs(f"EPSG:{epsg_code}", inplace=True) 

    #handles the nodata value and export to geotiff with tiling and windowed writing for efficiency    
    mask.rio.write_nodata(255, encoded=True, inplace=True)
    mask.rio.to_raster(output_filepath, tiled=True, windowed=True, lock=True, dtype="uint8")

    print("GeoTIFF Export complete!") 

#################### MAIN FUNCTION ##########################################################

def main():

    parser = argparse.ArgumentParser() # helpful for command line execution and parameter passing
    #the default threshold is set to 5% for the dual threshold classifier as in the cookbook
    parser.add_argument("--threshold", type=float, default=5)
    args = parser.parse_args()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        #load the time series data and get the native EPSG code
        cube, native_epsg =load_time_series()
        
        #calculate metrics for both polarizations, returning cv maps and sampled arrays for plotting
        cv_hv_lazy,cv_hv_sample,var_hv_sample= compute_metrics(cube, "HVHV")
        cv_hh_lazy,cv_hh_sample,var_hh_sample= compute_metrics(cube, "HHHH")
        
        #this will store the sampled metrics in a npz file for the plotting script to use
        npz_file= os.path.join(OUTPUT_DIR, "plot_samples.npz")
        np.savez(npz_file, cv_hv=cv_hv_sample, var_hv=var_hv_sample, cv_hh=cv_hh_sample, var_hh=var_hh_sample)
        
        # Make the combined mask
        combined_mask = generate_combined_mask(cv_hv_lazy, cv_hh_lazy, cv_hv_sample, cv_hh_sample, args.threshold)
        
        output_filename= os.path.join(OUTPUT_DIR, f"combined_crop_mask.tif")

        #export the combined mask to a GeoTIFF file that can be used in GIS
        export_to_geotiff(combined_mask, native_epsg, output_filename)
        
        # call the plotting script to generate plots based on the sampled metrics
        subprocess.run(["python", "generate_plots.py", "--npz", npz_file, "--out", OUTPUT_DIR])
        
        print("\nScript finished successfully.")
        
    except Exception as e:
        import traceback
        print(f"Script failed with error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
