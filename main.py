import requests
import pandas as pd
from flask import Flask
from datetime import datetime
import time

app = Flask(__name__)

# إعدادات البوت
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# الأدوات ورموزها من Yahoo Finance
symbols = {
    "GOLD": "XAUUSD=X",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^NDX"
}

# إرسال رسالة إلى تليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# جلب البيانات من Yahoo Finance مع حماية من الأخطاء

def fetch_yahoo_data(symbol, retries=3):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=15m"
    for attempt in range(retries):
        try:
            res = requests.get(url)
            if res.status_code != 200:
                raise ValueError(f"HTTP Error: {res.status_code}")
            data = res.json()
            result = data.get("chart", {}).get("result")
            if not result:
                raise ValueError("Empty result")
            indicators = result[0]["indicators"]["quote"][0]
            timestamps = result[0]["timestamp"]
            df = pd.DataFrame({"price": indicators["close"]}, index=pd.to_datetime(timestamps, unit='s'))
            return df.dropna()
        except Exception as e:
            if attempt == retries - 1:
                send_telegram(f"Error with {symbol}: {e}")
            time.sleep(1)  # انتظار بين المحاولات
    return None

# توليد الإشارات بنسبة نجاح عالية فقط
def generate_signals():
    for name, symbol in symbols.items():
        df = fetch_yahoo_data(symbol)
        if df is None or len(df) < 10:
            continue

        df["fast_ma"] = df["price"].rolling(window=3).mean()
        df["slow_ma"] = df["price"].rolling(window=7).mean()

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # شرط نجاح عالي: تقاطع حاد + ارتفاع واضح + عدم تقاطع سابق قريب
        if (
            latest["fast_ma"] > latest["slow_ma"]
            and prev["fast_ma"] <= prev["slow_ma"]
           
