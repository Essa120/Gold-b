import requests
import pandas as pd
from datetime import datetime
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_KEY = "4641d466300d46c587952fd42f03e811"

symbols = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD"
}

intervals = ["1min", "15min"]
TP_SPREAD = 0.001  # 0.1%
SL_SPREAD = 0.001


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})


def fetch_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"
    response = requests.get(url)
    try:
        data = response.json()
        if "values" not in data:
            raise ValueError(data.get("message", "No data"))
        df = pd.DataFrame(data["values"])
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        return df.sort_index()
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol} [{interval}]: {e}")
        return None


def ta_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def ta_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line


def calculate_indicators(df):
    df["fast_ma"] = df["close"].rolling(window=3).mean()
    df["slow_ma"] = df["close"].rolling(window=7).mean()
    df["rsi"] = ta_rsi(df["close"], 14)
    df["macd"], df["macd_signal"] = ta_macd(df["close"])
    df["vol_avg"] = df["volume"].rolling(window=10).mean()
    return df


def generate_signals():
    for name, symbol in symbols.items():
        df_1m = fetch_data(symbol, "1min")
        df_15m = fetch_data(symbol, "15min")
        if df_1m is None or df_15m is None or len(df_1m) < 30 or len(df_15m) < 30:
            continue

        df_1m = calculate_indicators(df_1m)
        df_15m = calculate_indicators(df_15m)

        last = df_1m.iloc[-1]
        prev = df_1m.iloc[-2]
        trend_15m = df_15m["fast_ma"].iloc[-1] > df_15m["slow_ma"].iloc[-1]
        downtrend_15m = df_15m["fast_ma"].iloc[-1] < df_15m["slow_ma"].iloc[-1]

        green_candle = last["close"] > last["open"]
        red_candle = last["close"] < last["open"]
        high_volume = last["volume"] > last["vol_avg"]

        # BUY conditions
        buy = (
            prev["fast_ma"] <= prev["slow_ma"] < last["fast_ma"] > last["slow_ma"] and
            last["macd"] > last["macd_signal"] and
            last["rsi"] < 70 and
            trend_15m and green_candle and high_volume
        )

        # SELL conditions
        sell = (
            prev["fast_ma"] >= prev["slow_ma"] > last["fast_ma"] < last["slow_ma"] and
            last["macd"] < last["macd_signal"] and
            last["rsi"] > 30 and
            downtrend_15m and red_candle and high_volume
        )

        price = round(last["close"], 2)
        tp = round(price * (1 + TP_SPREAD), 2)
        sl = round(price * (1 - TP_SPREAD), 2)

        if buy:
            msg = (
                f"BUY {name}\n"
                f"نسبة نجاح متوقعة: %99\n"
                f"دخول: {price}\nTP: {tp}\nSL: {sl}\n"
                f"الفريم: 1m + تأكيد 15m\n"
                f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_telegram(msg)
        elif sell:
            msg = (
                f"SELL {name}\n"
                f"نسبة نجاح متوقعة: %99\n"
                f"دخول: {price}\nTP: {sl}\nSL: {tp}\n"
                f"الفريم: 1m + تأكيد 15m\n"
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
