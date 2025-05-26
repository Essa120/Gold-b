import os
import json

# مسار ملف حفظ التوصيات السابقة
LAST_SIGNALS_FILE = "last_signals.json"

# تحميل آخر توصيات إذا كان الملف موجودًا
if os.path.exists(LAST_SIGNALS_FILE):
    with open(LAST_SIGNALS_FILE, "r") as f:
        last_signals = json.load(f)
else:
    last_signals = {}

# دالة توليد مفتاح فريد للتوصية
def generate_signal_key(symbol, action, price, tp, sl):
    return f"{symbol}_{action}_{round(price, 2)}_{round(tp, 2)}_{round(sl, 2)}"

# تعديل دالة إرسال التوصيات

def send_signal(symbol, action, price, tp, sl):
    key = generate_signal_key(symbol, action, price, tp, sl)
    
    if key in last_signals:
        print("توصية مكررة - لن يتم إرسالها")
        return

    last_signals[key] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    with open(LAST_SIGNALS_FILE, "w") as f:
        json.dump(last_signals, f)

    message = f"{action} {symbol}\nنسبة نجاح متوقعة: %2\nدخول: {price}\nTP: {tp}\nSL: {sl}\nUTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    send_message(message)
