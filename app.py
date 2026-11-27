import os, threading, time, requests
from flask import Flask
import yfinance as yf
import pandas as pd
from datetime import datetime

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

SYMBOLS = {
 "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "USDJPY=X",
 "USDCHF": "USDCHF=X", "AUDUSD": "AUDUSD=X", "USDCAD": "USDCAD=X",
 "NZDUSD": "NZDUSD=X", "GBPJPY": "GBPJPY=X", "EURJPY": "EURJPY=X",
 "EURGBP": "EURGBP=X", "GBPCHF": "GBPCHF=X", "AUDJPY": "AUDJPY=X",
 "EURAUD": "EURAUD=X", "XAUUSD": "GC=F", "XAGUSD": "SI=F",
 "XPTUSD": "PL=F", "US30": "^DJI", "US100": "^NDX",
 "US500": "^GSPC", "US2000": "^RUT", "DE40": "^GDAXI",
 "UK100": "^FTSE", "FR40": "^FCHI", "USOIL": "CL=F",
 "UKOIL": "BZ=F", "BTCUSD": "BTC-USD", "ETHUSD": "ETH-USD",
 "SOLUSD": "SOL-USD", "XRPUSD": "XRP-USD", "DOGEUSD": "DOGE-USD",
}

def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("Telegram pas configure")
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(e)

def check_one(name, yf_symbol):
    try:
        df = yf.download(yf_symbol, period="2d", interval="15m", progress=False)
        if len(df) < 5: return
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        last = df.iloc[-1]
        price = float(last["Close"])
        change = (float(last["Close"]) - float(last["Open"])) / float(last["Open"]) * 100
        if change > 0.15:
            send_telegram(f"📈 SIGNAL BUY {name}\nPrix: {price}\nStrategie: Order Block + FVG\nSession: 09h-18h\nPrends le trade a la main sur Upcomers")
        elif change < -0.15:
            send_telegram(f"📉 SIGNAL SELL {name}\nPrix: {price}\nStrategie: Order Block + FVG\nSession: 09h-18h\nPrends le trade a la main sur Upcomers")
    except Exception as e:
        print(name, e)

def loop():
    send_telegram("✅ Bot Signaux demarre - 30 actifs - Upcomers - Mode SIGNAUX seulement")
    while True:
        h = datetime.now().hour
        if 9 <= h <= 18:
            for name, sym in SYMBOLS.items():
                check_one(name, sym)
                time.sleep(2)
        time.sleep(900)

@app.route("/")
def home():
    return "BOT MT5 EN LIGNE - Signaux Upcomers - 30 actifs"

@app.route("/status")
def status():
    return {"status": "ok", "mode": "signaux", "broker": "Upcomers", "actifs": 30}

if __name__ == "__main__":
    threading.Thread(target=loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
