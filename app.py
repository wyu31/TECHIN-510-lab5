import streamlit as st
import pandas.io.sql as sqlio
import altair as alt
import folium
from streamlit_folium import st_folium
import pandas as pd

from db import conn_str

st.title("Seattle Events")

# Load data from the database
df = sqlio.read_sql_query("SELECT *, EXTRACT(MONTH FROM date) AS month, EXTRACT(DOW FROM date) AS day_of_week FROM events", conn_str)

# Ensure 'date' is a datetime type for any further datetime operations
df['date'] = pd.to_datetime(df['date'])

# Chart 1: Most common event categories
st.header("Most Common Event Categories in Seattle")
category_chart = alt.Chart(df).mark_bar().encode(
    x="count():Q",
    y=alt.Y("category:N", sort='-x'),
    tooltip=['category', 'count()']
).interactive().properties(
    title="Number of Events by Category"
)
st.altair_chart(category_chart, use_container_width=True)

# Chart 2: Number of events by month
st.header("Number of Events by Month")
month_chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('month:O', axis=alt.Axis(title='Month')),
    y='count():Q',
    tooltip=['month', 'count()']
).interactive().properties(
    title="Events Distribution by Month"
)
st.altair_chart(month_chart, use_container_width=True)

# Chart 3: Number of events by day of the week
st.header("Number of Events by Day of the Week")
day_chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('day_of_week:O', axis=alt.Axis(title='Day of the Week')),
    y='count():Q',
    tooltip=['day_of_week', 'count()']
).interactive().properties(
    title="Events Distribution by Day of the Week"
)
st.altair_chart(day_chart, use_container_width=True)

# Event Locations and Venues
st.header("Event Locations and Venues")
location = st.selectbox("Select a location to filter by", df['location'].unique())
category = st.selectbox("Select a category to filter by", df['category'].unique())

# Filter for selected location and category
df_filtered = df[(df['location'] == location) & (df['category'] == category)]

# Further filter to exclude events with missing latitude or longitude
df_filtered = df_filtered.dropna(subset=['latitude', 'longitude'])

m = folium.Map(location=[47.6062, -122.3321], zoom_start=12)
for index, event in df_filtered.iterrows():
    popup_text = f"{event['title']} at {event['venue']}"
    folium.Marker([event['latitude'], event['longitude']], popup=popup_text).add_to(m)
st_folium(m, width=1200, height=600)

st.write(df_filtered)