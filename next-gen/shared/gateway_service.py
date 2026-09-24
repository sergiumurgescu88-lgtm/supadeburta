import os
import sqlite3
import time
import logging
from dotenv import load_dotenv
from twisted.internet import reactor, task
from ctrader_open_api import Client, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAAccountAuthReq, ProtoOANewOrderReq
)

load_dotenv('/root/trinity-fund/next-gen/shared/.env')

log_dir = "/root/trinity-fund/next-gen/shared/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "gateway.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"
CLIENT_ID = os.getenv("CT_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CT_CLIENT_SECRET", "")
ACCOUNT_ID = int(os.getenv("CT_ACCOUNT_ID", "0"))

client_instance = None
is_connected = False

def start_client():
    global client_instance
    try:
        logging.info("🔌 Inițializare client cTrader...")
        client_instance = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
        client_instance.setConnectedCallback(on_connected)
        client_instance.setDisconnectedCallback(on_disconnected)
        client_instance.setMessageReceivedCallback(on_message)
        
        # Verificăm dinamic ce metodă de start este disponibilă în librărie
        if hasattr(client_instance, 'startService'):
            client_instance.startService()
        elif hasattr(client_instance, 'connect'):
            client_instance.connect()
        else:
            logging.error("❌ Client cTrader nu are nici startService, nici connect. Verifică versiunea librăriei ctrader_open_api.")
            
    except AttributeError as ae:
        logging.error(f"❌ Eroare de atribut la conectarea cTrader: {ae}. Reconectare în 30s...")
        reactor.callLater(30, start_client)
    except Exception as e:
        logging.error(f"❌ Eroare neașteptată la inițializarea clientului cTrader: {e}. Reconectare în 30s...")
        reactor.callLater(30, start_client)

def on_connected(c):
    global is_connected
    logging.info("✅ Gateway conectat la TCP. Se autentifică...")
    try:
        app_auth = ProtoOAApplicationAuthReq()
        app_auth.clientId = CLIENT_ID
        app_auth.clientSecret = CLIENT_SECRET
        c.send(app_auth)

        acc_auth = ProtoOAAccountAuthReq()
        acc_auth.ctidTraderAccountId = ACCOUNT_ID
        c.send(acc_auth)
        is_connected = True
    except Exception as e:
        logging.error(f"❌ Eroare la autentificare: {e}")

def on_disconnected(c, reason):
    global is_connected
    is_connected = False
    logging.warning(f"⚠️ Gateway deconectat: {reason}. Așteptăm 30 secunde politicos înainte de reconectare...")
    reactor.callLater(30, start_client)

def on_message(c, message):
    pass # Ignorăm mesajele de rutină pentru a păstra codul simplu

def process_queue():
    global client_instance
    if not is_connected or client_instance is None:
        return # Dacă nu suntem conectați, nu încercăm să trimitem

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT order_id, signal_id, bot_name, symbol_id, trade_type, volume FROM order_queue WHERE status = 'PENDING' LIMIT 1")
        order = cursor.fetchone()

        if order:
            order_id, signal_id, bot_name, symbol_id, trade_type, volume = order
            logging.info(f"🚀 Gateway: Execut ordin pentru {bot_name} (ID: {order_id})")

            req = ProtoOANewOrderReq()
            req.ctidTraderAccountId = ACCOUNT_ID
            req.symbolId = symbol_id
            req.tradeType = trade_type
            req.volume = volume
            req.comment = f"NextGen_{bot_name}"
            
            if hasattr(client_instance, 'send'):
                client_instance.send(req)
            else:
                logging.error("❌ Client instance nu are metoda send()")

            cursor.execute("UPDATE order_queue SET status = 'SENT' WHERE order_id = ?", (order_id,))
            conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Eroare la procesarea cozii: {e}")

if __name__ == "__main__":
    logging.info("🏗️ GATEWAY SERVICE a pornit. Gestionează conexiunea politicoasă.")
    task.LoopingCall(process_queue).start(5.0) # Verifică coada la 5 secunde
    start_client()
    reactor.run()
