from flask import Flask
import requests
import pandas as pd
import time

app = Flask(__name__)

BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

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

def format_signal_message(name, signal, price, tp, sl):
    return f"""{signal} {name}

دخول: {price}
الهدف (TP): {tp}
وقف الخسارة (SL): {sl}
"""

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

def check_signals():
    for name, symbol in symbols.items():
        try:
            df = get_data(symbol)
            if df.empty or len(df) < 2:
                raise ValueError("Not enough data")

            df["EMA5"] = df["Close"].ewm(span=5).mean()
            df["EMA20"] = df["Close"].ewm(span=20).mean()

            last = df.iloc[-1]
            prev = df.iloc[-2]

            signal = None
            if prev["EMA5"] < prev["EMA20"] and last["EMA5"] > last["EMA20"]:
                signal = "BUY"
            elif prev["EMA5"] > prev["EMA20"] and last["EMA5"] < last["EMA20"]:
                signal = "SELL"

            if signal:
                entry = round(last["Close"], 2)
                tp = round(entry * 1.001, 2)
                sl = round(entry * 0.999, 2)
                msg = format_signal_message(name, signal, entry, tp, sl)
                send_telegram(msg)

        except Exception as e:
            send_telegram(f"Error with {name}: {str(e)}")

        time.sleep(5)  # تأخير 5 ثواني بين كل أداة لتجنب الحظر

@app.route('/')
def home():
    return "Bot is running!"

# إشعار عند التشغيل
send_telegram("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")

# فحص الإشارات فور التشغيل
check_signals()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
