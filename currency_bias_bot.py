# Streamlit Economic Heatmap with Live Data, Historical DB, CSV Export & Multiple Regions

import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import sqlite3
import datetime

# --- DATABASE SETUP ---
DB_NAME = "macro_history.db"
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS macro_data (
    region TEXT,
    indicator TEXT,
    date TEXT,
    actual REAL,
    forecast REAL,
    previous REAL,
    surprise REAL,
    usd_impact TEXT,
    stocks_impact TEXT
)''')
conn.commit()

# --- SUPPORTED REGIONS & MOCKED DATA ---
REGIONS = {
    "US": "United States",
    "EU": "Euro Area",
    "UK": "United Kingdom",
    "JP": "Japan",
    "CA": "Canada"
}

# For demo purposes, mock data generator (replace with real API integration as needed)
def get_mock_data(region):
    mock_data = [
        {"name": "GDP Growth QoQ", "actual": -0.5, "forecast": -0.2, "previous": 2.4},
        {"name": "CPI YoY", "actual": 2.4, "forecast": 2.5, "previous": 2.3},
        {"name": "Unemployment Rate", "actual": 4.2, "forecast": 4.2, "previous": 4.2},
        {"name": "Retail Sales MoM", "actual": -0.9, "forecast": -0.5, "previous": 0.1},
        {"name": "Services PMI", "actual": 49.9, "forecast": 52, "previous": 51.6},
        {"name": "PCE YoY", "actual": 2.7, "forecast": 2.6, "previous": 2.5},
        {"name": "Jobless Claims", "actual": 236000, "forecast": 245000, "previous": 246000},
        {"name": "Exports", "actual": 1.5, "forecast": 1.8, "previous": 1.6},
        {"name": "Imports", "actual": 1.7, "forecast": 1.6, "previous": 1.5},
        {"name": "Industrial Production", "actual": 0.3, "forecast": 0.2, "previous": 0.1}
    ]
    return mock_data

# --- SCORING FUNCTION ---
def score_impact(actual, forecast):
    if forecast is None:
        return 0.0, "Neutral"
    surprise = actual - forecast
    direction = "Bullish" if surprise > 0 else "Bearish" if surprise < 0 else "Neutral"
    return round(surprise, 2), direction

# --- APP ---
st.set_page_config(layout="wide")
st.title("🌐 Economic Heatmap Dashboard with History & Export")

region_key = st.selectbox("Select Region:", list(REGIONS.keys()), format_func=lambda x: REGIONS[x])
data_source = get_mock_data(region_key)

# --- PROCESS DATA ---
today = datetime.date.today().isoformat()
data_rows = []

for row in data_source:
    surprise, usd_bias = score_impact(row["actual"], row["forecast"])
    stocks_bias = usd_bias
    data_rows.append({
        "Region": region_key,
        "Indicator": row["name"],
        "Date": today,
        "Surprise": surprise,
        "Actual": row["actual"],
        "Forecast": row["forecast"],
        "Previous": row["previous"],
        "USD Impact": usd_bias,
        "Stocks Impact": stocks_bias
    })
    # Save to DB
    c.execute("INSERT INTO macro_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (region_key, row["name"], today, row["actual"], row["forecast"], row["previous"], surprise, usd_bias, stocks_bias))
conn.commit()

# --- DISPLAY TABLE ---
df = pd.DataFrame(data_rows)
impact_counts = df["USD Impact"].value_counts(normalize=True) * 100

st.dataframe(df)

# --- BIAS GAUGE ---
gauge_value = impact_counts.get("Bullish", 0)
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = gauge_value,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': f"{region_key} Bias Score (%)"},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': "blue"},
        'steps': [
            {'range': [0, 40], 'color': "red"},
            {'range': [40, 60], 'color': "gray"},
            {'range': [60, 100], 'color': "green"}
        ]
    }
))
st.plotly_chart(fig, use_container_width=True)

# --- HISTORICAL SECTION ---
st.subheader("📈 Historical Records")
hist = pd.read_sql_query("SELECT * FROM macro_data WHERE region = ? ORDER BY date DESC", conn, params=(region_key,))
st.dataframe(hist)

# --- EXPORT BUTTON ---
st.download_button(
    label="Download History as CSV",
    data=hist.to_csv(index=False).encode('utf-8'),
    file_name=f'{region_key}_macro_history.csv',
    mime='text/csv'
)

conn.close()


