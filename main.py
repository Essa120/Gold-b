import requests
import pandas as pd
from flask import Flask
from datetime import datetime
import time

app = Flask(__name__)

BOT_TOKEN = "توكن_البوت"
CHAT_ID = "معرف_الشات"

symbols = {
    "GOLD": "XAUUSD=X",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^NDX"
}

# ترتيب الأدوات بالدور للتقليل من ضغط الطلبات
symbol_list = list(symbols.items())
symbol_index = 0

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except:
        pass

def fetch_yahoo_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=15m"
        res = requests.get(url)
        if res.status_code == 429:
            raise Exception("⚠️ HTTP 429 - Too Many Requests")
        data = res.json()
        result = data.get("chart", {}).get("result", [])[0]
        prices = result["indicators"]["quote"][0]["close"]
        timestamps = result["timestamp"]
        df = pd.DataFrame({"price": prices}, index=pd.to_datetime(timestamps, unit='s'))
        return df.dropna()
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol}: {e}")
        return None

def generate_signal():
    global symbol_index
    name, symbol = symbol_list[symbol_index]
    symbol_index = (symbol_index + 1) % len(symbol_list)

    df = fetch_yahoo_data(symbol)
    if df is None or len(df) < 10:
        return

    df["fast"] = df["price"].rolling(window=3).mean()
    df["slow"] = df["price"].rolling(window=7).mean()

    if df["fast"].iloc[-1] > df["slow"].iloc[-1] and df["fast"].iloc[-2] <= df["slow"].iloc[-2]:
        entry = round(df["price"].iloc[-1], 2)
        tp = round(entry * 1.001, 2)
        sl = round(entry * 0.999, 2)
        msg = (
            f"BUY {name}\n"
            f"دخول: {entry}\n"
            f"TP: {tp}\n"
            f"SL: {sl}\n"
            f"الوقت: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        send_telegram(msg)

@app.route('/')
def home():
    return "Bot Running!"

@app.route('/run')
def run():
    generate_signal()
    return "Signal checked."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
