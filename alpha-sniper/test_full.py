import traceback
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAGetAccountListByAccessTokenReq, ProtoOAAccountAuthReq)
from twisted.internet import reactor

env = {}
for line in open("/root/ctrader-g4trade-bot/.env"):
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
cid, sec, tok = env["CT_CLIENT_ID"], env["CT_CLIENT_SECRET"], env["CT_ACCESS_TOKEN"]
WANTED = int(env.get("CT_ACCOUNT_ID", "0"))
print("lungimi: secret", len(sec), "| token", len(tok))

client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)

def send(msg):
    client.send(msg).addErrback(lambda f: print("Eroare send:", f))

def finish():
    reactor.callLater(1, lambda: reactor.running and reactor.stop())

def on_connected(c):
    print("1) Conectat. Autentific aplicatia...")
    r = ProtoOAApplicationAuthReq(); r.clientId = cid; r.clientSecret = sec
    send(r)

def on_message(c, message):
    try:
        m = Protobuf.extract(message)
        name = type(m).__name__
        if name == "ProtoHeartbeatEvent":
            return
        if name == "ProtoOAApplicationAuthRes":
            print("   OK: aplicatia e autentificata.")
            print("2) Cer conturile asociate token-ului...")
            r = ProtoOAGetAccountListByAccessTokenReq(); r.accessToken = tok
            send(r)
        elif name == "ProtoOAGetAccountListByAccessTokenRes":
            accts = list(m.ctidTraderAccount)
            print("   Conturi gasite:", len(accts))
            for a in accts:
                print("   - ctidTraderAccountId =", a.ctidTraderAccountId,
                      "| login =", getattr(a, "traderLogin", "?"), "| live =", a.isLive)
            if not accts:
                finish(); return
            pick = next((a for a in accts if WANTED in (a.ctidTraderAccountId, getattr(a, "traderLogin", None))), accts[0])
            print("3) Autentific contul ctid =", pick.ctidTraderAccountId)
            r = ProtoOAAccountAuthReq(); r.ctidTraderAccountId = pick.ctidTraderAccountId; r.accessToken = tok
            send(r)
        elif name == "ProtoOAAccountAuthRes":
            print("   OK: CONT AUTENTIFICAT. Lantul complet functioneaza."); finish()
        else:
            print("   Mesaj:", name, "\n", m)
            if name == "ProtoOAErrorRes":
                finish()
    except Exception:
        traceback.print_exc(); finish()

def on_disconnected(c, reason):
    print("Deconectat:", reason.getErrorMessage())
    if reactor.running:
        reactor.stop()

client.setConnectedCallback(on_connected)
client.setMessageReceivedCallback(on_message)
client.setDisconnectedCallback(on_disconnected)
reactor.callLater(25, lambda: (print("Timeout 25s"), reactor.running and reactor.stop()))
client.startService()
reactor.run()
