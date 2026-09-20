# PEZA Economic Zones: Spatial Data Construction and Exploration

This repository constructs a spatial dataset of Philippine Economic Zone Authority (PEZA) economic zones (as of June 2024) and combines it with province-level demographic, infrastructure, and environmental indicators. The project demonstrates a reproducible workflow for integrating administrative, geospatial, and development datasets to create analysis-ready data for exploratory research on economic zones and local development contexts.

## Research Question

How are PEZA economic zones distributed across Philippine provinces, and how do provinces with and without economic zones differ in terms of population, infrastructure, environmental exposure, and access to services?

## Data Construction

The analysis pipeline:

- Geocodes PEZA economic zone addresses using the University of Chicago RCC-GIS geocoding service
- Links zones to Philippine administrative units using standardized administrative codes
- Integrates province-level indicators from HDX and HeiGIT, including population, flood exposure, facilities, rural population, and service access measures
- Produces analysis-ready datasets and a source audit documenting data provenance and limitations

The original PEZA dataset contains 603 economic zones. After removing failed geocodes, the final spatial dataset contains 589 successfully geocoded zones.

## Methods

The exploratory analysis includes:

- Descriptive comparisons between provinces with and without PEZA zones
- Summary statistics and correlation analysis
- Exploratory regression analysis

The analysis is descriptive and is not intended to estimate causal effects of economic zones. Economic zones are not randomly assigned, and observed differences may reflect pre-existing differences in infrastructure, population, and economic conditions.

## Software

- R
- sf
- tidyverse
- ggplot2

## Repository Structure

- `analysis/` contains data construction and exploratory analysis scripts
- `data/raw/` contains original source datasets
- `data/exports/` contains analysis-ready datasets and source documentation

## Outputs

The construction pipeline generates:

- `zones.csv` — geocoded PEZA economic zone dataset
- `analysis_units.csv` — province-level analysis dataset with zone indicators and covariates
- `sources.csv` — data source audit documenting origins, variables, limitations, and potential extensions

## Research Extensions

The constructed dataset could support future work evaluating how economic zone establishment relates to local economic outcomes. A potential extension would combine zone establishment dates with province-level outcomes to study changes over time using quasi-experimental methods.
