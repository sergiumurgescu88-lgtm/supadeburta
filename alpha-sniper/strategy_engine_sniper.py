import os, json, logging, time
from datetime import datetime, timezone
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAAccountAuthReq, ProtoOASymbolsListReq,
    ProtoOASubscribeSpotsReq, ProtoOAGetTrendbarsReq, ProtoOAReconcileReq, ProtoOATraderReq)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod
from twisted.internet import reactor

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("/var/log/g4trade-sniper.log"), logging.StreamHandler()])
log = logging.info

env = {}
with open("/root/ctrader-g4trade-bot/.env") as f:
    for line in f:
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
CLIENT_ID, CLIENT_SECRET = env["CT_CLIENT_ID"], env["CT_CLIENT_SECRET"]
ACCESS_TOKEN = env["CT_ACCESS_TOKEN"]
ACCOUNT_ID = int(env.get("CT_ACCOUNT_ID", "48710563"))

SYMBOL = "XAUUSD"
TRADE_FILE = "/root/ctrader-g4trade-bot/dashboard/static/trade_request.json"

# === SNIPER GATES (ultra-strict) ===
ADX_GATE = 35.0           # trend puternic (era 25)
WHALE_GATE = 3.0          # volum instituțional clar (era 3.0)
SCORE_GATE = 85.0         # consens maxim (era 70)
RISK_PCT = 0.04           # 4% equity per trade
MIN_LOTS, MAX_LOTS = 0.10, 0.500  # FIX 1.00 lot = ~100$/pip
ATR_SL_MULT = 1.0         # SL strâns (era 1.5)
RR = 2.0                  # TP = 2x SL
COOLDOWN_HOURS = 2        # minim 6 ore între trade-uri
MAX_PER_DAY = 999999           # maxim 2/zi (era 3)
MAX_SPREAD_PIPS = 50      # nu tranzacționăm spread mare

# Fereastra prime (overlap Londra + NY, lichiditate maximă)
PRIME_HOURS = [(0, 24)]   # 00:00-24:00 UTC (NON-STOP)
ROLLOVER_BLOCK = ((19, 0), (21, 0))
DAILY_BREAK = ((20, 55), (21, 10))

PERIODS = {"M1": ProtoOATrendbarPeriod.M1, "M15": ProtoOATrendbarPeriod.M15, 
           "M30": ProtoOATrendbarPeriod.M30, "H1": ProtoOATrendbarPeriod.H1}

client = None; symbol_id = None; ready = False; bootstrapped = False
spot = {"bid": 0.0, "ask": 0.0, "ts": 0}
bars = {"M1": [], "M15": [], "M30": [], "H1": []}
equity = 5000.0; last_equity_ts = 0
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cooldown_state.json")
def _load_state():
    global last_trade_ts, trades_today, trades_day
    try:
        with open(STATE_FILE) as f: s = json.load(f)
        last_trade_ts = float(s.get("last_trade_ts", 0.0))
        trades_today = int(s.get("trades_today", 0))
        trades_day = datetime.fromisoformat(s["trades_day"]).date() if s.get("trades_day") else None
    except Exception: pass
def _save_state():
    try:
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f: json.dump({"last_trade_ts": last_trade_ts, "trades_today": trades_today, "trades_day": trades_day.isoformat() if trades_day else None}, f)
        os.replace(tmp, STATE_FILE)
    except Exception: pass
last_trade_ts = 0; trades_today = 0; trades_day = None
market_state = "UNKNOWN"; _pending = None
TB_MAP = None

def now(): return datetime.now(timezone.utc)
def send(msg):
    if client: client.send(msg).addErrback(lambda f: log(f"Send err: {type(f.value).__name__}"))

def bar_dict(tb):
    low = getattr(tb, "low", 0)
    return {"t": getattr(tb, "utcTimestampInMinutes", 0) * 60,
            "o": (low + getattr(tb, "deltaOpen", 0)) / 1e5,
            "h": (low + getattr(tb, "deltaHigh", 0)) / 1e5,
            "l": low / 1e5,
            "c": (low + getattr(tb, "deltaClose", 0)) / 1e5,
            "v": getattr(tb, "volume", 0)}

def upsert(tf, bar):
    lst = bars[tf]
    if lst and lst[-1]["t"] == bar["t"]: lst[-1] = bar
    else:
        lst.append(bar)
        if len(lst) > 500: lst.pop(0)

def request_hist(tf, count=400):
    days = {"M1": 0.3, "M15": 3, "M30": 6, "H1": 15}[tf]
    r = ProtoOAGetTrendbarsReq(ctidTraderAccountId=ACCOUNT_ID, symbolId=symbol_id, period=PERIODS[tf])
    r.toTimestamp = int(time.time()*1000)
    r.fromTimestamp = r.toTimestamp - int(days*86400000)
    r.count = count
    send(r)

def adx(bs, period=14):
    if len(bs) < period*2: return 0.0, 0.0, 0.0
    trs, pdms, mdms = [], [], []
    for i in range(1, len(bs)):
        h, l, c = bs[i]["h"], bs[i]["l"], bs[i-1]["c"]
        trs.append(max(h-l, abs(h-c), abs(l-c)))
        up, dn = h-bs[i-1]["h"], bs[i-1]["l"]-l
        pdms.append(up if (up > dn and up > 0) else 0.0)
        mdms.append(dn if (dn > up and dn > 0) else 0.0)
    atr = sum(trs[:period])/period; sp = sum(pdms[:period]); sm = sum(mdms[:period])
    dxs, last = [], (0.0, 0.0)
    for i in range(period, len(trs)):
        atr = (atr*(period-1)+trs[i])/period
        sp = (sp*(period-1)+pdms[i])/period
        sm = (sm*(period-1)+mdms[i])/period
        if atr == 0: continue
        pdi, mdi = 100*sp/atr, 100*sm/atr
        s = pdi+mdi
        dxs.append(100*abs(pdi-mdi)/s if s else 0); last = (pdi, mdi)
    if not dxs: return 0.0, 0.0, 0.0
    a = sum(dxs[:period])/period
    for d in dxs[period:]: a = (a*(period-1)+d)/period
    return a, last[0], last[1]

def atr14(bs, period=14):
    if len(bs) < period+1: return 0.0
    trs = []
    for i in range(1, len(bs)):
        h, l, c = bs[i]["h"], bs[i]["l"], bs[i-1]["c"]
        trs.append(max(h-l, abs(h-c), abs(l-c)))
    a = sum(trs[:period])/period
    for t in trs[period:]: a = (a*(period-1)+t)/period
    return a

def whale():
    b = bars["M1"]
    if len(b) < 22: return 0.0
    avg = sum(x["v"] for x in b[-21:-1])/20
    return (b[-2]["v"]/avg) if avg > 0 else 0.0

def spread_pips():
    if spot["bid"] <= 0 or spot["ask"] <= 0: return 999
    return (spot["ask"] - spot["bid"]) * 10  # XAUUSD: 0.10 = 1 pip

def in_window(n, w): return w[0][0]*60+w[0][1] <= n.hour*60+n.minute < w[1][0]*60+w[1][1]

def is_prime_time():
    n = now()
    return any(s <= n.hour < e for s, e in PRIME_HOURS)

def market_state_now():
    n = now(); wd = n.weekday(); hm = n.hour*60 + n.minute
    if wd == 6:
        if hm >= 21*60+5: return "OPEN"
        if hm >= 19*60+5: return "PRE_OPEN"
        return "CLOSED"
    if wd == 5: return "CLOSED"
    if wd == 4 and hm >= 20*60+55: return "CLOSED"
    return "OPEN"

def blocked_now():
    n = now()
    if in_window(n, DAILY_BREAK): return "PAUZA ZILNICA"
    if in_window(n, ROLLOVER_BLOCK): return "ROLLOVER"
    return None

def tick_alive(): return spot["ts"] and (time.time() - spot["ts"]) < 90

def h1_alignment():
    """Verifică alinierea H1 cu M15/M30"""
    if len(bars["H1"]) < 20: return False, 0, "BUY"
    a, p, m = adx(bars["H1"])
    if a < ADX_GATE: return False, a, "BUY"
    side = "BUY" if p >= m else "SELL"
    return True, a, side

def evaluate():
    global market_state, last_trade_ts, trades_today, trades_day, _pending
    st = market_state_now()
    if st != market_state:
        log(f"🕐 STARE: {st} | tick: {tick_alive()}")
        market_state = st
    if st != "OPEN": return
    if not tick_alive(): return
    blk = blocked_now()
    if blk:
        log(f"🛡️ BLOCK: {blk}")
        return
    if not is_prime_time():
        log(f"⏰ Nu e prime time (13-17 UTC). Așteptăm.")
        return
    spr = spread_pips()
    if spr > MAX_SPREAD_PIPS:
        log(f"📏 Spread prea mare: {spr:.1f} pips > {MAX_SPREAD_PIPS}")
        return
    n = now()
    if trades_day != n.date(): trades_day, trades_today = n.date(), 0
    if trades_today >= MAX_PER_DAY:
        log(f"🛑 Max {MAX_PER_DAY} trade/zi atins")
        return
    hours_since = (time.time() - last_trade_ts) / 3600
    if hours_since < COOLDOWN_HOURS:
        log(f"⏳ Cooldown: {hours_since:.1f}h < {COOLDOWN_HOURS}h")
        return
    if any(len(bars[tf]) < 40 for tf in ("M15", "M30", "H1")) or len(bars["M1"]) < 22:
        return

    # Pilon 1: H1 alignment (trend major)
    h1_ok, h1_adx, h1_side = h1_alignment()
    if not h1_ok:
        log(f"❌ H1 nu aliniat (ADX={h1_adx:.1f}). Așteptăm.")
        return

    # Pilon 2: MTF ADX M15 + M30
    a15, p15, m15 = adx(bars["M15"]); a30, p30, m30 = adx(bars["M30"])
    m15_side = "BUY" if p15 >= m15 else "SELL"
    m30_side = "BUY" if p30 >= m30 else "SELL"
    adx_ok = a15 > ADX_GATE and a30 > ADX_GATE
    if not adx_ok:
        log(f"❌ ADX insuficient: M15={a15:.1f} M30={a30:.1f} (min {ADX_GATE})")
        return

    # Pilon 3: Toate timeframe-urile aliniate pe aceeași direcție
    if not (h1_side == m15_side == m30_side):
        log(f"❌ Timeframe-uri nealiniate: H1={h1_side} M15={m15_side} M30={m30_side}")
        return
    side = h1_side

    # Pilon 4: Whale radar
    wr = whale()
    if wr < WHALE_GATE:
        log(f"👁️ Whale insuficient: {wr:.2f}x (min {WHALE_GATE}x). Așteptăm balena.")
        return

    # Pilon 5: Pullback confirmation (nu intrăm la top/bottom)
    b = bars["M15"]
    if len(b) < 5: return
    cur = b[-1]; prev = b[-2]
    if side == "BUY" and cur["c"] > prev["h"]: 
        log(f"⚠️ Preț deja extins sus. Așteptăm pullback.")
        return
    if side == "SELL" and cur["c"] < prev["l"]:
        log(f"⚠️ Preț deja extins jos. Așteptăm pullback.")
        return

    # Calcul poziție
    entry = spot["ask"] if side == "BUY" else spot["bid"]
    a = atr14(bars["M15"])
    if a <= 0 or entry <= 0: return
    sl = round(entry - ATR_SL_MULT*a, 2) if side == "BUY" else round(entry + ATR_SL_MULT*a, 2)
    dist = abs(entry - sl)
    lots = MAX_LOTS  # FIX 1.00
    tp = round(entry + dist*RR, 2) if side == "BUY" else round(entry - dist*RR, 2)

    # Scor final
    score = 20 + (25 if wr >= 7 else 20 if wr >= 5 else 0) + \
            (25*min(a15/45, 1)) + (15*min(a30/45, 1)) + (15 if h1_adx > 40 else 10)
    log(f"🎯 SNIPER: H1={h1_side}({h1_adx:.1f}) M15={m15_side}({a15:.1f}) M30={m30_side}({a30:.1f}) | whale={wr:.1f}x | score={score:.0f} | {side} entry={entry:.2f} sl={sl} tp={tp} lots={lots} spread={spr:.1f}p")

    if score < SCORE_GATE:
        log(f"❌ Score {score:.0f} < {SCORE_GATE}. Respingem.")
        return

    # Netting check
    send(ProtoOAReconcileReq(ctidTraderAccountId=ACCOUNT_ID))
    _pending = {"side": side, "volume": lots, "stopLoss": sl, "takeProfit": tp, "score": round(score)}

def fire(sig):
    global last_trade_ts, trades_today
    data = {"action": "create", "approved": True, "symbol": SYMBOL, "side": sig["side"],
            "volume": sig["volume"], "stopLoss": sig["stopLoss"], "takeProfit": sig["takeProfit"],
            "comment": f"SNIPER v4.0 score={sig['score']}"}
    tmp = TRADE_FILE + ".tmp"
    with open(tmp, "w") as f: json.dump(data, f)
    os.replace(tmp, TRADE_FILE)
    last_trade_ts = time.time(); trades_today += 1; _save_state()
    log(f"🎯🎯🎯 SEMNAL SNIPER APROBAT: {data}")

def on_connected(c):
    global client
    client = c
    log("Sniper conectat TCP. Auth...")
    send(ProtoOAApplicationAuthReq(clientId=CLIENT_ID, clientSecret=CLIENT_SECRET))

def on_disconnected(c, r):
    log(f"Deconectat: {r}. Reconectare 5s...")
    reactor.callLater(5, client.startService)

def on_message(c, message):
    global symbol_id, ready, bootstrapped, equity, last_equity_ts, _pending
    try:
        m = Protobuf.extract(message); name = type(m).__name__
        if name in ("ProtoHeartbeatEvent", "ProtoOASubscribeSpotsRes"): return
        if name == "ProtoOAApplicationAuthRes":
            send(ProtoOAAccountAuthReq(ctidTraderAccountId=ACCOUNT_ID, accessToken=ACCESS_TOKEN))
        elif name == "ProtoOAAccountAuthRes":
            send(ProtoOASymbolsListReq(ctidTraderAccountId=ACCOUNT_ID))
        elif name == "ProtoOASymbolsListRes":
            for s in m.symbol:
                if getattr(s, "symbolName", "") == SYMBOL: symbol_id = s.symbolId
            log(f"Symbol {SYMBOL} id={symbol_id}")
            send(ProtoOASubscribeSpotsReq(ctidTraderAccountId=ACCOUNT_ID, symbolId=[symbol_id]))
            reactor.callLater(1.0, lambda: request_hist("M1"))
        elif name == "ProtoOASpotEvent":
            spot["bid"] = getattr(m, "bid", 0)/1e5; spot["ask"] = getattr(m, "ask", 0)/1e5
            spot["ts"] = time.time()
        elif name == "ProtoOAGetTrendbarsRes":
            tf = ProtoOATrendbarPeriod.Name(m.period)
            for tb in m.trendbar:
                upsert(tf, bar_dict(tb))
            bars[tf].sort(key=lambda x: x["t"])
            log(f"📥 Istoric {tf}: {len(bars[tf])} bare")
            if not bootstrapped:
                if tf == "M1": reactor.callLater(0.7, lambda: request_hist("M15"))
                elif tf == "M15": reactor.callLater(0.7, lambda: request_hist("M30"))
                elif tf == "M30": reactor.callLater(0.7, lambda: request_hist("H1"))
                elif tf == "H1":
                    bootstrapped = True; ready = True
                    send(ProtoOATraderReq(ctidTraderAccountId=ACCOUNT_ID))
                    log("🟢 SNIPER ONLINE - scanare la 60s (foarte selectiv)")
        elif name == "ProtoOATraderRes":
            tr = m.trader
            bal = getattr(tr, "balance", 0)
            eq = getattr(tr, "equity", 0)
            md = getattr(tr, "moneyDigits", None)
            scale = 10**md if md else 100
            equity = eq/scale if eq > 0 else bal/scale
            last_equity_ts = time.time()
            log(f"💰 Equity: {equity:.2f}")
        elif name == "ProtoOAReconcileRes":
            ops = [p for p in m.position if getattr(p.tradeData, "symbolId", None) == symbol_id]
            if ops:
                log(f"⛔ Poziție {SYMBOL} deschisă ({len(ops)}) - semnal anulat")
                _pending = None
            elif _pending:
                fire(_pending); _pending = None
    except Exception as e:
        log(f"Err mesaj: {e}")

def loop():
    global last_equity_ts
    try:
        if bootstrapped:
            evaluate()
            for tf in ("M1", "M15", "M30", "H1"): request_hist(tf, count=6)
            if time.time() - last_equity_ts > 300:
                last_equity_ts = time.time()
                send(ProtoOATraderReq(ctidTraderAccountId=ACCOUNT_ID))
    except Exception as e:
        log(f"Err evaluate: {e}")
    reactor.callLater(60, loop)

if __name__ == "__main__":
    log("="*60)
    log("=== G4Trade SNIPER v4.0 (Ultra-Selective) ===")
    _load_state()
    log(f"💾 STATE: last_trade_ts={last_trade_ts:.0f} | trades_today={trades_today} (persistat pe disc)")
    log(f"ADX>{ADX_GATE} | Whale>{WHALE_GATE}x | Score>{SCORE_GATE}")
    log(f"Lot FIX: {MAX_LOTS} | Risk: {RISK_PCT*100}% | Max {MAX_PER_DAY}/zi")
    log(f"Prime time: {PRIME_HOURS} UTC | Cooldown: {COOLDOWN_HOURS}h")
    log(f"Multi-TF alignment: H1 + M15 + M30 toate pe aceeași direcție")
    log("="*60)
    client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
    client.setConnectedCallback(on_connected)
    client.setDisconnectedCallback(on_disconnected)
    client.setMessageReceivedCallback(on_message)
    client.startService()
    reactor.callLater(10, loop)
    reactor.run()
