# NISAR GCOV Product Analysis for Crop Identification

## RGB Composites
These are made by taking three dates (initial, middle, and final) and assigning them bands (red, green, blue) respectively.
The final product should be interpreted as:
* **White/Gray/Black:** no change happened among the three dates;
* **Solid color (red, blue, or green):** the signal was the highest on the respective date and lowest in the other dates. Example: If a region shows solid red, it means that the signal was highest on day 1 and low on days 2 and 3.
* **Composite colors:**
  * Yellow (red + green): high backscatter on days 1 and 2, but dropped on day 3.
  * Cyan (green + blue): low backscatter on day 1, but high on days 2 and 3.
  * Magenta (red + blue): high backscatter on days 1 and 3, but dropped in the middle on day 2.
