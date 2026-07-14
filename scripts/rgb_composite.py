
# Libraries
import os
import glob
import numpy as np
import xarray as xr
import rioxarrary
import h5py
import pandas as pd
import re

# GLOBAL VARIABLES
INPUT_DIR = r"C:\Users\letii\Desktop\NISAR\initial_test\GCOV_data"
OUTPUT_DIR = r"C:\Users\letii\Desktop\NISAR\initial_test\test_outputs"
GROUP_PATH = "/science/LSAR/GCOV/grids/frequencyA"

#### FUNCTIONS ###############################################

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

