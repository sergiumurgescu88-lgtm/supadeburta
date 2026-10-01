#!/usr/bin/env python3
import re, sys, os
SRC = sys.argv[1] if len(sys.argv) > 1 else "strategy_engine_sniper.py"
DST = sys.argv[2] if len(sys.argv) > 2 else "strategy_engine_unified.py"
s = open(SRC, encoding="utf-8").read().replace("\r\n", "\n")

def sub1(pattern, repl, flags=0, label=""):
    global s
    new, n = re.subn(pattern, lambda m: repl, s, flags=flags)
    if n != 1:
        sys.exit(f"EROARE: '{label or pattern[:40]}' a gasit {n} potriviri (asteptat 1). Nu am scris nimic.")
    s = new

sub1(r"^import os, json, logging, time\n", "import os, json, logging, time, fcntl\n", re.M, "import")
sub1(r'/var/log/g4trade-sniper\.log', "/var/log/g4trade-unified.log", 0, "log file")
sub1(r"^ADX_GATE = .*$",
     "ADX_GATE = 25.0           # cerut: 25, pe H1/M15/M30, calculat doar pe lumanari INCHISE\n"
     "REQUIRE_ADX_RISING = True  # ADX curent > ADX de acum ADX_SLOPE_BARS bare inchise\n"
     "ADX_SLOPE_BARS = 3\n"
     "MAX_OPEN_PER_SIDE = 2      # plafon pe CONT (toti botii) pozitii deschise pe aceeasi directie\n"
     "GUARD_MINUTES = 30         # max 1 ordin nou pe directie la 30 min, pe tot contul\n"
     "BOT_NAME = 'unified'\n"
     "DRY_RUN = os.environ.get('DRY_RUN', '1') == '1'   # 1 = doar loguri, NU scrie fisierul de ordin\n"
     "GUARD_FILE = '/root/trinity-fund/shared/account_guard.json'",
     re.M, "ADX_GATE")
sub1(r'"cooldown_state\.json"\)', '"cooldown_state_unified.json")', 0, "STATE_FILE")
sub1(r"^def now\(\): return datetime\.now\(timezone\.utc\)\n",
     "def now(): return datetime.now(timezone.utc)\n"
     "TF_SEC = {'M1': 60, 'M15': 900, 'M30': 1800, 'H1': 3600}\n"
     "def closed(tf):\n"
     "    \"\"\"Doar lumanarile INCHISE (exclude lumanarea in formare).\"\"\"\n"
     "    t = time.time()\n"
     "    return [b for b in bars[tf] if b['t'] + TF_SEC[tf] <= t]\n", re.M, "now()")
sub1(r"^def upsert\(tf, bar\):.*?(?=^def request_hist)",
     "def upsert(tf, bar):\n"
     "    lst = bars[tf]\n"
     "    for i in range(len(lst) - 1, -1, -1):\n"
     "        if lst[i]['t'] == bar['t']:\n"
     "            lst[i] = bar\n"
     "            return\n"
     "        if lst[i]['t'] < bar['t']:\n"
     "            break\n"
     "    lst.append(bar)\n"
     "    lst.sort(key=lambda x: x['t'])\n"
     "    if len(lst) > 500: lst.pop(0)\n\n", re.S | re.M, "upsert")
sub1(r"^def h1_alignment\(\):.*?(?=^def evaluate)",
     "def adx_rising(cb):\n"
     "    if not REQUIRE_ADX_RISING: return True\n"
     "    return adx(cb)[0] > adx(cb[:-ADX_SLOPE_BARS])[0]\n\n"
     "def h1_alignment():\n"
     "    cb = closed('H1')\n"
     "    if len(cb) < 40: return False, 0, 'BUY'\n"
     "    a, p, m = adx(cb)\n"
     "    if a < ADX_GATE: return False, a, 'BUY'\n"
     "    if not adx_rising(cb): return False, a, 'BUY'\n"
     "    return True, a, ('BUY' if p >= m else 'SELL')\n\n", re.S | re.M, "h1_alignment")
sub1(r'^    a15, p15, m15 = adx\(bars\["M15"\]\); a30, p30, m30 = adx\(bars\["M30"\]\)\n',
     "    c15, c30 = closed('M15'), closed('M30')\n"
     "    a15, p15, m15 = adx(c15); a30, p30, m30 = adx(c30)\n", re.M, "adx M15/M30")
sub1(r"^    adx_ok = a15 > ADX_GATE and a30 > ADX_GATE\n",
     "    adx_ok = a15 > ADX_GATE and a30 > ADX_GATE and adx_rising(c15)\n", re.M, "adx_ok")
sub1(r'^    b = bars\["M15"\]\n', "    b = c15\n", re.M, "pullback bars")
sub1(r'^    a = atr14\(bars\["M15"\]\)\n', "    a = atr14(c15)\n", re.M, "atr")
sub1(r"\n    fire\(_pending\)\n", "\n", 0, "fire in evaluate")
sub1(r"^def fire\(sig\):",
     "def dry_mark(sig):\n"
     "    global last_trade_ts, trades_today\n"
     "    last_trade_ts = time.time(); trades_today += 1; _save_state()\n"
     "    log(f\"[DRY-RUN] AR FI TRIMIS: {sig}\")\n\n"
     "def guard_claim(side):\n"
     "    \"\"\"Rezervare atomica (flock): max 1 ordin pe directie la GUARD_MINUTES, pe tot contul. Fail-closed.\"\"\"\n"
     "    try:\n"
     "        os.makedirs(os.path.dirname(GUARD_FILE), exist_ok=True)\n"
     "        with open(GUARD_FILE + '.lock', 'w') as lk:\n"
     "            fcntl.flock(lk, fcntl.LOCK_EX)\n"
     "            try:\n"
     "                with open(GUARD_FILE) as f: claims = json.load(f)\n"
     "            except Exception:\n"
     "                claims = []\n"
     "            t = time.time()\n"
     "            claims = [c for c in claims if t - c['ts'] < 6*3600]\n"
     "            if any(c['side'] == side and t - c['ts'] < GUARD_MINUTES*60 for c in claims):\n"
     "                return False\n"
     "            claims.append({'ts': t, 'side': side, 'bot': BOT_NAME})\n"
     "            tmp = GUARD_FILE + '.tmp'\n"
     "            with open(tmp, 'w') as f: json.dump(claims, f)\n"
     "            os.replace(tmp, GUARD_FILE)\n"
     "            return True\n"
     "    except Exception as e:\n"
     "        log(f'Guard err: {e}')\n"
     "        return False\n\n"
     "def fire(sig):", re.M, "def fire")
sub1(r"^            if _pending:\n                pass\n",
     "            if _pending:\n"
     "                sig, _pending = _pending, None\n"
     "                want = 1 if sig['side'] == 'BUY' else 2\n"
     "                same = [p for p in ops if getattr(p.tradeData, 'tradeSide', 0) == want]\n"
     "                if len(same) >= MAX_OPEN_PER_SIDE:\n"
     "                    log(f\"GUARD: {len(same)} pozitii {sig['side']} deschise pe cont (max {MAX_OPEN_PER_SIDE}) - semnal anulat\")\n"
     "                elif DRY_RUN:\n"
     "                    dry_mark(sig)\n"
     "                elif not guard_claim(sig['side']):\n"
     "                    log(f\"GUARD: alt ordin {sig['side']} in ultimele {GUARD_MINUTES} min - semnal anulat\")\n"
     "                else:\n"
     "                    fire(sig)\n", re.M, "reconcile handler")
sub1(r'^            evaluate\(\)\n            for tf in \("M1", "M15", "M30", "H1"\): request_hist\(tf, count=6\)\n',
     '            for tf in ("M1", "M15", "M30", "H1"): request_hist(tf, count=6)\n'
     "            reactor.callLater(4, safe_evaluate)\n", re.M, "loop order")
sub1(r"^def loop\(\):",
     "def safe_evaluate():\n"
     "    try: evaluate()\n"
     "    except Exception as e: log(f'Err evaluate: {e}')\n\n"
     "def loop():", re.M, "def loop")
sub1(r'log\("=== G4Trade SNIPER v4\.0 \(Ultra-Selective\) ==="\)',
     'log(f"=== G4Trade UNIFIED v5.0 | DRY_RUN={DRY_RUN} | ADX>{ADX_GATE} rising={REQUIRE_ADX_RISING} ===")', 0, "banner")

open(DST, "w", encoding="utf-8").write(s)
print(f"OK: scris {DST} ({len(s.splitlines())} linii). Original neatins: {SRC}")
