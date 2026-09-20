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
    .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA LOADING & CACHING
# ==========================================
@st.cache_data
def load_data():
    try:
        analysis_units = pd.read_csv("../data/exports/analysis_units.csv")
        zones = pd.read_csv("../data/exports/zones.csv")
        sources = pd.read_csv("../data/exports/sources.csv")
        return analysis_units, zones, sources
    except FileNotFoundError:
        # Fallback synthetic structure if files aren't found locally yet
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
    st.error("⚠️ Processed CSV files not found in `../data/exports/`. Please run your data construction pipeline first or verify file paths.")
    st.stop()

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
    
    # Comparison table mirroring R script summary
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
        st.subheader("Distribution of Zones per Province")
        fig_hist = px.histogram(
            analysis_units, x="n_zones", nbins=15,
            labels={"n_zones": "Number of Zones", "count": "Number of Provinces"},
            color_discrete_sequence=["#1f77b4"]
        )
        fig_hist.update_layout(bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with col2:
        st.subheader("Geographic Mapping of Zones")
        if 'lat' in zones.columns and 'lon' in zones.columns:
            fig_map = px.scatter_mapbox(
                zones, lat="lat", lon="lon", hover_name="Zone Name" if "Zone Name" in zones.columns else zones.columns[0],
                zoom=5, height=400, mapbox_style="carto-positron"
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Latitude and longitude columns available in zones dataset.")

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
            x=analysis_units['has_zone'].map({1: 'Yes', 0: 'No'}), 
            y="hospitals_count",
            points="all",
            labels={"x": "Economic Zone in Province", "hospitals_count": "Hospital Count"},
            color_discrete_sequence=["#52accb"]
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
    with col2:
        st.subheader("Population vs. Zone Presence")
        fig_pop = px.scatter(
            analysis_units, x=analysis_units['has_zone'].map({1: 'Yes', 0: 'No'}), 
            y=np.log(analysis_units['T_TL'] + 1),
            labels={"x": "Economic Zone in Province", "y": "Log Population + 1"},
            trendline="ols", color_discrete_sequence=["#ff7f0e"]
        )
        st.plotly_chart(fig_pop, use_container_width=True)

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
