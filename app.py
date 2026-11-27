from flask import Flask, jsonify
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
import time, traceback

app = Flask(__name__)

ASSETS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","USDCHF=X",
"EURGBP=X","EURJPY=X","GBPJPY=X","XAUUSD=X","XAGUSD=X","BTC-USD","ETH-USD",
"US30","US500","NAS100","UK100","DE40","JP225","WTI","BRENT","NG=F",
"AAPL","MSFT","GOOGL","AMZN","TSLA","NVDA","META","NFLX"]

CACHE = {"data": [], "time": 0}

def get_one(sym):
    try:
        df = yf.Ticker(sym).history(period="1d", interval="15m")
        if df is None or len(df) < 20:
            return None
        price = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-20])
        change = (price - prev) / prev * 100
        signal = "ACHAT" if change > 0 else "VENTE"
        return {"symbol": sym, "price": round(price, 4), "change": round(change, 2), "signal": signal}
    except Exception:
        return None

def update():
    try:
        with ThreadPoolExecutor(max_workers=10) as ex:
            res = list(ex.map(get_one, ASSETS))
        data = [r for r in res if r]
        if data:
            CACHE["data"] = data
            CACHE["time"] = time.time()
    except Exception:
        print(traceback.format_exc())

@app.route("/")
def home():
    return """
    <html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>BOT MT5 EN LIGNE - Signaux Upcomers - 30 actifs</title>
    <style>body{font-family:Arial;background:#0f172a;color:white;padding:15px}table{width:100%;border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #334155;text-align:left}.up{color:#22c55e}.down{color:#ef4444}.box{background:#1e293b;padding:12px;border-radius:10px}</style></head>
    <body><h2>🤖 BOT MT5 EN LIGNE</h2><p>Signaux Upcomers - 30 actifs</p><div class='box' id='box'>Chargement...</div>
    <script>
    async function load(){
      try{
        let r = await fetch('/api/signals'); let j = await r.json();
        if(!j.signals || !j.signals.length){ document.getElementById('box').innerHTML='Pas de données, réessaie dans 30s...'; return; }
        let h='<table><tr><th>Actif</th><th>Prix</th><th>Signal</th></tr>';
        j.signals.forEach(s=>{ h+=`<tr><td>${s.symbol}</td><td>${s.price}</td><td class='${s.signal=='ACHAT'?'up':'down'}'><b>${s.signal}</b> (${s.change}%)</td></tr>` });
        document.getElementById('box').innerHTML=h+'</table>';
      }catch(e){ document.getElementById('box').innerHTML='Erreur de chargement, actualise.'; }
    }
    load(); setInterval(load, 30000);
    </script></body></html>
    """

@app.route("/api/signals")
def signals():
    if CACHE["data"] and time.time() - CACHE["time"] < 60:
        return jsonify({"signals": CACHE["data"]})
    update()
    return jsonify({"signals": CACHE["data"]})

if __name__ == "__main__":
    update()
    app.run(host="0.0.0.0", port=10000)
