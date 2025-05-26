import requests
import pandas as pd
from datetime import datetime
from flask import Flask

app = Flask(__name__)

# إعدادات التوكن و Chat ID
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_KEY = "4641d466300d46c587952fd42f03e811"

# الأدوات المطلوبة
symbols = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD"
}

# إرسال رسالة تيليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# جلب بيانات من Twelve Data
def fetch_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"
    try:
        res = requests.get(url)
        data = res.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)
            df = df.astype(float)
            return df.sort_index()
        else:
            raise ValueError(data.get("message", "Unknown error"))
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol} [{interval}]: {e}")
        return None

# تحليل EMA + MACD وإصدار توصيات
def analyze_signals(symbol, df):
    df["EMA5"] = df["close"].ewm(span=5).mean()
    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["MACD"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
    df["Signal"] = df["MACD"].ewm(span=9).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = round(latest["close"], 2)
    time = latest.name.strftime('%Y-%m-%d %H:%M:%S')

    signal = None
    if latest["EMA5"] > latest["EMA20"] and prev["EMA5"] <= prev["EMA20"] and latest["MACD"] > latest["Signal"]:
        signal = "BUY"
    elif latest["EMA5"] < latest["EMA20"] and prev["EMA5"] >= prev["EMA20"] and latest["MACD"] < latest["Signal"]:
        signal = "SELL"

    if signal:
        tp = round(price * 1.001, 2)
        sl = round(price * 0.999, 2)
        success_chance = round(abs((latest["MACD"] - latest["Signal"]) * 100), 2)
        msg = (
            f"{signal} {symbol}\n"
            f"نسبة نجاح متوقعة: %{success_chance}\n"
            f"دخول: {price}\n"
            f"TP: {tp}\n"
            f"SL: {sl}\n"
            f"UTC {time}"
        )
        send_telegram(msg)

# تنفيذ الدورة الكاملة
def run_bot():
    for name, code in symbols.items():
        df = fetch_data(code, "1min")
        if df is not None and len(df) >= 30:
            analyze_signals(name, df)

@app.route("/")
def home():
    return "Scalping Bot is Running!"

@app.route("/run")
def manual_run():
    send_telegram("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")
    run_bot()
    return "Bot Executed!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
