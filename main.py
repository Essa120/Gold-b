from flask import Flask
import requests
import pandas as pd
import time

app = Flask(__name__)

# إعدادات تيليجرام
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# رموز الأدوات
symbols = {
    "GOLD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^NDX"
}

def get_data(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}?interval=1m&range=1d"
    df = pd.read_csv(url)
    return df

def check_signals():
    for name, symbol in symbols.items():
        try:
            df = get_data(symbol)
            if df.empty or len(df) < 2:
                raise ValueError("Not enough data")

            df["EMA5"] = df["Close"].ewm(span=5).mean()
            df["EMA20"] = df["Close"].ewm(span=20).mean()

            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]

            signal = None
            if prev_row["EMA5"] < prev_row["EMA20"] and last_row["EMA5"] > last_row["EMA20"]:
                signal = "BUY"
            elif prev_row["EMA5"] > prev_row["EMA20"] and last_row["EMA5"] < last_row["EMA20"]:
                signal = "SELL"

            if signal:
                close_price = last_row["Close"]
                tp = round(close_price * 1.001, 2)
                sl = round(close_price * 0.999, 2)

                msg = f"""{signal} {name}

دخول:
{name} @ {round(close_price, 2)}

الهدف (TP):
{name} @ {tp}

وقف الخسارة (SL):
{name} @ {sl}
"""
                send_telegram(msg)

        except Exception as e:
            send_telegram(f"Error with {name}: {str(e)}")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

@app.route('/')
def home():
    return 'Bot is running!'

# إشعار تشغيل السيرفر
send_telegram("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")

# تنفيذ الفحص مرة واحدة عند التشغيل (يمكنك تعديلها لاحقًا لتكون دورية)
check_signals()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
