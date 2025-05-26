import requests, time
import pandas as pd
from datetime import datetime
from flask import Flask
import threading

# إعدادات البوت
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
TWELVE_API_KEY = "goldapi-16d6wmitsm2d9s-io"

# الرموز المراد تحليلها
SYMBOLS = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD",
}

# الفريمات المطلوبة
INTERVALS = ["1min", "15min"]

# دالة إرسال الرسائل إلى تيليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# جلب البيانات من Twelve Data ثم Yahoo في حال الفشل أو نقص البيانات
def fetch_data(symbol, interval):
    base_url = "https://api.twelvedata.com/time_series"
    params = {
