import requests, time
import pandas as pd
from datetime import datetime
from flask import Flask
import threading

# إعدادات البوت
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
TWELVE_API_KEY = "goldapi-16d6wmitsmb3hf9kp-io"

# الأدوات
symbols = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD"
}

# إعداد السيرفر
app = Flask(__name__)

@app.route("/")
def home():
    return "ScalpX bot is running!", 200

# إرسال رسالة إلى تليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except:
        pass

# جلب البيانات من Twelve Data
def fetch_from_twelve(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={TWELVE_API_KEY}&outputsize=100"
    try:
        res = requests.get(url).json()
        if "values" not in res: raise ValueError("Twelve Data Error")
        df = pd.DataFrame(res["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df = df.astype(float)
        return df.sort_index()
    except:
        return None

# جلب البيانات من Yahoo Finance
def fetch_from_yahoo(symbol_yf, interval):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol_yf}?interval={interval}&range=1d"
        res = requests.get(url).json()
        result = res["chart"]["result"][0]
        timestamps = result["timestamp"]
        prices = result["indicators"]["quote"][0]["close"]
        df = pd.DataFrame({"price": prices}, index=pd.to_datetime(timestamps, unit='s'))
        return df.dropna()
    except:
        return None

# تحليل البيانات
def analyze(df):
    df["ma_fast"] = df["price"].rolling(window=3).mean()
    df["ma_slow"] = df["price"].rolling(window=7).mean()
    df["macd"] = df["price"].ewm(span=12, adjust=False).mean() - df["price"].ewm(span=26, adjust=False).mean()
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    entry = round(last["price"], 2)
    tp = round(entry * 1.001, 2)
    sl = round(entry * 0.999, 2)

    signal = None
    if last["ma_fast"] > last["ma_slow"] and prev["ma_fast"] <= prev["ma_slow"] and last["macd"] > last["macd_signal"]:
        signal = "BUY"
    elif last["ma_fast"] < last["ma_slow"] and prev["ma_fast"] >= prev["ma_slow"] and last["macd"] < last["macd_signal"]:
        signal = "SELL"

    if signal:
        accuracy = round(abs((last["macd"] - last["macd_signal"]) * 100), 1)
        return signal, entry, tp, sl, accuracy
    return None

# فحص التوصيات
def check_signals():
    for name, code in symbols.items():
        for interval in ["1min", "15min"]:
            df = fetch_from_twelve(code, interval)
            source = "Twelve Data"

            if df is None or len(df) < 30:
                # التبديل إلى Yahoo
                yahoo_codes = {
                    "GOLD": "XAUUSD=X",
                    "BTC/USD": "BTC-USD",
                    "ETH/USD": "ETH-USD"
                }
                df = fetch_from_yahoo(yahoo_codes[name], "1m" if interval == "1min" else "15m")
                source = "Yahoo Finance"

            if df is None or len(df) < 30:
                send_telegram(f"⚠️ لا توجد بيانات كافية لـ {name} على {interval}.")
                continue

            signal = analyze(df)
            if signal:
                side, entry, tp, sl, acc = signal
                if acc < 50: continue  # فلترة نسب النجاح الضعيفة
                msg = (
                    f"{side} {name}\n"
                    f"نسبة نجاح متوقعة: %{acc}\n"
                    f"دخول: {entry}\n"
                    f"TP: {tp}\n"
                    f"SL: {sl}\n"
                    f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                send_telegram(msg)

# تكرار كل 5 دقائق
def loop():
    while True:
        try:
            check_signals()
        except Exception as e:
            send_telegram(f"❌ خطأ عام: {e}")
        time.sleep(300)

# بدء التشغيل
threading.Thread(target=loop).start()
app.run(host="0.0.0.0", port=10000)
