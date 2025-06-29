 # Streamlit Currency Bias Bot Using World Bank API with Explanations and Alerts

import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# --- SETTINGS ---
COUNTRIES = {
    "USD - United States": "USA",
    "EUR - Germany": "DEU",
    "JPY - Japan": "JPN",
    "GBP - United Kingdom": "GBR",
    "CAD - Canada": "CAN",
    "AUD - Australia": "AUS",
    "CHF - Switzerland": "CHE"
}

WORLD_BANK_INDICATORS = {
    "NY.GDP.MKTP.CD": ("GDP (current US$)", 1, "Higher GDP usually indicates economic strength, attracting investors (bullish)."),
    "FP.CPI.TOTL.ZG": ("Inflation, consumer prices (annual %)", -1, "Rising inflation weakens currency purchasing power (bearish)."),
    "SL.UEM.TOTL.ZS": ("Unemployment rate (% of labor force)", -1, "Higher unemployment suggests a weaker economy (bearish)."),
    "NE.EXP.GNFS.CD": ("Exports of goods and services (current US$)", 1, "Increased exports indicate stronger demand and currency inflows (bullish)."),
    "NE.IMP.GNFS.CD": ("Imports of goods and services (current US$)", -1, "Higher imports may reflect demand but can also widen trade deficits (bearish)."),
    "GC.DOD.TOTL.GD.ZS": ("Central government debt (% of GDP)", -1, "High debt-to-GDP can be a red flag for currency stability (bearish).")
}

# --- FUNCTIONS ---
def fetch_indicator(country_code, indicator_code):
    url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}?format=json&per_page=10"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if len(data) > 1:
            values = [d for d in data[1] if d['value'] is not None]
            if len(values) >= 2:
                return float(values[0]['value']), float(values[1]['value'])
    return None, None

def analyze_country(country_code):
    rows = []
    explanations = []
    score = 0

    for code, (label, weight, rationale) in WORLD_BANK_INDICATORS.items():
        latest, previous = fetch_indicator(country_code, code)
        if latest is not None and previous is not None:
            bias = "Bullish" if (latest > previous and weight > 0) or (latest < previous and weight < 0) else "Bearish"
            score += weight if bias == "Bullish" else -weight
            rows.append({"Indicator": label, "Latest": latest, "Previous": previous, "Bias": bias, "Explanation": rationale})
            explanations.append(f"**{label}**: {rationale} → **{bias}**")

    bias_summary = "Bullish" if score > 0 else "Bearish" if score < 0 else "Neutral"
    return pd.DataFrame(rows), bias_summary, score, explanations

# --- STREAMLIT APP ---
st.set_page_config(page_title="Currency Bias Bot (World Bank API)", layout="wide")
st.title("🌍 Currency Macroeconomic Bias Bot (Free API)")

st.markdown("This version uses the free World Bank API for global macroeconomic indicators. Biases are explained and alerts can be configured.")

selection = st.selectbox("Choose a Currency / Country:", list(COUNTRIES.keys()))
country_code = COUNTRIES[selection]
currency = selection.split(" - ")[0]

with st.spinner("Fetching data from World Bank API..."):
    table, summary, score, explanations = analyze_country(country_code)

if table.empty:
    st.error("Failed to fetch or parse macroeconomic data.")
else:
    st.subheader(f"Indicators for {currency}")
    st.dataframe(table.drop(columns=["Explanation"]))

    st.subheader("📈 Bias Meter")
    fig = px.bar(
        x=["Bearish", "Neutral", "Bullish"],
        y=[max(-6, -score), 0, max(0, score)],
        labels={"x": "Bias", "y": "Score"},
        title=f"Bias Score for {currency}: {summary}"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"🧠 Final {currency} Bias: {summary}")
    st.markdown(f"Based on GDP, inflation, unemployment, exports, imports, and debt — the {currency} is currently **{summary}**.")

    st.subheader("📚 Indicator Explanations")
    for expl in explanations:
        st.markdown(f"- {expl}")

    st.subheader("📧 Set Up Email Alert (Optional)")
    email = st.text_input("Enter your email to receive alerts when bias changes:")
    if st.button("Save Alert"):
        if email:
            st.success(f"(Simulated) Alert has been set for {currency} bias changes to {email}.")
        else:
            st.warning("Please enter a valid email address.")


