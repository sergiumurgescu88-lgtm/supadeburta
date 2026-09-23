import os
from dotenv import load_dotenv
from ctrader_open_api import Client, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAApplicationAuthRes,
    ProtoOAAccountAuthReq, ProtoOAAccountAuthRes,
    ProtoOAGetSymbolReq, ProtoOAGetSymbolRes
)
from twisted.internet import reactor

load_dotenv('/root/ctrader-g4trade-bot/.env')

CLIENT_ID = os.getenv("CT_CLIENT_ID")
CLIENT_SECRET = os.getenv("CT_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("CT_ACCESS_TOKEN")
ACCOUNT_ID = 48710563

def on_message(msg):
    if isinstance(msg, ProtoOAApplicationAuthRes):
        print("✅ 1. Autentificare Aplicație: SUCCES")
        req = ProtoOAAccountAuthReq()
        req.ctidTraderAccountId = ACCOUNT_ID
        req.accessToken = ACCESS_TOKEN
        client.send(req)
        
    elif isinstance(msg, ProtoOAAccountAuthRes):
        print("✅ 2. Autentificare Cont: SUCCES")
        print("🔍 3. Se solicită detaliile pentru Simbolul 41 (XAUUSD)...")
        req = ProtoOAGetSymbolReq()
        req.ctidTraderAccountId = ACCOUNT_ID
        req.symbolId.append(41)
        client.send(req)
        
    elif isinstance(msg, ProtoOAGetSymbolRes):
        print("\n" + "="*60)
        print("📊 DATELE REALE DE LA BROKER PENTRU SIMBOLUL 41:")
        print("="*60)
        for symbol in msg.symbol:
            print(f"Nume Simbol: {symbol.symbolName}")
            print(f"ID Simbol: {symbol.symbolId}")
            print(f"Tip: {symbol.type}")
            print(f"Digite: {symbol.digits}")
            # Afișăm toate atributele disponibile pentru a căuta volumul
            print(f"Specificații complete: {symbol}")
        print("="*60 + "\n")
        reactor.stop()
        
    else:
        print(f"ℹ️ Mesaj primit de la server: {type(msg).__name__}")

print("🔌 Se inițiază conexiunea la cTrader Demo...")
client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
client.on_message = on_message

req = ProtoOAApplicationAuthReq()
req.clientId = CLIENT_ID
req.clientSecret = CLIENT_SECRET
client.send(req)

reactor.run()
