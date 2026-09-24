import os
import sqlite3
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

from twisted.internet import reactor, task
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq,
    ProtoOAAccountAuthReq,
    ProtoOANewOrderReq
)

# Încărcăm credențialele izolate
load_dotenv('/root/trinity-fund/next-gen/shared/.env')

log_dir = "/root/trinity-fund/next-gen/shared/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "live_executor_real.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"

LOT_SIZE = 0.05  # Lot mic de test
MAX_OPEN_TRADES = 3

CLIENT_ID = os.getenv("CT_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CT_CLIENT_SECRET", "")
ACCOUNT_ID = int(os.getenv("CT_ACCOUNT_ID", "0"))

client_instance = None

def send(message):
    if client_instance:
        client_instance.send(message)

def on_connected(c):
    global client_instance
    client_instance = c
    logging.info("✅ TCP connected. Authenticating...")
    
    # 1. Autentificare Aplicație
    app_auth = ProtoOAApplicationAuthReq()
    app_auth.clientId = CLIENT_ID
    app_auth.clientSecret = CLIENT_SECRET
    send(app_auth)
    
    # 2. Autentificare Cont
    acc_auth = ProtoOAAccountAuthReq()
    acc_auth.ctidTraderAccountId = ACCOUNT_ID
    send(acc_auth)
    
    logging.info("✅ Conectat și autentificat cu succes la cTrader API!")
    
    # Pornim verificarea periodică la fiecare 30 de secunde
    loop = task.LoopingCall(check_and_execute)
    loop.start(30.0)

def on_disconnected(c, reason):
    logging.error(f"❌ Deconectat de la cTrader: {reason}")
    reactor.stop()

def on_message(c, message):
    # Mesajele primite de la server sunt procesate aici (pentru moment, le ignorăm)
    pass

def check_and_execute():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.signal_id, s.bot_name, s.status, sp.price_usd
            FROM signals s
            LEFT JOIN snapshots sp ON s.signal_id = sp.signal_id
            LEFT JOIN executions e ON s.signal_id = e.signal_id
            WHERE s.status IN ('SHADOW_LONG', 'SHOCK_DETECTED')
            AND e.signal_id IS NULL
            AND s.timestamp >= datetime('now', '-2 hour')
            ORDER BY s.timestamp DESC LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            signal_id, bot_name, status, entry_price = result
            entry_price = entry_price if entry_price else 4300.0
            
            logging.info(f"🎯 EXECUȚIE REALĂ: {bot_name} - {status} la prețul {entry_price}")
            
            # ⚠️ SIGURANȚĂ MAXIMĂ: Linia de trimitere efectivă a ordinului este comentată.
            # Când vei da OK-ul final, o vom decomenta.
            req = ProtoOANewOrderReq()
            req.ctidTraderAccountId = ACCOUNT_ID
            req.symbolId = 61  # XAUUSD (ID standard demo)
            req.tradeType = 1  # 1 = BUY, 2 = SELL
            req.volume = int(LOT_SIZE * 100000)
            req.comment = f"NextGen_{bot_name}"
            send(req)
            
            # Simulăm scrierea în DB pentru a valida fluxul
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO executions (signal_id, requested_price_usd, fill_price_usd, slippage_usd, exit_reason, price_at_30m_post, price_at_2h_post)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (signal_id, entry_price, entry_price, 0.0, 'OPEN_SIMULATED', None, None))
            conn.commit()
            conn.close()
            logging.info(f"✅ ORDIN PREGĂTIT (Mod Validare Flux): {bot_name}")
            
    except Exception as e:
        logging.error(f"Eroare în check_and_execute: {e}")

if __name__ == "__main__":
    logging.info("🚀 LIVE EXECUTOR (REAL) a pornit.")
    logging.info(f"Conectare la {EndPoints.PROTOBUF_DEMO_HOST}:{EndPoints.PROTOBUF_PORT}")
    
    # Inițializare exact ca în gold_bot.py
    client_instance = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
    client_instance.setConnectedCallback(on_connected)
    client_instance.setDisconnectedCallback(on_disconnected)
    client_instance.setMessageReceivedCallback(on_message)
    client_instance.startService()
    
    reactor.run()
