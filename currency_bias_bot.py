# streamlit_ff_heatmap.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import sqlite3
import datetime
import plotly.graph_objects as go

# --- Database setup ---
DB_NAME = "ff_calendar.db"
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS ff_calendar_data (
    date TEXT,
    currency TEXT,
    indicator TEXT,
    actual TEXT,
    forecast TEXT,
    previous TEXT,
    surprise REAL,
    bias TEXT,
    PRIMARY KEY(date, currency, indicator)
)""")
conn.commit()

# --- Currencies to include ---
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD"]

# --- Scraping function ---
def scrape_ff(currency):
    url = "https://www.forexfactory.com/calendar.php"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", id="economicCalendarData")
    rows = []
    release_date = datetime.date.today().isoformat()

    if table:
        for tr in table.find_all("tr", attrs={"data-eventid": True}):
            tds = tr.find_all("td")
            if len(tds) < 7:
                continue
            curr = tds[2].get_text(strip=True)
            if curr != currency:
                continue
            indicator = tds[3].get_text(strip=True)
            actual = tds[4].get_text(strip=True)
            forecast = tds[5].get_text(strip=True)
            previous = tds[6].get_text(strip=True)

            # Convert to numeric for surprise calculation
            def to_num(x):
                try:
                    return float(x.replace(",", "").replace("%", ""))
                except:
                    return np.nan

            act = to_num(actual)
            fore = to_num(forecast)
            surprise = act - fore if not np.isnan(act) and not np.isnan(fore) else np.nan

            # Bias logic: negative indicators
            if "Unemployment" in indicator or "Jobless" in indicator:
                bias = "Bearish" if surprise > 0 else "Bullish" if surprise < 0 else "Neutral"
            else:
                bias = "Bullish" if surprise > 0 else "Bearish" if surprise < 0 else "Neutral"

            rows.append({
                "date": release_date,
                "currency": currency,
                "indicator": indicator,
                "actual": actual,
                "forecast": forecast,
                "previous": previous,
                "surprise": round(surprise, 2) if not np.isnan(surprise) else None,
                "bias": bias
            })
    return pd.DataFrame(rows)

# --- Load from DB or scrape ---
def load_or_scrape(currency):
    today = datetime.date.today().isoformat()
    df = pd.read_sql_query(
        "SELECT * FROM ff_calendar_data WHERE date = ? AND currency = ?",
        conn, params=(today, currency)
    )
    if df.empty:
        df = scrape_ff(currency)
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT OR REPLACE INTO ff_calendar_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (row["date"], row["currency"], row["indicator"],
                 row["actual"], row["forecast"], row["previous"],
                 row["surprise"], row["bias"])
            )
        conn.commit()
    return df

# --- Streamlit App ---
st.set_page_config(page_title="Forex Factory Heatmap", layout="wide")
st.title("🌐 Multi-Currency Economic Heatmap (Forex Factory Live)")

currency = st.selectbox("Select Currency", CURRENCIES)
df = load_or_scrape(currency)

if df.empty:
    st.warning("No data available for today.")
else:
    st.subheader(f"{currency} Economic Calendar — {df['date'].iloc[0]}")
    df_display = df.rename(columns={"date": "Release Date"})
    st.dataframe(df_display[["indicator", "Release Date", "actual", "forecast", "previous", "surprise", "bias"]])

    # Gauge chart for overall bias
    counts = df["bias"].value_counts()
    bullish = counts.get("Bullish", 0)
    bearish = counts.get("Bearish", 0)
    total = bullish + bearish
    pct_bullish = (bullish / total * 100) if total > 0 else 0
    overall = "Bullish" if pct_bullish > 60 else "Bearish" if pct_bullish < 40 else "Neutral"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct_bullish,
        title={"text": f"{currency} Overall Bias: {overall}"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#4CAF50" if overall == "Bullish" else "#F44336"},
            "steps": [
                {"range": [0, 40], "color": "#F44336"},
                {"range": [40, 60], "color": "#FFC107"},
                {"range": [60, 100], "color": "#4CAF50"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Bias Explanations")
    for _, row in df.iterrows():
        st.markdown(f"- **{row['indicator']}** — Actual {row['actual']} vs Forecast {row['forecast']} → Surprise {row['surprise']} → **{row['bias']}**")

conn.close()
