#!/bin/bash
# Acest script afișează doar deciziile importante, perfect pentru OBS
pm2 logs --nostream --lines 0 | grep --color=never -E "Whale|BUY|SELL|VETO|Score|Eroare|SHOCK|aliniat|ADX|Așteptăm|Istoric|Zombie|Time Stop" | tail -n 50
# Apoi intră în modul live
pm2 logs | grep --color=never -E "Whale|BUY|SELL|VETO|Score|Eroare|SHOCK|aliniat|ADX|Așteptăm|Istoric|Zombie|Time Stop"
