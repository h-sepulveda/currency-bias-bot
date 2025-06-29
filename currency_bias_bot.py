# streamlit_live_heatmap.py

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import datetime
import sqlite3

# --- Currency-country mapping ---
COUNTRIES = {
    "USD": "USA",
    "EUR": "EMU",  # Euro Area
    "JPY": "JPN",
    "GBP": "GBR",
    "AUD": "AUS",
    "CAD": "CAN"
}

# --- Indicators and World Bank codes ---
INDICATORS = {
    "GDP Growth (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation (CPI YoY)": "FP.CPI.TOTL.ZG",
    "Unemployment Rate": "SL.UEM.TOTL.ZS",
    "Lending Interest Rate": "FR.INR.LEND"
}

# --- Database setup ---
DB_NAME = "macro_live_snapshots.db"
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS data (
    date TEXT,
    currency TEXT,
    indicator TEXT,
    value REAL,
    PRIMARY KEY (date, currency, indicator)
)
""")
conn.commit()

# --- Fetch from World Bank API ---
def fetch_world_bank_data(indicator_code, country_code):
    url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}?format=json&per_page=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 1:
            for entry in data[1]:
                if entry["value"] is not None:
                    return entry["value"], entry["date"]
    return None, None

# --- Load or fetch data ---
def get_data(currency):
    today = datetime.date.today().isoformat()
    stored = pd.read_sql_query("SELECT * FROM data WHERE date = ? AND currency = ?", conn, params=(today, currency))
    if stored.empty:
        rows = []
        for label, code in INDICATORS.items():
            val, year = fetch_world_bank_data(code, COUNTRIES[currency])
            if val is not None:
                rows.append((today, currency, label, val))
        df = pd.DataFrame(rows, columns=["date", "currency", "indicator", "value"])
        df.to_sql("data", conn, if_exists="append", index=False)
        return df
    else:
        return stored

# --- Streamlit UI ---
st.set_page_config(page_title="Live Economic Heatmap", layout="wide")
st.title("📊 Live Economic Heatmap (World Bank API)")

currency = st.selectbox("Select Currency", list(COUNTRIES.keys()))
df = get_data(currency)

if not df.empty:
    st.subheader(f"{currency} Macroeconomic Overview")
    df_display = df.copy()
    df_display["Bias"] = df_display.apply(lambda row: (
        "Bullish" if (
            (row["indicator"] in ["GDP Growth (%)", "Lending Interest Rate"] and row["value"] > 0) or
            (row["indicator"] == "Inflation (CPI YoY)" and row["value"] < 4) or
            (row["indicator"] == "Unemployment Rate" and row["value"] < 5)
        ) else "Bearish"
    ), axis=1)

    st.dataframe(df_display[["indicator", "value", "Bias"]])

    bullish = (df_display["Bias"] == "Bullish").sum()
    bearish = (df_display["Bias"] == "Bearish").sum()
    total = bullish + bearish
    pct = (bullish / total * 100) if total > 0 else 0
    score = "Bullish" if pct > 60 else "Bearish" if pct < 40 else "Neutral"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        title={"text": f"{currency} Bias Score: {score}"},
        gauge={"axis": {"range": [0, 100]},
               "bar": {"color": "#4CAF50" if score == "Bullish" else "#F44336"},
               "steps": [
                   {"range": [0, 40], "color": "#F44336"},
                   {"range": [40, 60], "color": "#FFC107"},
                   {"range": [60, 100], "color": "#4CAF50"}
               ]}
    ))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"**Final Market Bias:** {score} based on latest World Bank data for {currency}")
else:
    st.warning("No data available.")

conn.close()

