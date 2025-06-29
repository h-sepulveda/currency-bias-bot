# Streamlit Economic Heatmap with Full US Data + Bias Logic

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime

st.set_page_config(layout="wide")
st.title("🇺🇸 US Economic Heatmap - Multi Indicator Bias Tracker")

# --- Sample Realistic Placeholder Data (Live source can be added later) ---
data = [
    ["GDP Growth QoQ", -0.5, -0.2, 2.4],
    ["Manufacturing PMIs", 48.5, 49.3, 48.7],
    ["Services PMIs", 49.9, 52, 51.6],
    ["Retail Sales MoM", -0.9, -0.5, 0.1],
    ["CPI YoY", 2.4, 2.5, 2.3],
    ["PPI YOY", 2.5, 2.5, 2.6],
    ["PCE YOY", 2.7, 2.6, 2.5],
    ["Wage Growth YoY", 3.9, 2.6, 3.9],
    ["Unemployment Rate", 4.2, 4.2, 4.2],
    ["US Initial Jobless Claims", 236000, 245000, 246000],
    ["JOLTS Job Openings", 7.39, 7.11, 7.2],
    ["ADP", 37000, 111000, 62000],
    ["Non-Farm Payroll", 139000, 130000, 147000],
    ["House Price Index", 434.9, None, 436.7],
    ["US MBA Mortgage", 1.1, None, -2.6]
]

df = pd.DataFrame(data, columns=["Indicator", "Actual", "Forecast", "Previous"])

def evaluate_bias(row):
    try:
        actual = float(row["Actual"])
        forecast = float(row["Forecast"])
    except:
        return "Neutral", "No clear comparison"

    diff = actual - forecast
    direction = "Bullish" if diff > 0 else "Bearish" if diff < 0 else "Neutral"

    reasoning = f"Actual: {actual}, Forecast: {forecast}, Surprise: {diff:+.2f} → {direction}"
    return direction, reasoning

df[["Bias", "Explanation"]] = df.apply(lambda row: pd.Series(evaluate_bias(row)), axis=1)

# --- Display Table ---
st.subheader("US Economic Indicators")
st.dataframe(df[["Indicator", "Actual", "Forecast", "Previous", "Bias"]])

# --- Indicator Explanations ---
st.subheader("🧠 Explanation Per Indicator")
for _, row in df.iterrows():
    st.markdown(f"**{row['Indicator']}** → {row['Explanation']}")

# --- Overall Bias Summary ---
bullish_count = (df['Bias'] == 'Bullish').sum()
bearish_count = (df['Bias'] == 'Bearish').sum()
total_count = bullish_count + bearish_count

if total_count == 0:
    final_bias = "Neutral"
else:
    final_bias = "Bullish" if bullish_count > bearish_count else "Bearish"

score = round((bullish_count - bearish_count) / len(df) * 100, 2)

st.markdown(f"### ⚖️ Overall Market Bias: **{final_bias}**")
st.markdown(f"- **Bullish Signals:** {bullish_count}")
st.markdown(f"- **Bearish Signals:** {bearish_count}")
st.markdown(f"- **Score:** {score:+.2f} → Overall sentiment **{final_bias}**")

# --- Bias Gauge ---
gauge_value = max(min((bullish_count / len(df)) * 100, 100), 0)
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=gauge_value,
    title={'text': "Bullish % Score"},
    gauge={
        'axis': {'range': [0, 100]},
        'bar': {'color': "#4a90e2"},
        'steps': [
            {'range': [0, 40], 'color': "#d0021b"},
            {'range': [40, 60], 'color': "#9b9b9b"},
            {'range': [60, 100], 'color': "#4a90e2"}
        ]
    }
))
st.plotly_chart(fig, use_container_width=True)

