# Streamlit Live Economic Heatmap & Bias Tracker (Fixed Region Filtering)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import datetime

# --- DATABASE SETUP ---
DB_NAME = "macro_history.db"
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS macro_data (
    region TEXT,
    indicator TEXT,
    date TEXT,
    actual REAL,
    forecast REAL,
    previous REAL,
    surprise REAL,
    bias TEXT
)''')
conn.commit()

# --- SUPPORTED REGIONS ---
REGIONS = {
    "US": "USD",
    "EU": "EUR",
    "UK": "GBP",
    "JP": "JPY",
    "CA": "CAD"
}

# --- LIVE ECONOMIC CALENDAR SCRAPER ---
def get_live_events():
    url = 'https://www.investing.com/economic-calendar/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', {'id': 'economicCalendarData'})
    events = []
    today = datetime.date.today().isoformat()
    for row in table.tbody.find_all('tr', attrs={'data-eventid': True}):
        cells = row.find_all('td')
        curr = cells[2].get_text(strip=True)
        if curr not in REGIONS.values():
            continue
        event = cells[3].get_text(strip=True)
        actual = cells[4].get_text(strip=True) or None
        forecast = cells[5].get_text(strip=True) or None
        previous = cells[6].get_text(strip=True) or None
        try:
            actual_f = float(actual)
            forecast_f = float(forecast)
            previous_f = float(previous) if previous else None
        except:
            continue
        surprise = round(actual_f - forecast_f, 2)
        bias = 'Bullish' if surprise > 0 else 'Bearish' if surprise < 0 else 'Neutral'
        region_key = next(k for k, v in REGIONS.items() if v == curr)
        events.append({
            'region': region_key,
            'indicator': event,
            'date': today,
            'actual': actual_f,
            'forecast': forecast_f,
            'previous': previous_f,
            'surprise': surprise,
            'bias': bias
        })
    return pd.DataFrame(events)

# --- STREAMLIT APP ---
st.set_page_config(layout="wide")
st.title("🌐 Live Economic Heatmap & Bias Tracker")

# Select region
region = st.selectbox("Select Region/Currency:", list(REGIONS.keys()))

# Fetch live data
st.subheader("📅 Today's Economic Calendar")
df_live = get_live_events()
# Use bracket notation for column access
sub = df_live[df_live['region'] == region]

if sub.empty:
    st.info("No live events for selected region today.")
else:
    st.dataframe(sub[['indicator','actual','forecast','previous','surprise','bias']])
    # explanations per event
    st.markdown("### 🧠 Event Bias Explanations")
    for _, r in sub.iterrows():
        reason = (f"**{r['indicator']}**: Actual {r['actual']} vs Forecast {r['forecast']} "
                  f"→ Surprise {r['surprise']} → **{r['bias']}**")
        st.markdown(f"- {reason}")
    # overall bias
    counts = sub['bias'].value_counts()
    overall = ('Bullish' if counts.get('Bullish',0) > counts.get('Bearish',0)
               else 'Bearish' if counts.get('Bearish',0) > counts.get('Bullish',0)
               else 'Neutral')
    st.markdown(f"## ⚖️ Overall Market Bias: **{overall}**")
    # store to DB
    for _, r in sub.iterrows():
        c.execute(
            "INSERT INTO macro_data VALUES (?,?,?,?,?,?,?,?)",
            (region, r['indicator'], r['date'], r['actual'], r['forecast'], r['previous'], r['surprise'], r['bias'])
        )
    conn.commit()

# Historical data filter
st.subheader("📈 Historical Bias Records")
hist = pd.read_sql_query(
    "SELECT * FROM macro_data WHERE region = ?", conn, params=(region,)
)
# Convert date column to datetime for filtering
hist['date'] = pd.to_datetime(hist['date'])

# date filter
dates = st.date_input(
    "Filter by date range:",
    [datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()]
)
if isinstance(dates, list) and len(dates) == 2:
    start, end = dates
    hist = hist[(hist['date'] >= pd.to_datetime(start)) & (hist['date'] <= pd.to_datetime(end))]

st.dataframe(hist)

# Bias over time chart
time_df = (
    hist.groupby(hist['date'].dt.date)['bias']
        .apply(lambda x: (x=='Bullish').sum()/len(x)*100)
        .reset_index(name='bullish_pct')
)
fig_line = px.line(
    time_df, x='date', y='bullish_pct', title='Bullish Bias % Over Time'
)
st.plotly_chart(fig_line, use_container_width=True)

# CSV Export
st.download_button(
    label="Download Historical Data as CSV",
    data=hist.to_csv(index=False).encode('utf-8'),
    file_name=f'{region}_history.csv',
    mime='text/csv'
)

conn.close()

