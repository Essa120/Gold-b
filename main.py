import requests
import pandas as pd
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# إعدادات البوت
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
TWELVE_DATA_API_KEY = "4641d466300d46c587952fd42f03e811"

# الأدوات المدعومة
symbols = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD"
}

# إرسال رسالة إلى تليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# جلب البيانات من Twelve Data
def fetch_data(symbol):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=30&apikey={TWELVE_DATA_API_KEY}"
        res = requests.get(url)
        data = res.json()

        if "values" not in data:
            raise ValueError(data.get("message", "No data"))

        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df = df.sort_index()
        df["price"] = df["close"].astype(float)
        return df
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol}: {e}")
        return None

# توليد الإشارات
def generate_signals():
    for name, symbol in symbols.items():
        df = fetch_data(symbol)
        if df is None or len(df) < 10:
            continue

        df["fast_ma"] = df["price"].rolling(window=3).mean()
        df["slow_ma"] = df["price"].rolling(window=7).mean()

        # BUY signal
        if (
            df["fast_ma"].iloc[-1] > df["slow_ma"].iloc[-1]
            and df["fast_ma"].iloc[-2] <= df["slow_ma"].iloc[-2]
        ):
            entry = round(df["price"].iloc[-1], 2)
            tp = round(entry * 1.001, 2)
            sl = round(entry * 0.999, 2)
            msg = (
                f"BUY {name}\n"
                f"دخول: {entry}\n"
                f"TP: {tp}\n"
                f"SL: {sl}\n"
                f"الوقت: {datetime.utcnow().strftime('%H:%M:%S %d-%m-%Y')} UTC"
            )
            send_telegram(msg)

        # SELL signal
        elif (
            df["fast_ma"].iloc[-1] < df["slow_ma"].iloc[-1]
            and df["fast_ma"].iloc[-2] >= df["slow_ma"].iloc[-2]
        ):
            entry = round(df["price"].iloc[-1], 2)
            tp = round(entry * 0.999, 2)
            sl = round(entry * 1.001, 2)
            msg = (
                f"SELL {name}\n"
                f"دخول: {entry}\n"
                f"TP: {tp}\n"
                f"SL: {sl}\n"
                f"الوقت: {datetime.utcnow().strftime('%H:%M:%S %d-%m-%Y')} UTC"
            )
            send_telegram(msg)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/run')
def run_now():
    generate_signals()
    return "Executed!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
