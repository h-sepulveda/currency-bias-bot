# economic_heatmap.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import datetime
import sqlite3

# --- Setup ---
DB_NAME = "macro_snapshots.db"
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS calendar_data (
        currency TEXT,
        date TEXT,
        indicator TEXT,
        actual TEXT,
        forecast TEXT,
        previous TEXT,
        surprise REAL,
        impact TEXT
    )
""")
conn.commit()

# --- Currencies ---
CURRENCIES = {"USD": "US Dollar", "EUR": "Euro", "JPY": "Japanese Yen"}

# --- Scraper ---
def scrape_calendar(currency="USD"):
    url = "https://www.investing.com/economic-calendar/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find("table", {"id": "economicCalendarData"})
    rows = []

    if table:
        for row in table.tbody.find_all("tr", {"data-eventid": True}):
            tds = row.find_all("td")
            if not tds or tds[2].get_text(strip=True) != currency:
                continue
            try:
                ind = tds[3].get_text(strip=True)
                actual = tds[4].get_text(strip=True)
                forecast = tds[5].get_text(strip=True)
                previous = tds[6].get_text(strip=True)

                def to_num(x):
                    try: return float(x.replace('%','').replace('K','').replace(',',''))
                    except: return np.nan

                act_f = to_num(actual)
                for_f = to_num(forecast)
                surprise = act_f - for_f if not np.isnan(act_f) and not np.isnan(for_f) else np.nan
                impact = "Bullish" if surprise > 0 else "Bearish" if surprise < 0 else "Neutral"

                rows.append({
                    "currency": currency,
                    "date": str(datetime.date.today()),
                    "indicator": ind,
                    "actual": actual,
                    "forecast": forecast,
                    "previous": previous,
                    "surprise": round(surprise, 2) if not np.isnan(surprise) else '',
                    "impact": impact
                })
            except:
                continue
    return pd.DataFrame(rows)

# --- Get or fallback ---
def load_or_scrape(currency):
    today = str(datetime.date.today())
    df = scrape_calendar(currency)
    if not df.empty:
        for _, row in df.iterrows():
            c.execute("""
                INSERT INTO calendar_data (currency, date, indicator, actual, forecast, previous, surprise, impact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (row["currency"], row["date"], row["indicator"], row["actual"], row["forecast"], row["previous"], row["surprise"], row["impact"]))
        conn.commit()
    else:
        df = pd.read_sql_query("SELECT * FROM calendar_data WHERE currency=? ORDER BY date DESC LIMIT 15", conn, params=(currency,))
    return df

# --- Streamlit App ---
st.set_page_config(layout="wide")
st.title("🌐 Multi-Currency Economic Heatmap (Live + Fallback)")

selected = st.selectbox("Select Currency", list(CURRENCIES.keys()), format_func=lambda x: f"{x} - {CURRENCIES[x]}")
df = load_or_scrape(selected)

if df.empty:
    st.warning("No data available.")
else:
    st.subheader(f"Economic Calendar: {CURRENCIES[selected]}")
    st.dataframe(df[['indicator','actual','forecast','previous','surprise','impact']])

    counts = df['impact'].value_counts()
    pct = counts.get('Bullish', 0) / len(df) * 100

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        title={'text': f"{selected} Bullish %"},
        gauge={'axis': {'range': [0, 100]},
               'bar': {'color': "#4a90e2"},
               'steps': [
                   {'range': [0, 40], 'color': "#d0021b"},
                   {'range': [40, 60], 'color': "#9b9b9b"},
                   {'range': [60, 100], 'color': "#4a90e2"}
               ]}
    ))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Bias Explanations")
    for _, row in df.iterrows():
        st.markdown(f"- **{row['indicator']}**: Actual {row['actual']} vs Forecast {row['forecast']} → Surprise {row['surprise']} → **{row['impact']}**")

conn.close()
