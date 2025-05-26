import requests
import pandas as pd
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# إعدادات البوت
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_KEY = "4641d466300d46c587952fd42f03e811"

# الأدوات ورموزها من Twelve Data
symbols = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD"
}

intervals = ["1min", "15min"]

# إرسال رسالة إلى تليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# جلب بيانات من Twelve Data API
def fetch_data(symbol, interval):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=30&apikey={API_KEY}"
        res = requests.get(url)
        data = res.json()

        if "values" not in data:
            raise ValueError(data.get("message", "Unknown error"))

        df = pd.DataFrame(data["values"])
        df = df.astype({"close": float})
        df = df.sort_values("datetime")
        return df
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol} [{interval}]: {e}")
        return None

# حساب التوصيات بناءً على تقاطع المتوسطات + MACD
def generate_signals():
    for name, symbol in symbols.items():
        all_signals = []
        for interval in intervals:
            df = fetch_data(symbol, interval)
            if df is None or len(df) < 26:
                continue

            df["fast_ma"] = df["close"].rolling(window=5).mean()
            df["slow_ma"] = df["close"].rolling(window=12).mean()

            # MACD
            exp1 = df["close"].ewm(span=12, adjust=False).mean()
            exp2 = df["close"].ewm(span=26, adjust=False).mean()
            df["macd"] = exp1 - exp2
            df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()

            if (
                df["fast_ma"].iloc[-1] > df["slow_ma"].iloc[-1] and
                df["macd"].iloc[-1] > df["signal"].iloc[-1]
            ):
                direction = "BUY"
            elif (
                df["fast_ma"].iloc[-1] < df["slow_ma"].iloc[-1] and
                df["macd"].iloc[-1] < df["signal"].iloc[-1]
            ):
                direction = "SELL"
            else:
                continue

            price = round(df["close"].iloc[-1], 2)
            tp = round(price * (1.001 if direction == "BUY" else 0.999), 2)
            sl = round(price * (0.999 if direction == "BUY" else 1.001), 2)
            success_chance = round(abs(df["macd"].iloc[-1] - df["signal"].iloc[-1]) * 100, 1)

            msg = (
                f"{direction} {name}\n"
                f"نسبة نجاح متوقعة: %{success_chance}\n"
                f"دخول: {price}\nTP: {tp}\nSL: {sl}\n"
                f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            all_signals.append(msg)

        for m in all_signals:
            send_telegram(m)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/run')
def run_now():
    send_telegram("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")
    generate_signals()
    return "Bot executed."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
