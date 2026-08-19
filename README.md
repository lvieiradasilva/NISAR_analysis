# NISAR GCOV Product Analysis for Crop Identification
Part of the code developed here was based on the code present in the [NISAR Cookbook](https://github.com/ASFOpenSARlab/NISAR_Cookbook/tree/main).

## Polarizations:
A **Horizontal-Horizontal** (HH) polarization (co-polarized) means that the radar both transmits and receives horizontally polarized waveforms.

A **Horizontal-Vertical** (HV) polarization (cross-polarized) means that the radar transmits a horizontally polarized waveform but receives a vertically polarized return.

* **HHHH**: Sensitive to the roughness of the ground and the dielectric constant of the soil (linked to soil moisture). Good for detecting water beneath canopies. When water is below vegetation, the radar wave scatters off the smooth water surface and then bounces off vertically emergent vegetation back to the radar. This creates a highly reflective 'double bounce' scatter that dominates the HH channel.

* **HVHV**: As the radar waves penetrate a canopy, they interact with the structure of the branches, stems, and leaves, depolarizing the signal and creating a strong vertical return. This is 'volume scattering', which is used to estimate above-ground biomass and detect structural disturbances (deforestation, wildfires).

Both together:

Distinguish between dense vegetation (strong HV) and bare surface.
The HH/HV ratio is used to distinguish open water from inundated vegetation.
Observing how much they change over time allows us to identify crop areas (planting, growing, and cropping phases).

## Crop/Non-Crop Mask
This pipeline identifies and extracts active agricultural boundaries using multi-temporal SAR backscatter variability.
1. Active croplands are identified using the Coefficient of Variation (CV) to measure temporal backscatter dynamics. The CV is calculated for both HH and HV polarizations as the standard deviation divided by the temporal mean:

$$CV = \frac{\sigma}{\mu}$$

2. Following the NISAR cookbook standards, a 5% cutoff threshold was applied to the CV arrays. The resulting mask isolates high-variation pixels into three distinct classes:

* HV-only change (volume scattering variation)
* HH-only change (surface roughness variation)
* Dual-polarization change (highest probability of active cropping)

3. The classified array was exported as a GeoTIFF and processed in ArcGIS Pro to generate clean vector geometries:

* **Reclassification:** The 3-class raster was collapsed into a binary crop / non-crop mask.
* **Majority Filter:** Was applied to reduce SAR speckle and bridge internal field seams (Parameters: Number of Neighbors = 8, Replacement Threshold = Half).
* **Raster to Polygon:** The smoothed binary mask was converted into discrete vector features.
  
4. Polygons were filtered by size. Features with an area $\ge 20 \text{ ha}$ were classified as large-scale agribusiness (mapped in orange), while smaller geometries were classified as smallholder agriculture (mapped in blue).


## RGB Composites
### Multi-Temporal
These are made by taking three dates (initial, middle, and final) and assigning them bands (red, green, blue) respectively.
They are done independently for each polarization because HH tracks the surface and HV tracks the canopy.

The final product should be interpreted as:
* **White/Gray/Black:** no change happened among the three dates;
* **Solid color (red, blue, or green):** the signal was the highest on the respective date and lowest on the other dates. Example: If a region shows solid red, it means that the signal was highest on day 1 and low on days 2 and 3.
* **Composite colors:**
  * Yellow (red + green): high backscatter on days 1 and 2, but dropped on day 3.
  * Cyan (green + blue): low backscatter on day 1, but high on days 2 and 3.
  * Magenta (red + blue): high backscatter on days 1 and 3, but dropped in the middle on day 2.

### Polarimetric
This is done by taking the statistics of the available data and combining them as follows:
* **Red:** median of HH polarization - represents bare surface
* **Green:** median of HV - represents vegetated area
* **Blue:** ratio HH/HV.

This tells about the physical geometry of the landscape.
* **Green:** stable vegetation;
* **Red/Magenta:** permanent rough surfaces
* **Blue:** surface scattering


### Hybrid
This RGB composite is made by taking the statistics of the available data and combining them as follows:
* **Red:** median of HH polarization - represents bare surface
* **Green:** median of HV - represents vegetated area
* **Blue:** standard deviation of HV - detects changes in the vegetated area.

This approach was followed according to [this NASA example](https://science.nasa.gov/earth/earth-observatory/painting-the-growing-season-in-the-maize-triangle/.)

The final product should be interpreted as:
* **Blue:** this signals active agricultural fields. A high standard deviation means the volume of the vegetation is changing over time.
* **Green:** this represents permanent vegetation (high median HV but low standard deviation HV)
*  **Red:** this represents bare ground given the high median HH across all dates.
*  **Black:** low returns across all metrics, which can mean smooth surfaces (example: water).

