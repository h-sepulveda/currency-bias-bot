# README.md for Currency Bias Bot

## 📈 Currency Macroeconomic Bias Bot

This Streamlit app analyzes macroeconomic indicators (like interest rate, inflation, GDP, etc.) for major currencies and determines a bullish, bearish, or neutral bias based on real-time economic data.

---

## 🚀 Features
- Live data from TradingEconomics API
- Bullish/Bearish/Neutral bias generation based on indicator trends
- Interactive dashboard powered by Streamlit
- Visual bias meter using Plotly
- Email alert placeholder for bias changes
- Multi-country/currency support

---

## 🌍 Supported Currencies / Countries
- USD - United States
- EUR - Euro Area
- JPY - Japan
- GBP - United Kingdom
- CAD - Canada
- AUD - Australia
- CHF - Switzerland

---

## 🧪 Requirements
Create a `requirements.txt` file with the following:
```
streamlit
pandas
requests
plotly
```

---

## 🧑‍💻 How to Run Locally
```bash
# 1. Clone the repository
$ git clone https://github.com/YOUR_USERNAME/currency-bias-bot.git
$ cd currency-bias-bot

# 2. Install dependencies
$ pip install -r requirements.txt

# 3. Run the app
$ streamlit run currency_bias_dashboard.py
```

---

## ☁️ How to Deploy with Streamlit Cloud
1. Push your files to a GitHub repository
2. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. Sign in with GitHub and click **New App**
4. Select your repo and main file: `currency_bias_dashboard.py`
5. Click **Deploy**

Your app will be available at:
```
https://your-username-your-repo.streamlit.app
```

---

## 🔐 API Key Setup
You must sign up at [TradingEconomics](https://developer.tradingeconomics.com/) and replace the placeholder:
```python
API_KEY = "YOUR_TRADINGECONOMICS_API_KEY"
```

---

## ✍️ Author
Hector Sepulveda

---

## 📬 License
MIT License
