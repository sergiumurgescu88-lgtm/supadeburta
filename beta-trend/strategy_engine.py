import os, json, logging, time
from datetime import datetime, timezone
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAAccountAuthReq, ProtoOASymbolsListReq,
    ProtoOASubscribeSpotsReq, ProtoOAGetTrendbarsReq, ProtoOAReconcileReq, ProtoOATraderReq
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod
from twisted.internet import reactor

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("/var/log/g4trade-strategy.log"), logging.StreamHandler()])
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
BLACKLIST_FILE = "/root/ctrader-g4trade-bot/news_blacklist.json"
WEEK_CLOSE = (4, 20, 55)
DAILY_BREAK = ((20, 55), (21, 10))
ROLLOVER_BLOCK = ((19, 0), (20, 0))
NEWS_MINUTES = 15
ADX_GATE, WHALE_GATE, SCORE_GATE = 25.0, 1.8, 65.0
RISK_PCT = 0.10  # Test Adi: 10% risc per trade pentru a atinge 1 lot
MIN_LOTS, MAX_LOTS = 1.00, 1.00  # Test Adi: Fortam 1 Lot fix
ATR_MULT_SL, RR = 1.5, 3.0
COOLDOWN_MIN, MAX_PER_DAY = 45, 3
PERIODS = {"M1": ProtoOATrendbarPeriod.M1, "M15": ProtoOATrendbarPeriod.M15, "M30": ProtoOATrendbarPeriod.M30}
SILENT = {"ProtoOASubscribeSpotsRes", "ProtoOAHeartbeatEvent"}

client = None; symbol_id = None; ready = False; bootstrapped = False
spot = {"bid": 0.0, "ask": 0.0, "ts": 0}
bars = {"M1": [], "M15": [], "M30": []}
equity = 10000.0
last_equity_ts = 0
last_trade_ts = 0; trades_today = 0; trades_day = None
market_state = "UNKNOWN"; _pending = None; TB_MAP = None

def now(): return datetime.now(timezone.utc)
def send(msg):
    if client: client.send(msg).addErrback(lambda f: log(f"Send err: {type(f.value).__name__}"))

def in_window(n, w): return w[0][0]*60+w[0][1] <= n.hour*60+n.minute < w[1][0]*60+w[1][1]

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
    if in_window(n, DAILY_BREAK): return "PAUZA ZILNICA 23:55-00:10"
    if False: return "ROLLOVER 22:00-23:00 EET"
    try:
        with open(BLACKLIST_FILE) as f: bl = json.load(f)
        for ev in bl:
            et = datetime.fromisoformat(ev.replace("Z", "+00:00"))
            if abs((n - et).total_seconds()) < NEWS_MINUTES*60: return f"STIRE {ev}"
    except Exception: pass
    return None

def tick_alive(): return spot["ts"] and (time.time() - spot["ts"]) < 90

def request_hist(tf, count=400):
    days = {"M1": 0.25, "M15": 3, "M30": 6}[tf]
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

def upsert(tf, bar):
    lst = bars[tf]
    if lst and lst[-1]["t"] == bar["t"]: lst[-1] = bar
    else:
        lst.append(bar)
        if len(lst) > 400: lst.pop(0)


def bar_dict(tb):
    # cTrader trimite bare delta-codate: low absolut + delta fata de low
    low = getattr(tb, "low", 0)
    return {"t": getattr(tb, "utcTimestampInMinutes", 0) * 60,
            "o": (low + getattr(tb, "deltaOpen", 0)) / 1e5,
            "h": (low + getattr(tb, "deltaHigh", 0)) / 1e5,
            "l": low / 1e5,
            "c": (low + getattr(tb, "deltaClose", 0)) / 1e5,
            "v": getattr(tb, "volume", 0)}

def evaluate():
    global market_state, last_trade_ts, trades_today, trades_day, _pending
    st = market_state_now()
    if st != market_state:
        log(f"🕐 STARE PIATA: {st} | tick live: {tick_alive()}")
        market_state = st
    if st == "CLOSED": return
    if st == "PRE_OPEN":
        log("🔭 PRE-OPEN: scanare & calibrare indicatori (fara intrari)")
        return
    if not tick_alive():
        log("⚠️ Fara tick-uri >90s -> pauza (piata inchisa de facto)")
        return
    blk = blocked_now()
    if blk:
        log(f"🛡️ FILTRU MACRO: {blk} - fara intrari")
        return
    n = now()
    if trades_day != n.date(): trades_day, trades_today = n.date(), 0
    if trades_today >= MAX_PER_DAY: return
    if (time.time() - last_trade_ts) < COOLDOWN_MIN*60: return
    if len(bars["M15"]) < 40 or len(bars["M30"]) < 40 or len(bars["M1"]) < 22: return

    a15, p15, m15 = adx(bars["M15"]); a30, p30, m30 = adx(bars["M30"])
    best = max((a15, p15, m15), (a30, p30, m30))
    adx_ok = best[0] > ADX_GATE
    wr = whale(); whale_ok = wr >= WHALE_GATE
    side = "BUY" if best[1] >= best[2] else "SELL"
    entry = spot["ask"] if side == "BUY" else spot["bid"]
    a = atr14(bars["M15"])
    if a <= 0 or entry <= 0: return
    sl = round(entry - ATR_MULT_SL*a, 2) if side == "BUY" else round(entry + ATR_MULT_SL*a, 2)
    dist = abs(entry - sl)
    lots = round((equity*RISK_PCT)/(dist*100), 2) if dist > 0 else 0
    lots = max(MIN_LOTS, min(MAX_LOTS, lots))  # Fortam volumul in limite
    size_ok = MIN_LOTS <= lots <= MAX_LOTS   # Verificam dupa fortare
    tp = round(entry + dist*RR, 2) if side == "BUY" else round(entry - dist*RR, 2)
    score = 20 + (30 if wr >= 4 else 22 if whale_ok else 0) + (30*min(best[0]/40, 1) if adx_ok else 0) + (20 if size_ok else 0)
    log(f"📊 SCAN: ADX M15={a15:.1f} M30={a30:.1f} | whale={wr:.1f}x | score={score:.0f} | {side} entry={entry:.2f} sl={sl} tp={tp} lots={lots}")
    if not (adx_ok and size_ok and score >= SCORE_GATE): return  # Whale e acum bonus de scor, nu blocare
    _pending = {"side": side, "volume": lots, "stopLoss": sl, "takeProfit": tp, "score": round(score)}
    send(ProtoOAReconcileReq(ctidTraderAccountId=ACCOUNT_ID))

def fire(sig):
    global last_trade_ts, trades_today
    data = {"action": "create", "approved": True, "symbol": SYMBOL, "side": sig["side"],
            "volume": sig["volume"], "stopLoss": sig["stopLoss"], "takeProfit": sig["takeProfit"],
            "comment": f"G4Trade v3.2 score={sig['score']}"}
    tmp = TRADE_FILE + ".tmp"
    with open(tmp, "w") as f: json.dump(data, f)
    os.replace(tmp, TRADE_FILE)
    last_trade_ts = time.time(); trades_today += 1
    log(f"🚀 SEMNAL APROBAT TRIMIS CATRE BOT: {data}")

def on_connected(c):
    global client
    client = c
    log("Strategy engine conectat TCP. Auth...")
    send(ProtoOAApplicationAuthReq(clientId=CLIENT_ID, clientSecret=CLIENT_SECRET))

def on_disconnected(c, r):
    log(f"Deconectat: {r}. Reconectare 5s...")
    reactor.callLater(5, client.startService)

def on_message(c, message):
    global symbol_id, ready, bootstrapped, equity, _pending
    try:
        m = Protobuf.extract(message); name = type(m).__name__
        if name in ("ProtoHeartbeatEvent",) or name in SILENT: return
        if name == "ProtoOAApplicationAuthRes":
            send(ProtoOAAccountAuthReq(ctidTraderAccountId=ACCOUNT_ID, accessToken=ACCESS_TOKEN))
        elif name == "ProtoOAAccountAuthRes":
            send(ProtoOASymbolsListReq(ctidTraderAccountId=ACCOUNT_ID))
        elif name == "ProtoOASymbolsListRes":
            for s in m.symbol:
                if getattr(s, "symbolName", "") == SYMBOL: symbol_id = s.symbolId
            log(f"Symbol {SYMBOL} id={symbol_id}. Abonare spot...")
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
                elif tf == "M30":
                    bootstrapped = True; ready = True
                    send(ProtoOATraderReq(ctidTraderAccountId=ACCOUNT_ID))
                    log("🟢 STRATEGY ENGINE ONLINE - scanare continua la 60s")
        elif name == "ProtoOATraderRes":
            tr = m.trader
            bal = getattr(tr, "balance", 0)
            eq = getattr(tr, "equity", 0)
            md = getattr(tr, "moneyDigits", None)
            scale = 10**md if md else 100
            real_eq = eq/scale if eq > 0 else bal/scale
            global equity; equity = real_eq
            log(f"💰 Equity: {equity:.2f} (balance={bal/scale:.2f}, equity_raw={eq/scale:.2f})")
        elif name == "ProtoOAReconcileRes":
            ops = [p for p in m.position if getattr(p.tradeData, "symbolId", None) == symbol_id]
            if ops and _pending:
                log(f"🔄 Pozitie {SYMBOL} deschisa ({len(ops)}) - se inchide automat pentru semnal nou")
                from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOAClosePositionReq
                for pos in ops:
                    pos_id = getattr(pos, "positionId", 0)
                    vol = getattr(pos.tradeData, "volume", 0)
                    if pos_id and vol > 0:
                        close_req = ProtoOAClosePositionReq()
                        close_req.ctidTraderAccountId = ACCOUNT_ID
                        close_req.positionId = pos_id
                        close_req.volume = vol
                        send(close_req)
                        log(f"   📤 ClosePositionReq trimis: posId={pos_id} vol={vol}")
                time.sleep(1)
                fire(_pending); _pending = None
            elif ops:
                log(f"⛔ Pozitie {SYMBOL} deschisa ({len(ops)}) - fara semnal nou, se pastreaza")
            elif _pending:
                fire(_pending); _pending = None
        elif name == "ProtoOAErrorRes":
            log(f"❌ cTrader ErrorRes: {getattr(m,'errorCode','?')} | {getattr(m,'description','')}")
    except Exception as e:
        log(f"Err mesaj: {e}")

def loop():
    global last_equity_ts
    try:
        if bootstrapped:
            evaluate()
            for tf in ("M1", "M15", "M30"): request_hist(tf, count=6)
            if time.time() - last_equity_ts > 300:
                last_equity_ts = time.time()
                send(ProtoOATraderReq(ctidTraderAccountId=ACCOUNT_ID))
    except Exception as e:
        log(f"Err evaluate: {e}")
    reactor.callLater(60, loop)

if __name__ == "__main__":
    log("="*60)
    log("=== G4Trade STRATEGY ENGINE v3.2.1 (Institutional) ===")
    log(f"ADX>{ADX_GATE} M15/M30 | Whale>{WHALE_GATE}x | Score>{SCORE_GATE} | Risk {RISK_PCT*100}%")
    log("="*60)
    client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
    client.setConnectedCallback(on_connected)
    client.setDisconnectedCallback(on_disconnected)
    client.setMessageReceivedCallback(on_message)
    client.startService()
    reactor.callLater(10, loop)
    reactor.run()
