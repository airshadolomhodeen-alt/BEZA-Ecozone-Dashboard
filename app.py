import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
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
    .main-header { font-size: 2.3rem; color: #1f77b4; font-weight: 700; margin-bottom: 0px; }
    .sub-text { font-size: 1.1rem; color: #555555; margin-bottom: 20px; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ROBUST DATA LOADING & CACHING
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

# Sidebar Navigation & Mapbox Config
st.sidebar.markdown("## 🧭 Navigation")
app_mode = st.sidebar.radio("Choose a View:", [
    "📊 Executive Summary",
    "🗺️ Spatial & Zone Distribution",
    "🏥 Infrastructure & Demographics",
    "📈 Statistical Models",
    "📚 Data Source Audit"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Satellite Map Settings")
mapbox_token = st.sidebar.text_input("Mapbox Access Token", type="password", placeholder="pk.eyJ1...", help="Get a free token at mapbox.com to enable Google Earth-style satellite imagery.")
map_style_choice = st.sidebar.selectbox("Basemap Style", ["satellite-streets-v12", "satellite-v9", "streets-v12", "carto-positron"])

if analysis_units is None:
    st.error("⚠️ Processed CSV files not found. Please ensure `analysis_units.csv`, `zones.csv`, and `sources.csv` are in the root directory.")
    st.stop()

# Safe string formatting for categorical charts
analysis_units['zone_label'] = analysis_units['has_zone'].map({1: 'Zone Present', 0: 'No Zone'}).astype(str)

# ==========================================
# 1. EXECUTIVE SUMMARY
# ==========================================
if app_mode == "📊 Executive Summary":
    st.markdown('<p class="main-header">🇵🇭 PEZA Economic Zones Intelligence Hub</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">Comprehensive analytical assessment of Philippine Economic Zone Authority (PEZA) provincial distributions, infrastructure access, and regional disparities.</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Provinces Analyzed", f"{len(analysis_units):,}")
    with col2:
        zone_prov_count = int(analysis_units['has_zone'].sum())
        st.metric("Provinces with Zones", f"{zone_prov_count:,}")
    with col3:
        total_zones = int(analysis_units['n_zones'].sum())
        st.metric("Total Economic Zones", f"{total_zones:,}")
    with col4:
        avg_pop = int(analysis_units['T_TL'].mean())
        st.metric("Mean Provincial Pop.", f"{avg_pop:,}")
    
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
        'n_provinces': '{:,}',
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
    st.markdown('<p class="sub-text">Inspecting provincial concentration hierarchies and Google Earth satellite zone-type clusters.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.1, 1.3])
    
    with col1:
        st.subheader("Top Provinces by Zone Count")
        top_provinces = analysis_units[analysis_units['n_zones'] > 0].sort_values(by='n_zones', ascending=True)
        
        fig_bar = px.bar(
            top_provinces, 
            x="n_zones", 
            y="ADM2_NAME", 
            orientation="h",
            labels={"n_zones": "Number of Economic Zones", "ADM2_NAME": "Province"},
            color="n_zones",
            color_continuous_scale="Blues"
        )
        fig_bar.update_layout(height=650, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        st.subheader("Google Earth Satellite Mapping by Zone Nature")
        if zones is not None and len(zones) > 0:
            lat_col = next((c for c in zones.columns if c.lower() in ['lat', 'latitude']), None)
            lon_col = next((c for c in zones.columns if c.lower() in ['lon', 'long', 'longitude']), None)
            name_col = next((c for c in zones.columns if 'name' in c.lower() and c.upper() != 'PROVINCE_NAME'), zones.columns[0])
            nature_col = next((c for c in zones.columns if c.lower() in ['nature', 'type', 'status']), zones.columns[0])
            
            if lat_col and lon_col:
                map_df = zones.dropna(subset=[lat_col, lon_col]).copy()
                
                # Apply Mapbox token if user provided one in sidebar
                if mapbox_token:
                    px.set_mapbox_access_token(mapbox_token)
                    active_style = map_style_choice
                else:
                    active_style = "open-street-map"
                    st.sidebar.info("💡 Paste a free token from mapbox.com above to activate high-resolution Google Earth satellite imagery.")
                
                fig_map = px.scatter_mapbox(
                    map_df,
                    lat=lat_col,
                    lon=lon_col,
                    color=nature_col,
                    hover_name=name_col,
                    hover_data=['CITY', 'province_name', nature_col],
                    mapbox_style=active_style,
                    zoom=5.2,
                    center={"lat": 12.8797, "lon": 121.7740},
                    height=650,
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                
                fig_map.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    legend=dict(
                        title=dict(text="<b>Zone Nature</b>"),
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10)
                    )
                )
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("Latitude/Longitude columns not found in zones dataset.")
        else:
            st.info("Zones dataset is currently unavailable.")
            
    st.markdown("---")
    st.subheader("📋 Complete Provincial Zone Directory")
    directory_df = analysis_units[['ADM2_NAME', 'ADM1_NAME', 'n_zones', 'T_TL', 'hospitals_count']].sort_values(by='n_zones', ascending=False)
    directory_df.columns = ['Province / Area', 'Region', 'Total Zones', 'Total Population', 'Hospitals']
    st.dataframe(directory_df, use_container_width=True, height=350)

# ==========================================
# 3. INFRASTRUCTURE & DEMOGRAPHICS
# ==========================================
elif app_mode == "🏥 Infrastructure & Demographics":
    st.markdown('<p class="main-header">Infrastructure & Demographic Correlates</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">Evaluating healthcare capacity and population distributions relative to economic zone presence.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Hospital Distribution by Zone Presence")
        fig_box = px.box(
            analysis_units, 
            x="zone_label", 
            y="hospitals_count",
            points="all",
            labels={"zone_label": "Zone Status", "hospitals_count": "Hospital Count"},
            color_discrete_sequence=["#1f77b4"]
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
    with col2:
        st.subheader("Provincial Population Histogram")
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
    st.markdown('<p class="main-header">Cross-Sectional Regression Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">Econometric modeling of economic zone determinants across provinces.</p>', unsafe_allow_html=True)
    
    model_choice = st.selectbox("Select Econometric Specification:", [
        "Logistic Regression: Probability of Zone Placement",
        "OLS Regression: Population vs. Zone Status"
    ])
    
    if "Logistic" in model_choice:
        st.markdown("**Model Specification:** `has_zone ~ hospitals_count + log(access_pop_education_10km + 1) + log(T_TL + 1)`")
        try:
            logit_mod = smf.logit("has_zone ~ hospitals_count + np.log(access_pop_education_10km + 1) + np.log(T_TL + 1)", data=analysis_units).fit()
            st.text(str(logit_mod.summary()))
        except Exception as e:
            st.error(f"Model fitting engine error: {e}")
    else:
        st.markdown("**Model Specification:** `log(T_TL + 1) ~ has_zone`")
        try:
            ols_mod = smf.ols("np.log(T_TL + 1) ~ has_zone", data=analysis_units).fit()
            st.text(str(ols_mod.summary()))
        except Exception as e:
            st.error(f"Model fitting engine error: {e}")

# ==========================================
# 5. DATA SOURCE AUDIT
# ==========================================
elif app_mode == "📚 Data Source Audit":
    st.markdown('<p class="main-header">Data Provenance & Source Audit</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">Reviewing origin links, credibility scores, and variable mapping.</p>', unsafe_allow_html=True)
    
    if sources is not None:
        st.dataframe(sources, use_container_width=True)
    else:
        st.info("Sources table not detected.")
