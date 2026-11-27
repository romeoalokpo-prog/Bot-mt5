from flask import Flask, jsonify
import yfinance as yf
import requests, time, threading, traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = "8877516088:AAGdxUGYVTUdVT9yrXSCAXHvNLP4WjElbHE"
CHAT_ID = "7884780716"

ASSETS = {
 "EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X","USDJPY":"USDJPY=X","USDCHF":"USDCHF=X","AUDUSD":"AUDUSD=X","USDCAD":"USDCAD=X","NZDUSD":"NZDUSD=X",
 "GBPJPY":"GBPJPY=X","EURJPY":"EURJPY=X","EURGBP":"EURGBP=X","GBPCHF":"GBPCHF=X","AUDJPY":"AUDJPY=X","EURAUD":"EURAUD=X",
 "XAUUSD":"GC=F","XAGUSD":"SI=F","XPTUSD":"PL=F",
 "US30":"^DJI","US100":"^IXIC","US500":"^GSPC","US2000":"^RUT","DE40":"^GDAXI","UK100":"^FTSE","FR40":"^FCHI",
 "USOIL":"CL=F","UKOIL":"BZ=F",
 "BTCUSD":"BTC-USD","ETHUSD":"ETH-USD","SOLUSD":"SOL-USD","XRPUSD":"XRP-USD","DOGEUSD":"DOGE-USD"
}

CACHE = {"data": [], "time": 0}
BACKTEST_DONE = False

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print("TG error", e)

def in_session():
    h = datetime.now().hour
    return 9 <= h <= 18

def analyse(df):
    if df is None or len(df) < 50:
        return None
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    price = float(close.iloc[-1])
    recent_low = float(low.iloc[-20:-1].min())
    recent_high = float(high.iloc[-20:-1].max())
    prev_low = float(low.iloc[-1])
    prev_high = float(high.iloc[-1])
    mom = (float(close.iloc[-1]) - float(close.iloc[-4])) / float(close.iloc[-4]) * 100
    signal = None
    if prev_low < recent_low and mom > 0.05:
        signal = "ACHAT"
    elif prev_high > recent_high and mom < -0.05:
        signal = "VENTE"
    elif mom > 0.15:
        signal = "ACHAT"
    elif mom < -0.15:
        signal = "VENTE"
    else:
        return None
    atr = float((high.iloc[-14:] - low.iloc[-14:]).mean())
    if atr == 0:
        atr = price * 0.001
    if signal == "ACHAT":
        sl = price - atr * 1.0
        tp1 = price + atr * 1.5
        tp2 = price + atr * 3.0
    else:
        sl = price + atr * 1.0
        tp1 = price - atr * 1.5
        tp2 = price - atr * 3.0
    be = price
    return {"signal": signal, "price": price, "sl": sl, "tp1": tp1, "tp2": tp2, "be": be, "change": round(mom, 2)}

def get_live_one(item):
    name, sym = item
    try:
        df = yf.Ticker(sym).history(period="2d", interval="15m")
        r = analyse(df)
        if not r:
            return None
        return {"symbol": name, "price": round(r["price"], 4), "signal": r["signal"], "sl": round(r["sl"], 4), "tp1": round(r["tp1"], 4), "tp2": round(r["tp2"], 4), "be": round(r["be"], 4), "change": r["change"]}
    except Exception:
        return None

def update_live(send=False):
    try:
        with ThreadPoolExecutor(max_workers=10) as ex:
            res = list(ex.map(get_live_one, ASSETS.items()))
        data = [r for r in res if r]
        if data:
            CACHE["data"] = data
            CACHE["time"] = time.time()
            if send and in_session():
                for s in data[:5]:
                    send_tg(f"📈 SIGNAL LIVE - {s['symbol']}\nSignal: {s['signal']}\nEntree: {s['price']}\nSL: {s['sl']}\nTP1: {s['tp1']}\nTP2: {s['tp2']}\nBE: {s['be']} (apres TP1)\nSession: 09h-18h | OB + FVG + Sweep")
    except Exception:
        print(traceback.format_exc())

def backtest_one(label, period, interval="15m"):
    wins = 0; losses = 0; total = 0
    try:
        for name, sym in ASSETS.items():
            try:
                df = yf.Ticker(sym).history(period=period, interval=interval)
                if df is None or len(df) < 60:
                    continue
                for i in range(50, len(df)-10):
                    sub = df.iloc[i-50:i+1]
                    r = analyse(sub)
                    if not r:
                        continue
                    total += 1
                    fut = df.iloc[i+1:i+11]
                    if len(fut) == 0:
                        continue
                    if r["signal"] == "ACHAT":
                        if float(fut["High"].max()) >= r["tp2"]:
                            wins += 1
                        elif float(fut["Low"].min()) <= r["sl"]:
                            losses += 1
                    else:
                        if float(fut["Low"].min()) <= r["tp2"]:
                            wins += 1
                        elif float(fut["High"].max()) >= r["sl"]:
                            losses += 1
                    if total > 200:
                        break
            except Exception:
                continue
        wr = round(wins/(wins+losses)*100, 1) if (wins+losses) > 0 else 0
        msg = f"🔙 BACKTEST {label} TERMINE\nTrades: {total}\nGagnes: {wins} / Perdus: {losses}\nWinrate: {wr}%\nStrategie: Sweep + OB + FVG | TP structurel | BE structurel"
        print(msg)
        send_tg(msg)
        return msg
    except Exception as e:
        print(traceback.format_exc())
        send_tg(f"❌ BACKTEST {label} ERREUR: {e}")

def run_all_backtests():
    global BACKTEST_DONE
    if BACKTEST_DONE:
        return
    BACKTEST_DONE = True
    time.sleep(5)
    send_tg("🤖 BOT DEMARRE - Je lance les 5 backtests...")
    backtest_one("1 SEMAINE", "5d")
    backtest_one("1 MOIS", "1mo")
    backtest_one("3 MOIS", "3mo")
    backtest_one("6 MOIS", "6mo")
    backtest_one("1 AN", "1y")
    send_tg("✅ LES 5 BACKTESTS SONT FINIS. Je passe en LIVE 09h-18h.")
    update_live(send=True)

@app.route("/")
def home():
    rows = ""
    for s in CACHE["data"]:
        col = "up" if s["signal"] == "ACHAT" else "down"
        rows += f"<tr><td>{s['symbol']}</td><td>{s['price']}</td><td class='{col}'><b>{s['signal']}</b></td><td>{s['sl']}</td><td>{s['tp1']}</td><td>{s['tp2']}</td></tr>"
    if not rows:
        rows = "<tr><td colspan='6'>Chargement... Actualise dans 30s</td></tr>"
    return f"""
    <html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>BOT MT5 - Signaux Upcomers - 30 actifs</title>
    <style>body{{font-family:Arial;background:#0f172a;color:white;padding:15px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #334155;text-align:left;font-size:13px}}.up{{color:#22c55e}}.down{{color:#ef4444}}.box{{background:#1e293b;padding:12px;border-radius:10px}}</style></head>
    <body><h2>🤖 BOT MT5 EN LIGNE</h2><p>Signaux Upcomers - 30 actifs | OB + FVG + Sweep | Session 09h-18h</p><div class='box'><table><tr><th>Actif</th><th>Entree</th><th>Signal</th><th>SL</th><th>TP1</th><th>TP2</th></tr>{rows}</table></div>
    <script>setTimeout(()=>location.reload(),30000);</script></body></html>
    """

@app.route("/api/signals")
def signals():
    if CACHE["data"] and time.time() - CACHE["time"] < 60:
        return jsonify({"signals": CACHE["data"]})
    update_live(send=False)
    return jsonify({"signals": CACHE["data"]})

@app.route("/backtest")
def backtest_route():
    threading.Thread(target=run_all_backtests, daemon=True).start()
    return jsonify({"status": "backtests lances, check Telegram"})

if __name__ == "__main__":
    threading.Thread(target=run_all_backtests, daemon=True).start()
    update_live(send=False)
    app.run(host="0.0.0.0", port=10000)
