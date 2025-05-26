import requests
import pandas as pd
from flask import Flask
from datetime import datetime
import threading
import time

# بيانات بوت Telegram
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# مفاتيح API
TWELVE_API_KEY = "goldapi-16d6wmitsmxxxxxxxxxx"

# إعداد Flask للسيرفر
app = Flask(__name__)

# رموز الأدوات المطلوبة
symbols = {
    "GOLD": {"symbol": "XAU/USD", "yahoo": "GC=F", "twelve": "XAU/USD"},
    "BTC/USD": {"symbol": "BTC/USD", "yahoo": "BTC-USD", "twelve": "BTC/USD"},
    "ETH/USD": {"symbol": "ETH/USD", "yahoo": "ETH-USD", "twelve": "ETH/USD"}
}

# ذاكرة لحفظ آخر توصيات
last_signals = {}

# إرسال رسالة إلى تيليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# تحميل البيانات من Twelve Data
def fetch_from_twelve(symbol):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=15&apikey={TWELVE_API_KEY}"
        r = requests.get(url)
        data = r.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)
            df = df.sort_index()
            df["price"] = df["close"].astype(float)
            return df[["price"]]
        raise Exception("No values found")
    except Exception as e:
        return None

# تحميل البيانات من Yahoo Finance
def fetch_from_yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=15m"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Yahoo error: Invalid HTTP status: {response.status_code}")
        data = response.json()["chart"]["result"][0]
        prices = data["indicators"]["quote"][0]["close"]
        timestamps = data["timestamp"]
        df = pd.DataFrame({"price": prices}, index=pd.to_datetime(timestamps, unit="s"))
        return df.dropna()
    except Exception as e:
        return None

# دالة التحليل الرئيسية
def analyze():
    for name, s in symbols.items():
        df = fetch_from_twelve(s["twelve"])
        source = "Twelve Data"
        if df is None or df.empty:
            df = fetch_from_yahoo(s["yahoo"])
            source = "Yahoo Finance"

        if df is None or len(df) < 10:
            send_telegram(f"⚠️ {s['yahoo']}: فشل تحميل البيانات من جميع المصادر\nYahoo error: Invalid HTTP status: 429")
            continue

        df["fast"] = df["price"].rolling(window=3).mean()
        df["slow"] = df["price"].rolling(window=7).mean()

        signal = None
        if df["fast"].iloc[-1] > df["slow"].iloc[-1] and df["fast"].iloc[-2] <= df["slow"].iloc[-2]:
            signal = "BUY"
        elif df["fast"].iloc[-1] < df["slow"].iloc[-1] and df["fast"].iloc[-2] >= df["slow"].iloc[-2]:
            signal = "SELL"

        if signal:
            entry = round(df["price"].iloc[-1], 2)
            tp = round(entry * 1.001, 2) if signal == "BUY" else round(entry * 0.999, 2)
            sl = round(entry * 0.999, 2) if signal == "BUY" else round(entry * 1.001, 2)
            confidence = round(abs(df["fast"].iloc[-1] - df["slow"].iloc[-1]) / entry * 100, 1)

            msg = f"{signal} {name}\nنسبة نجاح متوقعة: %{confidence}\nدخول: {entry}\nTP: {tp}\nSL: {sl}\nUTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            if last_signals.get(name) != msg:
                send_telegram(msg)
                last_signals[name] = msg

@app.route('/')
def index():
    return 'ScalpX Bot is Running!'

def run_loop():
    while True:
        analyze()
        time.sleep(300)

if __name__ == '__main__':
    threading.Thread(target=run_loop).start()
    app.run(host='0.0.0.0', port=10000)