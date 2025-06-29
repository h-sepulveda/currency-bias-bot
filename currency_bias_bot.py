# Enhanced Streamlit Currency Bias Bot Dashboard with Charts, Selector, and Alerts

import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# --- SETTINGS ---
COUNTRIES = {
    "USD - United States": "united states",
    "EUR - Euro Area": "euro area",
    "JPY - Japan": "japan",
    "GBP - United Kingdom": "united kingdom",
    "CAD - Canada": "canada",
    "AUD - Australia": "australia",
    "CHF - Switzerland": "switzerland"
}
API_KEY = "YOUR_TRADINGECONOMICS_API_KEY"

# --- FUNCTIONS ---
def get_macro_data(country):
    url = f"https://api.tradingeconomics.com/calendar/country/{country}?c={API_KEY}"
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
    return pd.DataFrame(rows), bias_summary, score

# --- STREAMLIT APP ---
st.set_page_config(page_title="Currency Macro Bias Dashboard", layout="wide")
st.title("📊 Currency Macroeconomic Bias Bot")

st.markdown("""
This tool fetches real macroeconomic data and assigns a bullish or bearish bias to currencies.
Select a country/currency from the dropdown below to view live analysis.
""")

# Country selection
selection = st.selectbox("Choose a Currency / Country:", list(COUNTRIES.keys()))
country = COUNTRIES[selection]
currency = selection.split(" - ")[0]

with st.spinner("Fetching macroeconomic data..."):
    data = get_macro_data(country)

if not data:
    st.error("Failed to fetch data. Check API key or internet connection.")
else:
    table, summary, score = parse_and_score(data)

    # Table display
    st.subheader(f"Macroeconomic Indicators for {currency}")
    st.dataframe(table)

    # Bias score gauge (simplified chart)
    st.subheader("📈 Bias Meter")
    fig = px.bar(
        x=["Bearish", "Neutral", "Bullish"],
        y=[max(-5, -score), 0, max(0, score)],
        labels={"x": "Bias", "y": "Score"},
        title=f"Bias Score for {currency}: {summary}"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary text
    st.subheader(f"🧠 Final {currency} Bias: {summary}")
    st.markdown(f"The overall macroeconomic outlook for **{currency}** based on the latest data is: **{summary}**.")

    # Email alert setup
    with st.expander("📧 Set Up Email Alert (Optional)"):
        email = st.text_input("Enter your email to get alerts when bias changes:")
        if st.button("Save Alert"):
            if email:
                st.success(f"Alert setup for {currency} bias updates to {email} (placeholder logic).")
            else:
                st.warning("Please enter a valid email address.")

