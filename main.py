import requests, time
import pandas as pd
from datetime import datetime
from flask import Flask
import threading

# إعدادات البوت
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
TWELVE_API_KEY = "goldapi-16d6wmitsn4c3y-io"

app = Flask(__name__)

symbols = ["XAU/USD", "BTC/USD", "ETH/USD"]
timeframes = ["1min", "15min"]

# دالة لإرسال رسالة لتيليجرام
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

# دالة لجلب بيانات من Twelve Data وإذا فشلت يستعمل Yahoo

def fetch_data(symbol, interval):
    base_url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "apikey": TWELVE_API_KEY,
        "outputsize": 100
    }
    try:
        r = requests.get(base_url, params=params)
        data = r.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)
            df = df.astype(float)
            return df
        else:
            raise Exception("No values found")
    except Exception as e:
        send_telegram(f"⚡️ Error with Twelve Data ({symbol}): {e}\nSwitching to Yahoo Finance...")
        return fetch_yahoo_data(symbol, interval)

# يحول الرمز إلى تنسيق Yahoo

def convert_symbol_yahoo(sym):
    if sym == "XAU/USD": return "XAUUSD=X"
    elif sym == "BTC/USD": return "BTC-USD"
    elif sym == "ETH/USD": return "ETH-USD"
    return sym

# دالة مساعدة لجلب بيانات من Yahoo Finance

def fetch_yahoo_data(symbol, interval):
    try:
        import yfinance as yf
        y_symbol = convert_symbol_yahoo(symbol)
        tf_map = {"1min": "1m", "15min": "15m"}
        data = yf.download(tickers=y_symbol, interval=tf_map[interval], period="1d")
        data = data[["Open", "High", "Low", "Close"]]
        data.columns = ["open", "high", "low", "close"]
        return data
    except Exception as e:
        send_telegram(f"❌ Failed to fetch Yahoo data for {symbol}: {e}")
        return None

# دالة التحليل وإرسال التوصية

def analyze(symbol, tf):
    df = fetch_data(symbol, tf)
    if df is None or len(df) < 20:
        send_telegram(f"⚠️ لا توجد بيانات كافية ل {symbol} على {tf}.")
        return

    last = df.iloc[-1]
    prev = df.iloc[-2]
    signal = ""

    if last["close"] > prev["high"]:
        signal = "BUY"
    elif last["close"] < prev["low"]:
        signal = "SELL"

    if signal:
        entry = round(last["close"], 2)
        sl = round(entry * (0.998 if signal == "BUY" else 1.002), 2)
        tp = round(entry * (1.002 if signal == "BUY" else 0.998), 2)
        percent = round(abs(tp - entry) / entry * 100, 1)
        send_telegram(f"{signal} {symbol}\nنسبة نجاح متوقعة: %{percent}\nدخول: {entry}\nTP: {tp}\nSL: {sl}\nUTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

# تشغيل من خلال خيط مستقل

def run():
    while True:
        for sym in symbols:
            for tf in timeframes:
                analyze(sym, tf)
        time.sleep(300)

@app.route('/')
def home():
    return "ScalpX is running"

@app.route('/run')
def runner():
    thread = threading.Thread(target=run)
    thread.start()
    return "✔️ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7"

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
