import os, time, threading, requests
import pandas as pd
import yfinance as yf
from flask import Flask
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")

app = Flask(__name__)

symbols = {
    'XAUUSD': 'XAU/USD',
    'BTC-USD': 'BTC/USD',
    'ETH-USD': 'ETH/USD'
}

interval_map = {
    '1m': '1m',
    '5m': '5m',
    '15m': '15m',
    '30m': '30m'
}

last_signals = {}

def get_data(symbol, interval):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={TWELVE_API_KEY}&outputsize=100"
        response = requests.get(url)
        data = response.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={"datetime": "time"})
            df["time"] = pd.to_datetime(df["time"])
            df = df.astype(float, errors='ignore')
            df = df.sort_values("time")
            return df
        else:
            raise Exception("No values found")
    except:
        try:
            df = yf.download(tickers=symbol, interval=interval, period="1d", progress=False)
            if not df.empty:
                df = df.reset_index()
                df = df.rename(columns={"Datetime": "time"})
                return df
        except:
            return None
    return None

def analyze():
    for yf_symbol, alias in symbols.items():
        sent = False
        for interval in interval_map:
            df = get_data(yf_symbol, interval)
            if df is None or len(df) < 20:
                continue

            df['sma'] = df['close'].rolling(window=9).mean()
            df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()

            signal = ''
            if df['close'].iloc[-1] > df['sma'].iloc[-1] and df['macd'].iloc[-1] > 0:
                signal = 'BUY'
            elif df['close'].iloc[-1] < df['sma'].iloc[-1] and df['macd'].iloc[-1] < 0:
                signal = 'SELL'

            if signal:
                price = df['close'].iloc[-1]
                entry_key = f"{alias}-{signal}-{interval}"
                if entry_key == last_signals.get(alias):
                    return
                last_signals[alias] = entry_key

                tp = round(price * 1.001, 2) if signal == 'BUY' else round(price * 0.999, 2)
                sl = round(price * 0.999, 2) if signal == 'BUY' else round(price * 1.001, 2)
                text = f"{signal} {alias}\nنسبة نجاح متوقعة: 0.2%\nدخول: {price}\nTP: {tp}\nSL: {sl}\nUTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                send_message(text)
                sent = True
                break

        if not sent:
            send_message(f"⚠️ لا توجد بيانات كافية لـ {alias} على جميع الفريمات المتاحة.")

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=data)
    except:
        pass

@app.route('/')
def home():
    return "ScalpX Bot is Running!"

def run_bot():
    while True:
        analyze()
        time.sleep(300)

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)
