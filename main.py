import os
import requests
import pandas as pd
from flask import Flask, request
from datetime import datetime
import threading
import time
from dotenv import load_dotenv

load_dotenv()

# استدعاء البيانات من env
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# إعداد Flask
app = Flask(__name__)

# رموز الأدوات
symbols = {
    "GOLD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD"
}

# إرسال رسالة إلى تيليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# جلب البيانات من Yahoo Finance

def fetch_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=15m"
        response = requests.get(url)
        data = response.json()
        result = data["chart"]["result"][0]
        prices = result["indicators"]["quote"][0]["close"]
        timestamps = result["timestamp"]
        df = pd.DataFrame({"price": prices}, index=pd.to_datetime(timestamps, unit="s"))
        return df.dropna()
    except Exception as e:
        send_telegram(f"⚠️ {symbol}: فشل تحميل البيانات من جميع المصادر\n{str(e)}")
        return None

# تحليل البيانات وإرسال الإشارة
last_signals = {}

def analyze():
    for name, symbol in symbols.items():
        df = fetch_data(symbol)
        if df is None or len(df) < 10:
            continue

        df["fast"] = df["price"].rolling(window=3).mean()
        df["slow"] = df["price"].rolling(window=7).mean()

        if df["fast"].iloc[-1] > df["slow"].iloc[-1] and df["fast"].iloc[-2] <= df["slow"].iloc[-2]:
            signal = "BUY"
        elif df["fast"].iloc[-1] < df["slow"].iloc[-1] and df["fast"].iloc[-2] >= df["slow"].iloc[-2]:
            signal = "SELL"
        else:
            continue

        entry = round(df["price"].iloc[-1], 2)
        tp = round(entry * 1.001, 2) if signal == "BUY" else round(entry * 0.999, 2)
        sl = round(entry * 0.999, 2) if signal == "BUY" else round(entry * 1.001, 2)
        confidence = round(abs(df["fast"].iloc[-1] - df["slow"].iloc[-1]) / entry * 100, 1)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"{signal} {name}\nنسبة نجاح: %{confidence}\nدخول: {entry}\nTP: {tp}\nSL: {sl}\nوقت: {now}"

        if last_signals.get(name) != message:
            send_telegram(message)
            last_signals[name] = message

# نقطة البداية
@app.route('/')
def home():
    return 'ScalpX Bot is Running'

def loop():
    while True:
        analyze()
        time.sleep(300)

if __name__ == '__main__':
    threading.Thread(target=loop).start()
    app.run(host='0.0.0.0', port=10000)
