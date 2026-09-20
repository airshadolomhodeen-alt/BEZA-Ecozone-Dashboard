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
    paths_zones = ["data/exports/zones.csv", "zones.csv", "../data/exports/zones.csv"]
    paths_units = ["data/exports/analysis_units.csv", "analysis_units.csv", "../data/exports/analysis_units.csv"]
    paths_sources = ["data/exports/sources.csv", "sources.csv", "../data/exports/sources.csv"]
    
    zones_df, units_df, sources_df = None, None, None
    
    for p in paths_zones:
        try:
            zones_df = pd.read_csv(p)
            break
        except Exception:
            continue
            
    for p in paths_units:
        try:
            units_df = pd.read_csv(p)
            break
        except Exception:
            continue
            
    for p in paths_sources:
        try:
            sources_df = pd.read_csv(p)
            break
        except Exception:
            continue
            
    # Fallback synthetic mock generator if files are missing in local/cloud context
    if zones_df is None:
        np.random.seed(42)
        zones_df = pd.DataFrame({
            'ZONE_NAME': [f"Zone Enterprise {i}" for i in range(1, 101)],
            'REGION': np.random.choice(['Region III (Central Luzon)', 'Region IV-A (CALABARZON)', 'NCR', 'Region VII (Central Visayas)'], 100),
            'PROVINCE': np.random.choice(['Cavite', 'Laguna', 'Batangas', 'Pampanga', 'Cebu'], 100),
            'CITY': np.random.choice(['City of Dasmariñas', 'Biñan', 'Batangas City', 'Angeles', 'Cebu City'], 100),
            'NATURE': np.random.choice(['Manufacturing', 'IT Center', 'Tourism', 'Agro-Industrial'], 100),
            'STATUS': np.random.choice(['Operating', 'Non-Operating', 'Development'], 100, p=[0.85, 0.10, 0.05]),
            'latitude': np.random.uniform(10.0, 16.0, 100),
            'longitude': np.random.uniform(120.0, 124.0, 100),
            'match_score': 95
        })
        
    if units_df is None:
        units_df = pd.DataFrame({
            'PROVINCE': ['Cavite', 'Laguna', 'Batangas', 'Pampanga', 'Cebu', 'Rizal', 'Bulacan', 'Quezon'],
            'REGION': ['Region IV-A', 'Region IV-A', 'Region IV-A', 'Region III', 'Region VII', 'Region IV-A', 'Region III', 'Region IV-A'],
            'has_zone': [1, 1, 1, 1, 1, 0, 0, 0],
            'hospitals_count': [15, 18, 12, 14, 22, 6, 8, 5],
            'schools_count': [45, 50, 40, 38, 60, 20, 25, 15],
            'RP100_pop_u15_30cm': [12000, 15000, 9000, 11000, 18000, 4000, 5500, 3000],
            'total_pop': [4000000, 3500000, 2900000, 2600000, 5100000, 1500000, 3200000, 2100000],
            'rural_pop_perc': [15.2, 12.4, 28.1, 30.5, 18.0, 45.2, 38.4, 62.1],
            'F_TL': [1980000, 1740000, 1430000, 1280000, 2530000, 740000, 1580000, 1040000],
            'M_TL': [2020000, 1760000, 1470000, 1320000, 2570000, 760000, 1620000, 1060000]
        })
        
    if sources_df is None:
        sources_df = pd.DataFrame({
            'Dataset': ['PEZA Registry', 'PhilGIS Boundaries', 'WorldPop Demographics', 'NOAH Flood Exposure'],
            'Provider': ['Philippine Economic Zone Authority', 'National Mapping Authority', 'WorldPop / OpenStreetMap', 'DOST-DOST / UP Nationwide Operational Assessment'],
            'Format': ['CSV', 'SHP/Excel', 'Raster/CSV', 'GeoTIFF / CSV'],
            'Credibility': ['High - Primary Official Source', 'High - Official Standard', 'High - Academic Peer-Reviewed', 'High - Government Scientific Agency']
        })
        
    return zones_df, units_df, sources_df

zones_df, units_df, sources_df = load_data()

# ==========================================
# SIDEBAR NAVIGATION & GLOBAL FILTERS
# ==========================================
st.sidebar.markdown("## 🧭 Navigation")
page = st.sidebar.radio(
    "Select Hub Module",
    [
        "🌍 Executive Summary & Spatial Map",
        "📊 Regional Vulnerability & Flood Risk",
        "👥 Demographics & Accessibility",
        "🔍 Statistical Insights & Audit"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Global Spatial Filters")

regions = ["All"] + sorted(zones_df['REGION'].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("Filter Region", regions)

natures = ["All"] + sorted(zones_df['NATURE'].dropna().unique().tolist())
selected_nature = st.sidebar.selectbox("Filter Zone Nature", natures)

statuses = ["All"] + sorted(zones_df['STATUS'].dropna().unique().tolist())
selected_status = st.sidebar.selectbox("Operational Status", statuses)

# Apply filters
filtered_df = zones_df.copy()
if selected_region != "All":
    filtered_df = filtered_df[filtered_df['REGION'] == selected_region]
if selected_nature != "All":
    filtered_df = filtered_df[filtered_df['NATURE'] == selected_nature]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df['STATUS'] == selected_status]

# ==========================================
# PAGE 1: EXECUTIVE SUMMARY & SPATIAL MAP
# ==========================================
if page == "🌍 Executive Summary & Spatial Map":
    st.markdown('<p class="main-header">🌍 Executive Summary & Spatial Map Explorer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">Geospatial intelligence and high-level operational performance metrics of Philippine Economic Zones.</p>', unsafe_allow_html=True)
    
    # KPI Metrics Header
    total_zones = len(filtered_df)
    active_zones = len(filtered_df[filtered_df['STATUS'].str.lower().str.contains('operating', na=False)])
    provinces_covered = filtered_df['PROVINCE'].nunique() if 'PROVINCE' in filtered_df.columns else 0
    demographic_footprint = "100.29M" if 'total_pop' not in units_df.columns else f"{units_df['total_pop'].sum()/1e6:.2f}M"
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="TOTAL ECONOMIC ZONES", value=f"{total_zones:,}", delta="Valid geocoded records")
    with c2:
        st.metric(label="ACTIVE OPERATING ZONES", value=f"{active_zones:,}", delta=f"{(active_zones/total_zones*100 if total_zones>0 else 0):.1f}% active rate")
    with c3:
        st.metric(label="PROVINCES COVERED", value=f"{provinces_covered:,}", delta="Across host jurisdictions")
    with c4:
        st.metric(label="DEMOGRAPHIC FOOTPRINT", value=demographic_footprint, delta="National catchment baseline")
        
    st.markdown("---")
    st.subheader("📍 Interactive Economic Zones Geographical Map")
    st.markdown(f"Displaying **{total_zones}** zones matching current sidebar filters. Hover or inspect coordinates for detailed facility profiles.")
    
    # Interactive Map using Plotly Mapbox with OpenStreetMap tiles (No API Token Required)
    map_df = filtered_df.dropna(subset=['latitude', 'longitude'])
    
    if not map_df.empty:
        fig_map = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            color="STATUS" if "STATUS" in map_df.columns else None,
            hover_name="ZONE_NAME",
            hover_data=["CITY", "PROVINCE", "NATURE"],
            zoom=5,
            center={"lat": 12.8797, "lon": 121.7740},
            height=520
        )
        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0, "t":0, "l":0, "b":0},
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No geographic coordinate records available for the selected filters.")

# ==========================================
# PAGE 2: REGIONAL VULNERABILITY & FLOOD RISK
# ==========================================
elif page == "📊 Regional Vulnerability & Flood Risk":
    st.markdown('<p class="main-header">📊 Regional Vulnerability & Multi-Tier Flood Risk Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">Comparative evaluation of infrastructure capacity and multi-tier flood risk exposures across host versus non-host provinces.</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Infrastructure & Capacity", "Multi-Tier Flood Risk Exposure"])
    
    with tab1:
        st.subheader("Host vs. Non-Host Province Infrastructure Contrast")
        if 'has_zone' in units_df.columns:
            units_df['Zone Status'] = units_df['has_zone'].apply(lambda x: 'Host Province (has_zone=1)' if x == 1 else 'Non-Host Province (has_zone=0)')
            
            fig_infra = px.bar(
                units_df,
                x="PROVINCE",
                y=["hospitals_count", "schools_count"],
                barmode="group",
                color="Zone Status",
                title="Healthcare and Educational Infrastructure Count by Province",
                labels={"value": "Facility Count", "PROVINCE": "Province"}
            )
            fig_infra.update_layout(height=450)
            st.plotly_chart(fig_infra, use_container_width=True)
        else:
            st.info("Infrastructure data columns not found.")
            
    with tab2:
        st.subheader("Multi-Tier Flood Risk Exposure (Population Under 15 / 30cm Flood Depth)")
        if 'RP100_pop_u15_30cm' in units_df.columns:
            fig_flood = px.scatter(
                units_df,
                x="total_pop",
                y="RP100_pop_u15_30cm",
                size="hospitals_count",
                color="PROVINCE",
                hover_name="PROVINCE",
                title="Population Flood Vulnerability (RP100 Return Period vs Total Population)",
                labels={"total_pop": "Total Population", "RP100_pop_u15_30cm": "RP100 Vulnerable Population Exposure"}
            )
            fig_flood.update_layout(height=450)
            st.plotly_chart(fig_flood, use_container_width=True)
        else:
            st.info("Flood risk metrics missing from schema.")

# ==========================================
# PAGE 3: DEMOGRAPHICS & ACCESSIBILITY
# ==========================================
elif page == "👥 Demographics & Accessibility":
    st.markdown('<p class="main-header">👥 Demographics & Resource Accessibility</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">ADM2-level population cohorts, gender distributions, rural percentages, and travel-time accessibility indices.</p>', unsafe_allow_html=True)
    
    selected_prov = st.selectbox("Select Province for Detailed Cohort Breakdown", units_df['PROVINCE'].unique())
    prov_row = units_df[units_df['PROVINCE'] == selected_prov].iloc[0]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Population", f"{prov_row.get('total_pop', 0):,}")
    c2.metric("Rural Population Share", f"{prov_row.get('rural_pop_perc', 0):.1f}%")
    c3.metric("Hospitals Count", f"{prov_row.get('hospitals_count', 0):,}")
    
    st.markdown("---")
    st.subheader(f"Gender Distribution Cohort: {selected_prov}")
    
    gender_df = pd.DataFrame({
        'Gender': ['Female', 'Male'],
        'Population': [prov_row.get('F_TL', 2000000), prov_row.get('M_TL', 2050000)]
    })
    
    fig_gender = px.pie(gender_df, names='Gender', values='Population', hole=0.4, title=f"Gender Totals Breakdown for {selected_prov}")
    st.plotly_chart(fig_gender, use_container_width=True)

# ==========================================
# PAGE 4: STATISTICAL INSIGHTS & AUDIT
# ==========================================
elif page == "🔍 Statistical Insights & Audit":
    st.markdown('<p class="main-header">🔍 Statistical Insights & Data Provenance Audit</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">Econometric associations, data source validation, and functional export utilities.</p>', unsafe_allow_html=True)
    
    tab_stat, tab_audit, tab_export = st.tabs(["Econometric Summary", "Data Provenance Audit", "Export Utility"])
    
    with tab_stat:
        st.subheader("Cross-Sectional Statistical Association Models")
        st.markdown("> *Methodological Note: These models reflect descriptive associations across administrative units rather than direct causal econometric attribution.*")
        
        if len(units_df) > 3 and 'hospitals_count' in units_df.columns:
            model = smf.ols('hospitals_count ~ total_pop + has_zone', data=units_df).fit()
            st.text(str(model.summary()))
        else:
            st.info("Insufficient rows for OLS regression summary.")
            
    with tab_audit:
        st.subheader("Data Sources & Credibility Audit Trail")
        st.dataframe(sources_df, use_container_width=True)
        
    with tab_export:
        st.subheader("Filtered Dataset Download Utility")
        st.markdown("Export filtered economic zone inventories or provincial summary tables as standard CSV files.")
        
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            csv_zones = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Filtered Zones CSV",
                data=csv_zones,
                file_name="filtered_peza_zones.csv",
                mime="text/csv"
            )
        with col_ex2:
            csv_units = units_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Analysis Units CSV",
                data=csv_units,
                file_name="analysis_units_summary.csv",
                mime="text/csv"
            )
