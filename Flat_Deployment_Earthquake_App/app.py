
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

import os
DATA_PATH = os.path.join(os.path.dirname(__file__), "phivolcs_earthquake_data_clean.csv")

st.set_page_config(page_title="Earthquake Risk Map — PH", layout="wide")
st.title("Earthquake Risk Map — Philippines (Flat Deployment Version)")

@st.cache_data
def load_data(path):
    return pd.read_csv(path, parse_dates=['datetime'], infer_datetime_format=True)

df = load_data(DATA_PATH)

st.sidebar.header("Filters")
if 'datetime' in df.columns:
    min_d = df['datetime'].min().date()
    max_d = df['datetime'].max().date()
    dr = st.sidebar.date_input("Date Range", (min_d, max_d))
    start = pd.to_datetime(dr[0])
    end = pd.to_datetime(dr[1]) + pd.Timedelta(days=1)
else:
    start = None
    end = None

mag_min, mag_max = float(df['magnitude'].min()), float(df['magnitude'].max())
mag_range = st.sidebar.slider("Magnitude", mag_min, mag_max, (mag_min, mag_max))

depth_min, depth_max = float(df['depth_km'].min()), float(df['depth_km'].max())
depth_range = st.sidebar.slider("Depth (km)", depth_min, depth_max, (depth_min, depth_max))

search = st.sidebar.text_input("Search Location")

mask = pd.Series(True, index=df.index)
if start is not None:
    mask &= (df['datetime'] >= start) & (df['datetime'] <= end)
mask &= df['magnitude'].between(mag_range[0], mag_range[1])
mask &= df['depth_km'].between(depth_range[0], depth_range[1])
if search:
    mask &= df['region'].str.contains(search, case=False, na=False)

filtered = df[mask]
st.sidebar.write(f"Events: {len(filtered):,}")

st.subheader("Map")
if len(filtered) > 0:
    center = [filtered['latitude'].mean(), filtered['longitude'].mean()]
    m = folium.Map(location=center, zoom_start=6)
    mc = MarkerCluster().add_to(m)
    for _, r in filtered.iterrows():
        if pd.isna(r['latitude']) or pd.isna(r['longitude']):
            continue
        folium.CircleMarker(
            location=[r['latitude'], r['longitude']],
            radius=5,
            color="red",
            fill=True,
            fill_opacity=0.7,
            popup=f"Date: {r['datetime']}<br>Mag: {r['magnitude']}<br>Depth: {r['depth_km']} km"
        ).add_to(mc)
    st_folium(m, width=1000, height=600)
else:
    st.info("No events found.")

st.subheader("Data Preview")
st.dataframe(filtered.head(100))

st.download_button("Download CSV", filtered.to_csv(index=False), "filtered.csv", "text/csv")
