#!/bin/bash
cd /root/trinity-fund || { echo "lipseste /root/trinity-fund"; exit 1; }
NOW=$(date +%s)
age() { [ -f "$1" ] && echo $(( NOW - $(stat -c %Y "$1") )) || echo "N/A"; }

echo "=== 0. ORA ==="
date -u; timedatectl 2>/dev/null | grep -E "System clock synchronized|NTP service"

echo; echo "=== 1. PM2 (procese relevante) ==="
pm2 jlist > /tmp/hc_pm2.json 2>/dev/null
python3 - <<'PY'
import json, time
want = ["unified-engine", "sergiu-gold-bot", "live-feed-service",
        "sergiu-strategy-engine", "alpha-sniper-engine", "beta-trend-engine",
        "gamma-scalp-engine", "epsilon-strategy-engine",
        "alpha-gold-bot", "beta-gold-bot", "gamma-gold-bot", "epsilon-gold-bot"]
try:
    procs = {p["name"]: p for p in json.load(open("/tmp/hc_pm2.json"))}
except Exception as ex:
    print("  nu pot citi pm2 jlist:", ex); raise SystemExit
engines_on = []
for n in want:
    p = procs.get(n)
    if not p:
        print(f"  {n:26s} LIPSA"); continue
    e = p["pm2_env"]; up = (time.time()*1000 - e.get("pm_uptime", 0))/60000
    print(f"  {n:26s} {e['status']:8s} restarturi={e.get('restart_time')} uptime={up:.0f}min")
    if n.endswith("engine") and e["status"] == "online": engines_on.append(n)
print("  >> engine-uri care pot trimite ordine:", engines_on or "NICIUNUL")
print("  >> asteptat dupa unificare: doar unified-engine")
PY

echo; echo "=== 2. UNIFIED: stare si ultimele decizii ==="
U=/var/log/g4trade-unified.log
echo "ultimul mesaj acum $(age $U) secunde (>180 = problema)"
grep "UNIFIED v5.0" $U | tail -1 | cut -c1-140
grep -E "Equity|ONLINE" $U | tail -2 | cut -c1-140
tail -n 6 $U | cut -c1-200
echo "erori in ultimele 300 linii: $(tail -n 300 $U | grep -c -E "Err|Guard err|Traceback")"
echo "semnale dry-run/guard pana acum: $(grep -c -E "DRY-RUN|GUARD" $U)"

echo; echo "=== 3. Praguri in fisierele de engine ==="
grep -H -n -E "^ADX_GATE|^DRY_RUN|^MAX_OPEN_PER_SIDE|^COOLDOWN_HOURS" \
  sergiu-flagship/strategy_engine_unified.py alpha-sniper/strategy_engine_sniper.py \
  beta-trend/strategy_engine_trend.py gamma-scalp/strategy_engine_scalp.py \
  epsilon-liquidity/strategy_engine_sniper.py sergiu-flagship/strategy_engine_sniper.py 2>/dev/null | cut -c1-110

echo; echo "=== 4. LANTUL DE EXECUTIE: gold_bot -> cTrader ==="
B=/var/log/g4trade-bot.log
echo "ultimul mesaj gold_bot acum $(age $B) secunde"
grep -E "ONLINE|authenticated|AUTHENTICATED|Found XAUUSD|Disconnected|ORDER FAILED|ORDER ERROR|error" $B | tail -6 | cut -c1-170
echo "--- ultimele ordine trimise:"
grep -E "VALID TRADE|SENDING" $B | tail -6 | cut -c1-150
echo "--- fisiere de ordin ramase neprocesate (nu ar trebui sa existe):"
ls -la /root/ctrader-g4trade-bot/dashboard/static/*_request.json 2>/dev/null || echo "  niciunul (ok)"

echo; echo "=== 5. Dashboard: din ce loguri citeste ==="
grep -n -E "/var/log|pm2|\.log" */dashboard/app.py 2>/dev/null | cut -c1-170 | head -12

echo; echo "=== 6. Fisiere .env (permisiuni) ==="
ls -l */.env /root/ctrader-g4trade-bot/.env 2>/dev/null | awk '{print "  "$1, $NF}'

echo; echo "=== 7. Portar comun ==="
ls -la /root/trinity-fund/shared/ 2>/dev/null || echo "  nu exista inca (se creeaza la primul ordin live)"
echo; echo "GATA. Lipeste tot textul de mai sus in chat."
