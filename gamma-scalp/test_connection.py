from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOAApplicationAuthReq
from twisted.internet import reactor
import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("CT_CLIENT_ID")
client_secret = os.getenv("CT_CLIENT_SECRET")

host = EndPoints.PROTOBUF_DEMO_HOST
client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)

def onError(failure):
    print("❌ Eroare fatală:", failure)
    reactor.stop()

def connected(client):
    print("✅ Conectat fizic la serverul cTrader DEMO!")
    req = ProtoOAApplicationAuthReq()
    req.clientId = client_id
    req.clientSecret = client_secret
    print(f"📤 Trimitere cerere de autentificare pentru Client ID: {client_id[:15]}...")
    client.send(req)

def onMessageReceived(client, message):
    msg_name = message.__class__.__name__
    print(f"📩 Mesaj primit de la server: {msg_name}")
    
    if msg_name == "ProtoOAApplicationAuthRes":
        print("🎉 SUCCES! Aplicatia este autorizata oficial de Spotware!")
        reactor.stop()
    elif msg_name == "ProtoOAApplicationAuthErrorRes":
        print("⚠️ Eroare de autorizare! Serverul a respins cererea.")
        print("Detalii eroare:", Protobuf.extract(message))
        reactor.stop()
    else:
        print("Detalii mesaj:", Protobuf.extract(message))

def disconnected(client, reason):
    print(f"🔴 Deconectat. Motiv: {reason}")
    reactor.stop() # Oprim scriptul la deconectare pentru a evita bucla infinită

client.setConnectedCallback(connected)
client.setMessageReceivedCallback(onMessageReceived)
client.setDisconnectedCallback(disconnected)

print("🔄 Se încearcă conectarea...")
client.startService()
reactor.run()
