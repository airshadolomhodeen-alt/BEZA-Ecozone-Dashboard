import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm
import statsmodels.formula.api as smf

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="PEZA Economic Zones Intelligence Hub",
    page_icon="🇵🇭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #1f77b4; font-weight: 700; }
    .sub-header { font-size: 1.3rem; color: #333333; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA LOADING & CACHING
# ==========================================
@st.cache_data
def load_data():
    paths_to_try = [
        ("data/exports/analysis_units.csv", "data/exports/zones.csv", "data/exports/sources.csv"),
        ("../data/exports/analysis_units.csv", "../data/exports/zones.csv", "../data/exports/sources.csv"),
        ("analysis_units.csv", "zones.csv", "sources.csv")
    ]
    
    for au_path, z_path, s_path in paths_to_try:
        try:
            analysis_units = pd.read_csv(au_path)
            zones = pd.read_csv(z_path)
            sources = pd.read_csv(s_path)
            return analysis_units, zones, sources
        except FileNotFoundError:
            continue
            
    return None, None, None

analysis_units, zones, sources = load_data()

# Sidebar Navigation
st.sidebar.markdown("## 🧭 Navigation")
app_mode = st.sidebar.radio("Choose a View:", [
    "📊 Executive Summary",
    "🗺️ Spatial & Zone Distribution",
    "🏥 Infrastructure & Demographics",
    "📈 Statistical Models",
    "📚 Data Source Audit"
])

if analysis_units is None:
    st.error("⚠️ Processed CSV files not found in repository. Please ensure export files are pushed to `data/exports/`.")
    st.stop()

# Prepare safe display string columns to prevent Plotly/Narwhals casting errors
analysis_units['zone_label'] = analysis_units['has_zone'].map({1: 'Zone Present', 0: 'No Zone'}).astype(str)

# ==========================================
# 1. EXECUTIVE SUMMARY
# ==========================================
if app_mode == "📊 Executive Summary":
    st.markdown('<p class="main-header">🇵🇭 PEZA Economic Zones Dashboard</p>', unsafe_allow_html=True)
    st.markdown("Exploring spatial distribution, provincial disparities, and infrastructure correlates of Philippine Economic Zone Authority (PEZA) zones.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Provinces", len(analysis_units))
    with col2:
        zone_prov_count = analysis_units['has_zone'].sum()
        st.metric("Provinces w/ Zones", int(zone_prov_count))
    with col3:
        total_zones = analysis_units['n_zones'].sum()
        st.metric("Total Economic Zones", int(total_zones))
    with col4:
        avg_pop = int(analysis_units['T_TL'].mean())
        st.metric("Avg Province Population", f"{avg_pop:,}")
    
    st.markdown("---")
    st.subheader("Descriptive Comparison: Zone vs. Non-Zone Provinces")
    
    comparison = analysis_units.groupby('has_zone').agg(
        n_provinces=('ADM2_PCODE', 'count'),
        mean_total_pop=('T_TL', 'mean'),
        mean_hospitals=('hospitals_count', 'mean'),
        mean_primary_hc=('primary_healthcare_count', 'mean'),
        mean_education=('education_count', 'mean'),
        mean_rural_pct=('rural_pop_perc', 'mean'),
        mean_hosp_access_1h=('access_pop_hospitals_1h', 'mean')
    ).reset_index()
    
    comparison['has_zone'] = comparison['has_zone'].map({1: 'Zone Province', 0: 'Non-Zone Province'})
    st.dataframe(comparison.style.format({
        'mean_total_pop': '{:,.0f}',
        'mean_hospitals': '{:.2f}',
        'mean_primary_hc': '{:.2f}',
        'mean_education': '{:.2f}',
        'mean_rural_pct': '{:.2f}%',
        'mean_hosp_access_1h': '{:,.0f}'
    }), use_container_width=True)

# ==========================================
# 2. SPATIAL & ZONE DISTRIBUTION
# ==========================================
elif app_mode == "🗺️ Spatial & Zone Distribution":
    st.markdown('<p class="main-header">Spatial Distribution of Economic Zones</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top Provinces by Economic Zone Count")
        # Filter provinces with at least 1 zone and sort by count descending
        top_provinces = analysis_units[analysis_units['n_zones'] > 0].sort_values(by='n_zones', ascending=True)
        
        fig_bar = px.bar(
            top_provinces, 
            x="n_zones", 
            y="ADM2_NAME", 
            orientation="h",
            labels={"n_zones": "Number of Economic Zones", "ADM2_NAME": "Province / District"},
            color="n_zones",
            color_continuous_scale="Blues"
        )
        fig_bar.update_layout(height=500, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        st.subheader("Geographic Mapping of Zones")
        if zones is not None and len(zones) > 0:
            lat_col = next((c for c in zones.columns if c.lower() in ['lat', 'latitude']), None)
            lon_col = next((c for c in zones.columns if c.lower() in ['lon', 'long', 'longitude']), None)
            name_col = next((c for c in zones.columns if 'name' in c.lower()), zones.columns[0])
            
            if lat_col and lon_col:
                fig_map = px.scatter_geo(
                    zones, lat=lat_col, lon=lon_col, hover_name=name_col,
                    projection="mercator", height=500, color_discrete_sequence=["#ff7f0e"]
                )
                fig_map.update_geos(
                    visible=True,
                    center={"lat": 12.8797, "lon": 121.7740},
                    lonaxis_range=[116, 127],
                    lataxis_range=[4, 21]
                )
                fig_map.update_layout(margin={"r":0,"t":10,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("Latitude/Longitude columns not found in zones dataset.")
        else:
            st.info("Zones dataset is currently unavailable.")
            
    st.markdown("---")
    st.subheader("📋 Province Economic Zone Directory")
    province_table = analysis_units[['ADM2_NAME', 'ADM1_NAME', 'n_zones', 'T_TL', 'hospitals_count']].sort_values(by='n_zones', ascending=False)
    province_table.columns = ['Province / Area', 'Region', 'Total Economic Zones', 'Total Population', 'Hospital Count']
    st.dataframe(province_table, use_container_width=True, height=350)

# ==========================================
# 3. INFRASTRUCTURE & DEMOGRAPHICS
# ==========================================
elif app_mode == "🏥 Infrastructure & Demographics":
    st.markdown('<p class="main-header">Infrastructure & Demographic Correlates</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Hospital Counts by Zone Presence")
        fig_box = px.box(
            analysis_units, 
            x="zone_label", 
            y="hospitals_count",
            points="all",
            labels={"zone_label": "Economic Zone Presence", "hospitals_count": "Hospital Count"},
            color_discrete_sequence=["#52accb"]
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
    with col2:
        st.subheader("Provincial Population Distribution")
        fig_hist_pop = px.histogram(
            analysis_units, x="T_TL", color="zone_label",
            nbins=20, barmode="group",
            labels={"T_TL": "Total Population", "zone_label": "Zone Status"},
            color_discrete_map={"Zone Present": "#1f77b4", "No Zone": "#ff7f0e"}
        )
        st.plotly_chart(fig_hist_pop, use_container_width=True)

# ==========================================
# 4. STATISTICAL MODELS
# ==========================================
elif app_mode == "📈 Statistical Models":
    st.markdown('<p class="main-header">Cross-Sectional Regression Models</p>', unsafe_allow_html=True)
    st.markdown("Analyzing predictors of economic zone placement across provinces using OLS and Logistic regressions.")
    
    model_type = st.selectbox("Select Model:", ["Logistic Regression: Zone Placement", "OLS: Population vs Zone Presence"])
    
    if "Logistic" in model_type:
        logit_mod = smf.logit("has_zone ~ hospitals_count + np.log(access_pop_education_10km + 1) + np.log(T_TL + 1)", data=analysis_units).fit()
        st.text(str(logit_mod.summary()))
    else:
        ols_mod = smf.ols("np.log(T_TL + 1) ~ has_zone", data=analysis_units).fit()
        st.text(str(ols_mod.summary()))

# ==========================================
# 5. DATA SOURCE AUDIT
# ==========================================
elif app_mode == "📚 Data Source Audit":
    st.markdown('<p class="main-header">Source Audit & Provenance</p>', unsafe_allow_html=True)
    if sources is not None:
        st.dataframe(sources, use_container_width=True)
    else:
        st.info("Source audit table not loaded.")
