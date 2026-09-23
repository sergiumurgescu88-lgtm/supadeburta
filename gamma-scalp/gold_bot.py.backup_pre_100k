import os
import json
import logging
import time
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq,
    ProtoOAAccountAuthReq,
    ProtoOANewOrderReq,
    ProtoOASymbolsListReq,
    ProtoOAAmendPositionSLTPReq,
    ProtoOAClosePositionReq,
    ProtoOAReconcileReq
)
from twisted.internet import reactor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("/var/log/g4trade-bot.log"), logging.StreamHandler()]
)

env = {}
with open("/root/ctrader-g4trade-bot/.env", "r") as f:
    for line in f:
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

CLIENT_ID = env.get("CT_CLIENT_ID", "")
CLIENT_SECRET = env.get("CT_CLIENT_SECRET", "")
ACCESS_TOKEN = env.get("CT_ACCESS_TOKEN", "")
ACCOUNT_ID = int(env.get("CT_ACCOUNT_ID", "48710563"))

MAX_VOLUME = 1.00  # Sniper safe
SYMBOL_NAME = "XAUUSD"
TRADE_FILE = "/root/ctrader-g4trade-bot/dashboard/static/trade_request.json"
PROCESSED_FILE = TRADE_FILE + ".processed"

ORDER_TYPE_MARKET = 1
TRADE_SIDE_BUY = 1
TRADE_SIDE_SELL = 2
TIME_IN_FORCE_IOC = 3

client_instance = None
is_online = False
xauusd_symbol_id = None
symbols_loaded = False
pending_volume_units = {}

def send(msg):
    if client_instance:
        client_instance.send(msg).addErrback(lambda f: logging.error(f"Send error: {f}"))

def validate_trade(data):
    if not isinstance(data, dict) or not data:
        return False, "Empty or invalid JSON"
    if data.get('action') != 'create':
        return False, "Invalid action"
    if not data.get('approved'):
        return False, "Trade not approved"
    if data.get('symbol') != SYMBOL_NAME:
        return False, f"Wrong symbol: {data.get('symbol')}"
    
    side = str(data.get('side', '')).upper()
    if side not in ['BUY', 'SELL']:
        return False, f"Invalid side: {side}"
    
    try:
        volume = float(data.get('volume', 0))
        if volume <= 0:
            return False, "Volume must be > 0"
        if volume > MAX_VOLUME:
            logging.warning(f"⚠️ Volume {volume} exceeds max {MAX_VOLUME}, capping!")
            data['volume'] = MAX_VOLUME
    except (ValueError, TypeError):
        return False, "Invalid volume"
    
    sl = float(data.get('stopLoss', 0) or data.get('sl', 0) or 0)
    if sl <= 0:
        return False, "🛡️ REJECTED: Stop Loss must be > 0"
    data['_sl'] = sl
    
    tp = float(data.get('takeProfit', 0) or data.get('tp', 0) or 0)
    if tp <= 0:
        return False, "🛡️ REJECTED: Take Profit must be > 0"
    data['_tp'] = tp
    
    return True, ""

def load_symbols():
    logging.info("📋 Loading symbols list...")
    r = ProtoOASymbolsListReq()
    r.ctidTraderAccountId = ACCOUNT_ID
    send(r)

def send_market_order(trade_data):
    global xauusd_symbol_id
    
    side_str = trade_data['side'].upper()
    volume_lots = float(trade_data['volume'])
    volume_units = int(volume_lots * 10000)
    
    logging.info(f"🚀 SENDING {side_str} {volume_lots} lots {SYMBOL_NAME} @ MARKET")
    logging.info(f"   Volume units: {volume_units} | SL: {trade_data['_sl']} | TP: {trade_data['_tp']}")
    
    pending_volume_units[volume_units] = {
        'sl': trade_data['_sl'],
        'tp': trade_data['_tp'],
        'trade_data': trade_data
    }
    
    r = ProtoOANewOrderReq()
    r.ctidTraderAccountId = ACCOUNT_ID
    r.symbolId = xauusd_symbol_id
    r.tradeSide = TRADE_SIDE_BUY if side_str == 'BUY' else TRADE_SIDE_SELL
    r.orderType = ORDER_TYPE_MARKET
    r.timeInForce = TIME_IN_FORCE_IOC
    r.volume = volume_units
    r.clientOrderId = f"G4T_{int(time.time())}"
    
    if trade_data.get('comment'):
        r.label = str(trade_data['comment'])[:50]
    
    send(r)

def apply_sl_tp(position_id, sl, tp):
    logging.info(f"🎯 Applying SL={sl} TP={tp} to position {position_id}")
    r = ProtoOAAmendPositionSLTPReq()
    r.ctidTraderAccountId = ACCOUNT_ID
    r.positionId = position_id
    r.stopLoss = sl
    r.takeProfit = tp
    send(r)

def mark_processed():
    try:
        if os.path.exists(TRADE_FILE):
            os.rename(TRADE_FILE, PROCESSED_FILE)
            logging.info("📝 Trade file marked as processed")
    except Exception as e:
        logging.error(f"Error marking file: {e}")

def on_connected(c):
    global client_instance
    client_instance = c
    logging.info("TCP connected. Authenticating...")
    r = ProtoOAApplicationAuthReq()
    r.clientId = CLIENT_ID
    r.clientSecret = CLIENT_SECRET
    send(r)

def on_disconnected(c, reason):
    global is_online, symbols_loaded
    logging.warning(f"Disconnected: {reason}")
    is_online = False
    symbols_loaded = False
    reactor.callLater(5, client_instance.startService)

def on_message(c, message):
    global is_online, xauusd_symbol_id, symbols_loaded, pending_volume_units
    try:
        m = Protobuf.extract(message)
        name = type(m).__name__
        
        if name == "ProtoHeartbeatEvent":
            return
            
        elif name == "ProtoOAApplicationAuthRes":
            if hasattr(m, 'error') and m.error:
                logging.error(f"App auth failed: {m}")
            else:
                logging.info("✅ App authenticated")
                r = ProtoOAAccountAuthReq()
                r.ctidTraderAccountId = ACCOUNT_ID
                r.accessToken = ACCESS_TOKEN
                send(r)
                
        elif name == "ProtoOAAccountAuthRes":
            if hasattr(m, 'error') and m.error:
                logging.error(f"Account auth failed: {m}")
            else:
                logging.info("✅ ACCOUNT AUTHENTICATED.")
                is_online = True
                load_symbols()
                
        elif name == "ProtoOASymbolsListRes":
            xauusd_found = False
            if hasattr(m, 'symbol'):
                for sym in m.symbol:
                    name_attr = getattr(sym, 'symbolName', '')
                    if SYMBOL_NAME.upper() in name_attr.upper() and 'EXP' not in name_attr.upper():
                        xauusd_symbol_id = sym.symbolId
                        xauusd_found = True
                        logging.info(f"✅ Found {name_attr}: symbolId = {xauusd_symbol_id}")
                        break
            
            if xauusd_found:
                symbols_loaded = True
                logging.info("🚀 Bot fully ONLINE and ready for trades!")
                reactor.callLater(0, watch_trades)
            else:
                logging.error(f"❌ Could not find {SYMBOL_NAME}!")
                
        elif name == "ProtoOANewOrderRes":
            if hasattr(m, 'error') and m.error:
                logging.error(f"❌ ORDER FAILED: {m}")
            else:
                order_id = getattr(m, 'orderId', 'N/A')
                logging.info(f"✅ Market order ACCEPTED! Order ID: {order_id}")
                
        elif name == "ProtoOAExecutionEvent":
            exec_type = getattr(m, 'executionType', None)
            logging.info(f"📨 EXECUTION EVENT: {exec_type}")
            
            if hasattr(m, 'position') and m.position:
                pos = m.position
                pos_id = getattr(pos, 'positionId', None)
                volume = getattr(getattr(pos, 'tradeData', None), 'volume', 0) if hasattr(pos, 'tradeData') else 0
                
                logging.info(f"   Position ID: {pos_id}, Volume: {volume}")
                
                if pos_id and volume > 0 and volume in pending_volume_units:
                    trade_info = pending_volume_units[volume]
                    logging.info(f"🎯 POSITION OPENED! Applying SL/TP...")
                    apply_sl_tp(pos_id, trade_info['sl'], trade_info['tp'])
                    del pending_volume_units[volume]
            
            if hasattr(m, 'errorCode') and m.errorCode:
                logging.error(f"❌ Execution error: {m.errorCode} - {getattr(m, 'description', '')}")
                
        elif name == "ProtoOAAmendPositionSLTPRes":
            if hasattr(m, 'error') and m.error:
                logging.error(f"❌ SL/TP amend failed: {m}")
            else:
                logging.info(f"✅ SL/TP APPLIED SUCCESSFULLY! Position protected.")
            
        elif name == "ProtoOAOrderErrorEvent":
            logging.error(f"❌ ORDER ERROR: {getattr(m, 'errorCode', 'UNKNOWN')} - {getattr(m, 'description', '')}")
            
        elif name == "ProtoOAErrorRes":
            logging.error(f"cTrader error: {m}")
            
    except Exception as e:
        logging.error(f"Message processing error: {e}", exc_info=True)

def watch_trades():
    global is_online, symbols_loaded, xauusd_symbol_id
    
    if not is_online or not symbols_loaded or xauusd_symbol_id is None:
        reactor.callLater(2, watch_trades)
        return
    
    try:
        if os.path.exists(TRADE_FILE):
            with open(TRADE_FILE, 'r') as f:
                data = json.load(f)
            
            is_valid, error = validate_trade(data)
            if is_valid:
                logging.info(f"🎯 VALID TRADE: {data}")
                mark_processed()
                send_market_order(data)
            elif data:
                logging.warning(f"Invalid trade: {error}")
                mark_processed()
    except json.JSONDecodeError as e:
        logging.error(f"JSON parse error: {e}")
        mark_processed()
    except FileNotFoundError:
        pass
    except Exception as e:
        logging.error(f"Watch error: {e}")
        mark_processed()
    
    reactor.callLater(2, watch_trades)

if __name__ == "__main__":
    logging.info("=" * 60)
    logging.info("=== G4Trade Gold Bot v3.6 - FINAL PRODUCTION ===")
    logging.info(f"Account: {ACCOUNT_ID} | Max Volume: {MAX_VOLUME} lots")
    logging.info(f"Symbol: {SYMBOL_NAME}")
    logging.info("=" * 60)
    
    client_instance = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
    client_instance.setConnectedCallback(on_connected)
    client_instance.setDisconnectedCallback(on_disconnected)
    client_instance.setMessageReceivedCallback(on_message)
    client_instance.startService()
    reactor.run()
