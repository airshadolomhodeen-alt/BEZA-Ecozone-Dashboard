## ============================================================
## PEZA Economic Zones: Descriptive Analysis
## Nina
## ============================================================

library(ggplot2)
library(tidyverse)

# =============================================================
# 1. Read in and summarize analysis-ready data
# =============================================================

analysis_units <- read_csv("../data/exports/analysis_units.csv")

# Descriptive comparison table

comparison = analysis_units %>%
  group_by(has_zone) %>%
  summarise(
    n_provinces             = n(),
    mean_total_pop          = mean(T_TL, na.rm=TRUE),
    mean_hospitals          = mean(hospitals_count, na.rm=TRUE),
    mean_primary_hc         = mean(primary_healthcare_count, na.rm=TRUE),
    mean_education          = mean(education_count, na.rm=TRUE),
    mean_rural_pct          = mean(rural_pop_perc, na.rm=TRUE),
    mean_flood_exp_rp100    = mean(RP100_pop_u15_30cm, na.rm=TRUE),
    mean_hosp_access_1h     = mean(access_pop_hospitals_1h, na.rm=TRUE),
    .groups = "drop"
  ) %>%
  mutate(has_zone = ifelse(has_zone==1, "Zone province", "Non-zone province"))

print(comparison)


# Zone distribution histogram

ggplot(analysis_units, aes(n_zones)) +
  geom_histogram(binwidth = 2) +
  labs(
    title = "Distribution of Economic Zones per Province",
    y = "Number of Provinces",
    x = "Number of Zones"
  )


# Exploratory comparisons by zone presence

model_pop  = lm(log(T_TL + 1) ~ has_zone, data = analysis_units)
model_hosp = lm(hospitals_count ~ has_zone, data = analysis_units)
model_educ_10k = lm(log(access_pop_education_10km) ~ has_zone, data = analysis_units)

summary(model_pop)
summary(model_hosp)
summary(model_educ_10k)


# Cross-sectional associations with zone presence

# Economic zones are not randomly assigned across provinces. Existing
# characteristics such as population, infrastructure, and development may
# influence zone placement, while zone establishment may also affect subsequent
# local outcomes. These cross-sectional regressions therefore capture
# descriptive associations rather than causal effects.

model_zone_pop <- glm(
  has_zone ~ log(T_TL + 1),
  data = analysis_units,
  family = binomial()
)

summary(model_zone_pop)

model_logit <- glm(
  has_zone ~ hospitals_count +
    log(access_pop_education_10km) +
    log(T_TL + 1),
  data = analysis_units,
  family = binomial()
)
summary(model_logit)


# Plots
# i. population
plot(analysis_units$has_zone, log(analysis_units$T_TL + 1), 
     main = "Economic Zone Presence and Population", 
     xlab = "Has zone (0, 1)", 
     ylab = "Log Population + 1", 
     pch = 16,        
     col = "darkgray")

abline(model_pop, 
       col = "blue",    
       lwd = 2)       

# ii. hospitals and SEZs
ggplot(
  analysis_units,
  aes(x = factor(has_zone, labels = c("No", "Yes")),
      y = hospitals_count)
) +
  geom_boxplot(
    fill = "transparent",
    color = "black", 
    linewidth = 0.8,
    outlier.shape = NA
    ) +
  geom_jitter(
    width = 0.08, 
    alpha = 0.5,
    color = "#52accb"
    ) +
  stat_summary(
    fun = mean,
    geom = "point",
    color = "blue",
    size = 3
    ) +
  labs(
    title = "Hospital Counts by Economic Zone Presence",
    x = "Economic Zone in Province",
    y = "Hospitals"
  )

# Correlation matrix: assessing overlap among development indicators

analysis_units %>%
  select(
    T_TL,
    hospitals_count,
    education_count,
    rural_pop_perc,
    RP100_pop_u15_30cm
  ) %>%
  cor(use = "complete.obs")


# =============================================================
# 2. Longitudinal causal extension (not implemented)
# =============================================================

# The descriptive analysis above examines differences between provinces with
# and without PEZA economic zones. These comparisons should not be interpreted
# as causal effects because zone placement may reflect pre-existing differences
# in population, infrastructure, and economic development.

# A potential causal extension would exploit variation in the timing of zone
# establishment. The PEZA zone list includes operating status and proclamation
# information that could be used to construct establishment dates. Combined
# with panel outcomes such as BIR monthly provincial tax collections (CY 2016-2024),
# this could support a staggered difference-in-differences design.

# Additional work would be needed to validate establishment dates, define treatment
# timing, and assess whether parallel trends assumptions are plausible.
