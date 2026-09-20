## ============================================================
## PEZA Economic Zones: Spatial Data Construction
## Nina
## ============================================================

rm(list=ls())

library(sf)
library(tidyverse)

# =============================================================
# 1. Construct PEZA zone data
# =============================================================

# read in base dataset w/ admin pcodes (constructed w/ Claude, see memo)
peza_full = read_csv("../data/raw/peza_with_pcodes.csv")

# geocoded coordinates from UChicago RCC-GIS service
geocodes = read_csv("../data/raw/peza_geocoded.csv")
colnames(geocodes)[10] = "MATCH_SCORE"

# drop zeros -- these are failed geocodes
zeros_dropped = geocodes[geocodes$MATCH_SCORE!=0,]
# 603 -> 589; lowest non-zero match score is 75, so threshold is fine

# convert to sf points, WGS84
geocodes_sf <- st_as_sf(zeros_dropped, coords = c("Longitude","Latitude"), crs = 4326)

# keep ID + geometry only for clean merge
geocodes_only = geocodes_sf[c("ID", "geometry")]

# merge attributes onto geocoded points
peza_merged = merge(peza_full, geocodes_only, by="ID")

# fix column name for consistency w/ HDX pcode convention
colnames(peza_merged)[colnames(peza_merged) == "admin2_pcode"] = "ADM2_PCODE"

# validation: track expected geocoded count
stopifnot(nrow(peza_merged) == nrow(zeros_dropped))
stopifnot(!anyDuplicated(peza_merged$ID))

# add longitude and latitude columns
# peza_merged already has everything; just add lon/lat columns from the sf geometry
peza_merged_coords = peza_merged %>%
  mutate(
    lon = st_coordinates(geometry)[,1],
    lat = st_coordinates(geometry)[,2]
  ) %>%
  st_drop_geometry()


# =============================================================
# 2. Merge province-level covariates
# =============================================================

# population projections from HDX COD-PS
population = read_csv("../data/raw/phl_admpop2025.csv")
stopifnot(!anyDuplicated(population$ADM2_PCODE))

# development indicators -- all from HeiGIT via HDX
# validate uniqueness of ADM2 keys before merging
flood_exp = read_csv("../data/raw/PHL_ADM2_flood_exposure.csv")
stopifnot(!anyDuplicated(flood_exp$ADM2_PCODE))

facilities = read_csv("../data/raw/PHL_ADM2_facilities.csv")
stopifnot(!anyDuplicated(facilities$ADM2_PCODE))

rural = read_csv("../data/raw/PHL_ADM2_rural_population.csv")
stopifnot(!anyDuplicated(rural$ADM2_PCODE))

resource_access = read_csv("../data/raw/PHL_ADM2_access.csv")
stopifnot(!anyDuplicated(resource_access$ADM2_PCODE))

# HeiGIT pcodes are shorter -- need to pad + trim to match HDX format
# e.g. "PH0308" -> pad -> "PH030800000" -> trim 5th char -> "PH03080000"
fix_heigit_pcode = function(df) {
  df$ADM2_PCODE = paste0(df$ADM2_PCODE, "00000")
  df$ADM2_PCODE = sub("^(.{4}).", "\\1", df$ADM2_PCODE)
  return(df)
}

flood_exp = fix_heigit_pcode(flood_exp)
facilities = fix_heigit_pcode(facilities)
rural = fix_heigit_pcode(rural)
resource_access = fix_heigit_pcode(resource_access)

# validation: attach province characteristics to PEZA zones without changing observation count
zones = peza_merged %>%
  left_join(population, by = "ADM2_PCODE") %>%
  left_join(flood_exp, by = "ADM2_PCODE") %>%
  left_join(facilities, by = "ADM2_PCODE") %>%
  left_join(rural, by = "ADM2_PCODE") %>%
  left_join(resource_access, by = "ADM2_PCODE")

stopifnot(nrow(zones) == nrow(peza_merged))

# province-level: each row = one province
province_data = population %>%
  left_join(flood_exp, by="ADM2_PCODE") %>%
  left_join(facilities, by="ADM2_PCODE") %>%
  left_join(rural, by="ADM2_PCODE") %>%
  left_join(resource_access, by="ADM2_PCODE")

stopifnot(nrow(province_data) == nrow(population))


# =============================================================
# 3. Create analysis-ready province dataset
# =============================================================

# count zones per province
zone_counts = peza_merged %>%
  group_by(ADM2_PCODE) %>%
  summarise(n_zones = n(), .groups = "drop")

# clean up duplicate pcode cols from HeiGIT merges before joining
province_data = province_data %>% select(-starts_with("ADM_PCODE"))

# build analysis_units: one row per province, w/ zone indicator
analysis_units = province_data %>%
  left_join(zone_counts, by = "ADM2_PCODE") %>%
  mutate(
    n_zones  = replace_na(n_zones, 0),
    has_zone = as.integer(n_zones > 0)
  )

# ensure no unintended duplication after zone aggregation merge
stopifnot(nrow(analysis_units) == nrow(province_data))


# =============================================================
# 4. Construct source audit table
# =============================================================

sources = tibble(
  source_name = c(
    "PEZA List of Economic Zones (as of 30 June 2024)",
    "UChicago RCC-GIS Geocoding Service",
    "HDX Philippines Administrative Boundaries (COD-AB)",
    "HDX Philippines Population Projections (COD-PS)",
    "HeiGIT Flood Exposure (ADM2)",
    "HeiGIT Health and Education Facilities (ADM2)",
    "HeiGIT Rural Population (ADM2)",
    "HeiGIT Resource Access (ADM2)",
    "BIR Monthly Internal Revenue Collections by Province (2016-2024)",
    "Wikipedia: List of Special Economic Zones in the Philippines",
    "Philippine Statistics Authority"
  ),
  link = c(
    "https://www.peza.gov.ph",
    "https://gis.rcc.uchicago.edu",
    "https://data.humdata.org/dataset/cod-ab-phl",
    "https://data.humdata.org/dataset/cod-ps-phl",
    "https://data.humdata.org/dataset/philippines---risk-assessment-indicators",
    "https://data.humdata.org/dataset/philippines---risk-assessment-indicators",
    "https://data.humdata.org/dataset/philippines---risk-assessment-indicators",
    "https://data.humdata.org/dataset/philippines---risk-assessment-indicators",
    "https://data.bettergov.ph/datasets/8/resources/27",
    "https://en.wikipedia.org/wiki/List_of_special_economic_zones_in_the_Philippines",
    "https://psa.gov.ph"
  ),
  type = c(
    "government list (XLS)",
    "geocoding API",
    "XLSX gazetteer + shapefile",
    "CSV/XLSX",
    "CSV",
    "CSV",
    "CSV",
    "CSV",
    "CSV",
    "wiki table",
    "government portal"
  ),
  raw_download_available = c(
    "yes", "yes (output CSV)", "yes", "yes", "yes", "yes", "yes", "yes",
    "yes", "no (scraping required)", "partial"
  ),
  variables_used = c(
    "zone name, location, developer, area (sqm), region, zone type, operating status",
    "latitude, longitude, match score per zone address",
    "admin3 (municipality) names and pcodes, admin2 (province) names and pcodes",
    "total population by sex and age group, province level, 2022-2025 projections",
    "population exposed to flooding at return periods 10/50/100/500yr by demographic group",
    "counts of hospitals, primary healthcare facilities, education facilities per province",
    "rural population counts by demographic group, rural population share per province",
    "population within 5/10/20km of education, within 30min/1h/2h of hospitals and primary healthcare",
    "monthly tax revenue by region and province, CY 2016-2024",
    "zone names, locations, developers, region, area",
    "GDP by region, population census, building permits, labour force surveys"
  ),
  credibility = c(
    "official Philippine government agency administering all economic zones",
    "University of Chicago institutional Esri geocoder",
    "OCHA Common Operational Dataset sourced from PSA and NAMRIA",
    "UNFPA-validated projections based on PSA 2015 Census",
    "HeiGIT / Heidelberg Institute for Geoinformation Technology; established flood modelling",
    "HeiGIT; facility locations likely sourced from OpenStreetMap",
    "HeiGIT; based on population distribution models",
    "HeiGIT; travel time estimates based on road network analysis",
    "Bureau of Internal Revenue via Open Data Philippines; official government tax data",
    "community-maintained but well-sourced from PEZA and government proclamations",
    "official national statistics office"
  ),
  limitation = c(
    "no coordinates; addresses are text strings requiring geocoding; no explicit establishment year",
    "14 zones returned 0 match score (dropped); some rural addresses may be imprecise",
    "used gazetteer for name-matching rather than spatial join; some municipality names differ from PEZA conventions",
    "projections not actuals; province-level aggregation masks within-province variation",
    "exposure estimates depend on flood model assumptions; 30cm depth threshold",
    "OSM coverage varies; rural facilities may be underrepresented",
    "rural/urban classification depends on model resolution",
    "travel time models assume normal conditions; actual access affected by traffic and geography",
    "province-level aggregation; does not separate zone-specific tax from general provincial revenue",
    "may be outdated or incomplete relative to official PEZA list",
    "most granular data in PDF or requires formal data request"
  ),
  next_step = c(
    "geocode addresses via RCC-GIS; extract proclamation dates from PEZA website per zone",
    "spot-check low-scoring geocodes against Google Maps; manually correct outliers",
    "use shapefile for point-in-polygon join if shapefile reads successfully",
    "link to 2020 Census actuals at municipality level for finer resolution",
    "cross-reference with PAGASA historical flood data",
    "validate against DOH National Health Facility Registry",
    "compare with PSA urbanisation statistics",
    "validate with ground-truth travel surveys if available",
    "use as outcome variable in staggered DiD linking zone establishment to provincial tax revenue",
    "use as supplementary cross-check only",
    "submit formal data request for municipality-level GDP and building permits"
  )
)


# =============================================================
# 5. Export datasets and audit
# =============================================================

write_csv(peza_merged_coords, "../data/exports/zones.csv")

write_csv(analysis_units, "../data/exports/analysis_units.csv")

write_csv(sources, "../data/exports/sources.csv")
