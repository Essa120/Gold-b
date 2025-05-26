import requests
import pandas as pd
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# إعدادات البوت
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_KEY = "4641d466300d46c587952fd42f03e811"

# الأدوات المدعومة
symbols = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD"
}

# الفريمات المستخدمة
intervals = ["1min", "15min"]

# إرسال رسالة إلى تيليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# جلب بيانات الأداة
def fetch_data(symbol, interval):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=100&apikey={API_KEY}"
        res = requests.get(url)
        data = res.json()

        if "values" not in data:
            raise ValueError(data.get("message", "No data found."))

        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df = df.astype(float).sort_index()
        return df
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol} [{interval}]: {e}")
        return None

# حساب MACD
def compute_macd(df):
    exp1 = df["close"].ewm(span=12, adjust=False).mean()
    exp2 = df["close"].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# توليد إشارات الشراء والبيع
def generate_signals():
    for name, symbol in symbols.items():
        for interval in intervals:
            df = fetch_data(symbol, interval)
            if df is None or len(df) < 35:
                continue

            df["fast_ma"] = df["close"].rolling(window=3).mean()
            df["slow_ma"] = df["close"].rolling(window=7).mean()
            df["macd"], df["signal"] = compute_macd(df)

            price = df["close"].iloc[-1]
            tp = round(price * 1.001, 2)
            sl = round(price * 0.999, 2)

            # BUY شرط
            if (
                df["fast_ma"].iloc[-1] > df["slow_ma"].iloc[-1]
                and df["fast_ma"].iloc[-2] <= df["slow_ma"].iloc[-2]
                and df["macd"].iloc[-1] > df["signal"].iloc[-1]
            ):
                success = round((df["macd"].iloc[-1] - df["signal"].iloc[-1]) * 100, 1)
                if success >= 0.5:
                    msg = (
                        f"BUY {name}\n"
                        f"نسبة نجاح متوقعة: %{success}\n"
                        f"دخول: {round(price, 2)}\n"
                        f"TP: {tp}\n"
                        f"SL: {sl}\n"
                        f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_telegram(msg)

            # SELL شرط
            if (
                df["fast_ma"].iloc[-1] < df["slow_ma"].iloc[-1]
                and df["fast_ma"].iloc[-2] >= df["slow_ma"].iloc[-2]
                and df["macd"].iloc[-1] < df["signal"].iloc[-1]
            ):
                success = round(abs(df["macd"].iloc[-1] - df["signal"].iloc[-1]) * 100, 1)
                if success >= 0.5:
                    msg = (
                        f"SELL {name}\n"
                        f"نسبة نجاح متوقعة: %{success}\n"
                        f"دخول: {round(price, 2)}\n"
                        f"TP: {tp}\n"
                        f"SL: {sl}\n"
                        f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_telegram(msg)

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
