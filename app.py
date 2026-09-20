with col2:
        st.subheader("Google Earth Satellite Mapping by Zone Nature")
        if zones is not None and len(zones) > 0:
            lat_col = next((c for c in zones.columns if c.lower() in ['lat', 'latitude']), None)
            lon_col = next((c for c in zones.columns if c.lower() in ['lon', 'long', 'longitude']), None)
            name_col = next((c for c in zones.columns if 'name' in c.lower() and c.upper() != 'PROVINCE_NAME'), zones.columns[0])
            nature_col = next((c for c in zones.columns if c.lower() in ['nature', 'type', 'status']), zones.columns[0])
            
            if lat_col and lon_col:
                map_df = zones.dropna(subset=[lat_col, lon_col]).copy()
                
                # Check if a valid token is provided
                if mapbox_token and mapbox_token.strip() != "":
                    px.set_mapbox_access_token(mapbox_token)
                    active_style = map_style_choice
                else:
                    active_style = "open-street-map"
                    st.sidebar.info("💡 Paste your free Mapbox token above to activate high-resolution satellite imagery.")
                
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
