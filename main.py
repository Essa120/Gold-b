import requests
import pandas as pd
from flask import Flask
from datetime import datetime
import threading
import time

# إعدادات تيليجرام
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# مفتاح Twelve Data
TWELVE_API_KEY = "goldapi-16d6wmitsm..."

# Flask app
app = Flask(__name__)

# الرموز
symbols = {
    "GOLD": {"td": "XAU/USD", "yf": "XAUUSD=X"},
    "BTC/USD": {"td": "BTC/USD", "yf": "BTC-USD"},
    "ETH/USD": {"td": "ETH/USD", "yf": "ETH-USD"},
}

# سجل التوصيات المرسلة لتفادي التكرار
last_signals = {}

# إرسال رسالة Telegram
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# جلب البيانات من Twelve Data
def fetch_from_twelve(symbol):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=15&apikey={TWELVE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        if "values" not in data:
            raise Exception("No values in Twelve Data response")
        df = pd.DataFrame(data["values"])
        df = df.rename(columns={"datetime": "time", "close": "price"})
        df["time"] = pd.to_datetime(df["time"])
        df["price"] = pd.to_numeric(df["price"])
        df = df.sort_values("time")
        return df.set_index("time")
    except Exception as e:
        raise Exception(f"TwelveData error: {e}")

# جلب البيانات من Yahoo Finance
def fetch_from_yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=15m"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.content.strip().startswith(b'{'):
            raise Exception("Invalid Yahoo response")
        data = response.json()
        result = data["chart"]["result"][0]
        prices = result["indicators"]["quote"][0]["close"]
        timestamps = result["timestamp"]
        df = pd.DataFrame({"price": prices}, index=pd.to_datetime(timestamps, unit="s"))
        return df.dropna()
    except Exception as e:
        raise Exception(f"Yahoo error: {e}")

# تحليل البيانات
def analyze():
    for label, symbol_info in symbols.items():
        try:
            df = fetch_from_twelve(symbol_info["td"])
        except:
            try:
                df = fetch_from_yahoo(symbol_info["yf"])
            except Exception as e:
                send_telegram(f"⚠️ {label}: فشل تحميل البيانات من جميع المصادر\n{e}")
                continue

        if df is None or len(df) < 10:
            continue

        df["fast_ma"] = df["price"].rolling(window=3).mean()
        df["slow_ma"] = df["price"].rolling(window=7).mean()

        if df["fast_ma"].iloc[-1] > df["slow_ma"].iloc[-1] and df["fast_ma"].iloc[-2] <= df["slow_ma"].iloc[-2]:
            signal = "BUY"
        elif df["fast_ma"].iloc[-1] < df["slow_ma"].iloc[-1] and df["fast_ma"].iloc[-2] >= df["slow_ma"].iloc[-2]:
            signal = "SELL"
        else:
            continue

        entry = round(df["price"].iloc[-1], 2)
        tp = round(entry * 1.001, 2) if signal == "BUY" else round(entry * 0.999, 2)
        sl = round(entry * 0.999, 2) if signal == "BUY" else round(entry * 1.001, 2)
        confidence = round(abs(df["fast_ma"].iloc[-1] - df["slow_ma"].iloc[-1]) / entry * 100, 1)

        message = (
            f"{signal} {label}\n"
            f"نسبة نجاح متوقعة: %{confidence}\n"
            f"دخول: {entry}\n"
            f"TP: {tp}\n"
            f"SL: {sl}\n"
            f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if last_signals.get(label) != message:
            send_telegram(message)
            last_signals[label] = message

# تشغيل التحليل دوريًا
@app.route('/')
def index():
    return 'ScalpX bot running'

def run_loop():
    while True:
        analyze()
        time.sleep(300)

if __name__ == '__main__':
    threading.Thread(target=run_loop).start()
    app.run(host="0.0.0.0", port=10000)
