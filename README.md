# NISAR GCOV Product Analysis for Crop Identification

## Polarizations:
A **Horizontal-Horizontal** (HH) polarization (co-polarized) means that the radar both transmits and receives horizontally polarized waveforms.

A **Horizontal-Vertical** (HV) polarization (cross-polarized) means that the radar transmits a horizontally polarized waveform but receives a vertically polarized return.

* **HHHH**: Sensitive to the roughness of the ground and the dielectric constant of the soil (linked to soil moisture). Good for detecting water beneath canopies. When water is below vegetation, the radar wave scatters off the smooth water surface and then bounces off vertically emergent vegetation back to the radar. This creates a highly reflective 'double bounce' scatter that dominates the HH channel.

* **HVHV**: As the radar waves penetrate a canopy, they interact with the structure of the branches, stems, and leaves, depolarizing the signal and creating a strong vertical return. This is 'volume scattering', which is used to estimate above-ground biomass and detect structural disturbances (deforestation, wildfires).

Both together:

Distinguish between dense vegetation (strong HV) and bare surface.
The HH/HV ratio is used to distinguish open water from inundated vegetation.
Observing how much they change over time allows us to identify crop areas (planting, growing, and cropping phases).

## RGB Composites
### Multi-Temporal
These are made by taking three dates (initial, middle, and final) and assigning them bands (red, green, blue) respectively.
They are done independently for each polarization because HH tracks the surface and HV tracks the canopy.

The final product should be interpreted as:
* **White/Gray/Black:** no change happened among the three dates;
* **Solid color (red, blue, or green):** the signal was the highest on the respective date and lowest in the other dates. Example: If a region shows solid red, it means that the signal was highest on day 1 and low on days 2 and 3.
* **Composite colors:**
  * Yellow (red + green): high backscatter on days 1 and 2, but dropped on day 3.
  * Cyan (green + blue): low backscatter on day 1, but high on days 2 and 3.
  * Magenta (red + blue): high backscatter on days 1 and 3, but dropped in the middle on day 2.
