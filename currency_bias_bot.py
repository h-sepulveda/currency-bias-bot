# streamlit_combined_heatmap.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Placeholder DataFrame simulating merged data (World Bank + Forex Factory)
data = [
    {"Indicator": "GDP Growth QoQ", "Actual": 2.4, "Forecast": 2.0, "Previous": 2.1, "Release Date": "2024-12-22"},
    {"Indicator": "Manufacturing PMI", "Actual": 49.5, "Forecast": 50.0, "Previous": 50.2, "Release Date": "2024-12-21"},
    {"Indicator": "Services PMI", "Actual": 52.0, "Forecast": 51.0, "Previous": 50.9, "Release Date": "2024-12-20"},
    {"Indicator": "Retail Sales MoM", "Actual": 0.6, "Forecast": 0.3, "Previous": 0.4, "Release Date": "2024-12-19"},
    {"Indicator": "CPI YoY", "Actual": 3.2, "Forecast": 3.3, "Previous": 3.4, "Release Date": "2024-12-18"},
    {"Indicator": "PPI YoY", "Actual": 2.6, "Forecast": 2.5, "Previous": 2.7, "Release Date": "2024-12-17"},
    {"Indicator": "PCE YoY", "Actual": 3.4, "Forecast": 3.4, "Previous": 3.5, "Release Date": "2024-12-16"},
    {"Indicator": "Wage Growth YoY", "Actual": 4.1, "Forecast": 4.0, "Previous": 4.2, "Release Date": "2024-12-15"},
    {"Indicator": "Unemployment Rate", "Actual": 3.8, "Forecast": 3.7, "Previous": 3.7, "Release Date": "2024-12-14"},
    {"Indicator": "US Initial Jobless Claims", "Actual": 242, "Forecast": 220, "Previous": 230, "Release Date": "2024-12-13"},
    {"Indicator": "JOLTS Job Openings", "Actual": 9.3, "Forecast": 8.8, "Previous": 8.9, "Release Date": "2024-12-12"},
    {"Indicator": "ADP Employment", "Actual": 180, "Forecast": 160, "Previous": 165, "Release Date": "2024-12-11"},
    {"Indicator": "Non-Farm Payroll", "Actual": 215, "Forecast": 190, "Previous": 200, "Release Date": "2024-12-10"},
]

df = pd.DataFrame(data)

# Define logic to assign bias and reasoning
def assess_bias(row):
    if row["Indicator"] in ["Unemployment Rate", "US Initial Jobless Claims"]:
        bias = "Bearish" if row["Actual"] > row["Forecast"] else "Bullish" if row["Actual"] < row["Forecast"] else "Neutral"
    else:
        bias = "Bullish" if row["Actual"] > row["Forecast"] else "Bearish" if row["Actual"] < row["Forecast"] else "Neutral"
    reason = f"Actual: {row['Actual']} vs Forecast: {row['Forecast']} → {bias}"
    return pd.Series([bias, reason])

df[["Bias", "Reason"]] = df.apply(assess_bias, axis=1)

# App layout
st.set_page_config(page_title="Combined Economic Heatmap", layout="wide")
st.title("🌐 Combined Economic Heatmap (World Bank + Forex Factory)")

st.dataframe(df[["Indicator", "Actual", "Forecast", "Previous", "Release Date", "Bias", "Reason"]])

# Scoring summary
bullish = (df["Bias"] == "Bullish").sum()
bearish = (df["Bias"] == "Bearish").sum()
total = bullish + bearish
bullish_pct = (bullish / total) * 100 if total > 0 else 0
final_score = "Bullish" if bullish_pct > 60 else "Bearish" if bullish_pct < 40 else "Neutral"

# Plotly gauge
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=bullish_pct,
    title={"text": f"Overall USD Market Bias: {final_score}"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "#4CAF50" if final_score == "Bullish" else "#F44336"},
        "steps": [
            {"range": [0, 40], "color": "#F44336"},
            {"range": [40, 60], "color": "#FFC107"},
            {"range": [60, 100], "color": "#4CAF50"}
        ]
    }
))
st.plotly_chart(fig, use_container_width=True)

st.markdown(f"**Bullish Signals:** {bullish} | **Bearish Signals:** {bearish} | **Overall Bias:** {final_score}")
