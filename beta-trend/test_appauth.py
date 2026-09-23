from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOAApplicationAuthReq
from twisted.internet import reactor

def load_env(path):
    env = {}
    with open(path, newline="") as f:
        for line in f:
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.rstrip("\n")
    return env

env = load_env("/root/ctrader-g4trade-bot/.env")
raw_id = env.get("CT_CLIENT_ID", "")
raw_sec = env.get("CT_CLIENT_SECRET", "")

def diag(name, v):
    print(f"{name}: len={len(v)} | spatii/CR la capete={v != v.strip()} | ghilimele={v[:1] in '\"\'' or v[-1:] in '\"\''}")

diag("CLIENT_ID    ", raw_id)
diag("CLIENT_SECRET", raw_sec)

cid = raw_id.strip().strip('"').strip("'")
sec = raw_sec.strip().strip('"').strip("'")

client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)

def on_connected(c):
    print(">> Conectat (TCP+TLS OK). Trimit ApplicationAuthReq...")
    req = ProtoOAApplicationAuthReq()
    req.clientId = cid
    req.clientSecret = sec
    c.send(req).addErrback(lambda f: print(">> Eroare send:", f))

def on_message(c, message):
    print(">> RASPUNS SERVER:\n", Protobuf.extract(message))
    reactor.callLater(1, reactor.stop)

def on_disconnected(c, reason):
    print(">> DECONECTAT:", reason)
    if reactor.running:
        reactor.stop()

client.setConnectedCallback(on_connected)
client.setMessageReceivedCallback(on_message)
client.setDisconnectedCallback(on_disconnected)
reactor.callLater(20, lambda: (print(">> Timeout 20s"), reactor.stop()))
client.startService()
reactor.run()
