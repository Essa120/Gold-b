import requests
import pandas as pd
from datetime import datetime
from flask import Flask
import threading
import time

app = Flask(__name__)

BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

symbols = {
    "GOLD": "XAUUSD",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^NDX"
}

def send_message(text):
    try:
        requests.post(SEND_URL, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Failed to send message:", e)

def fetch_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
        response = requests.get(url)
        data = response.json()
        timestamps = data['chart']['result'][0]['timestamp']
        prices = data['chart']['result'][0]['indicators']['quote'][0]['close']
        df = pd.DataFrame({"Time": pd.to_datetime(timestamps, unit='s'), "Price": prices})
        df = df.dropna().reset_index(drop=True)
        return df
    except Exception as e:
        raise RuntimeError(f"Error fetching {symbol}: {e}")

def analyze(df):
    try:
        df['MA5'] = df['Price'].rolling(window=5).mean()
        df['MA10'] = df['Price'].rolling(window=10).mean()
        if df['MA5'].iloc[-2] < df['MA10'].iloc[-2] and df['MA5'].iloc[-1] > df['MA10'].iloc[-1]:
            return True  # Buy Signal
        return False
    except Exception as e:
        raise RuntimeError(f"Analysis error: {e}")

def monitor():
    while True:
        for name, symbol in symbols.items():
            try:
                df = fetch_data(symbol)
                if len(df) < 10:
                    continue
                if analyze(df):
                    entry = df['Price'].iloc[-1]
                    tp = round(entry * 1.001, 2)
                    sl = round(entry * 0.999, 2)
                    time_str = df['Time'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')
                    message = f"BUY {name}\n\nدخول: {entry}\nTP: {tp}\nSL: {sl}\nTime: {time_str}"
                    send_message(message)
            except Exception as e:
                send_message(f"Error with {name}: {e}")
        time.sleep(300)  # Wait 5 minutes

@app.route("/")
def index():
    return "Bot is running!"

def start():
    send_message("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")
    threading.Thread(target=monitor).start()

if __name__ == '__main__':
    start()
    app.run(host='0.0.0.0', port=10000)
