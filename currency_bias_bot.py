# Streamlit Currency Bias Bot Dashboard

import requests
import pandas as pd
import streamlit as st

# --- SETTINGS ---
CURRENCY = "USD"
COUNTRY = "united states"
API_KEY = "YOUR_TRADINGECONOMICS_API_KEY"

# --- FUNCTIONS ---
def get_macro_data():
    url = f"https://api.tradingeconomics.com/calendar/country/{COUNTRY}?c={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return []

def parse_and_score(data):
    indicators = {
        "GDP Growth Rate": 1,
        "Unemployment Rate": -1,
        "Inflation Rate": -1,
        "Interest Rate": 1,
        "Retail Sales": 1,
        "Balance of Trade": 1,
        "Consumer Confidence": 1
    }

    rows = []
    score = 0

    for item in data:
        indicator = item.get("Event")
        actual = item.get("Actual")
        previous = item.get("Previous")

        if indicator in indicators and actual is not None and previous is not None:
            try:
                actual = float(actual)
                previous = float(previous)
                weight = indicators[indicator]
                bias = "Bullish" if (actual > previous and weight > 0) or (actual < previous and weight < 0) else "Bearish"
                score += weight if bias == "Bullish" else -weight
                rows.append({"Indicator": indicator, "Actual": actual, "Previous": previous, "Bias": bias})
            except:
                continue

    bias_summary = "Bullish" if score > 0 else "Bearish" if score < 0 else "Neutral"
    return pd.DataFrame(rows), bias_summary

# --- STREAMLIT APP ---
st.set_page_config(page_title="Currency Macro Bias Bot", layout="wide")
st.title(f"📈 {CURRENCY} Macroeconomic Bias Dashboard")

st.markdown("This dashboard fetches live macroeconomic data and evaluates a bullish or bearish bias for the currency.")

with st.spinner("Fetching macroeconomic data..."):
    data = get_macro_data()

if not data:
    st.error("Failed to fetch data. Check API key or internet connection.")
else:
    table, summary = parse_and_score(data)
    st.subheader("Macroeconomic Indicators")
    st.dataframe(table)
    st.subheader(f"📊 Final {CURRENCY} Bias: {summary}")
