import requests
import os
from dotenv import load_dotenv, set_key

load_dotenv()
client_id = "40034_3cfKWjo53RDFvbI72kW98rMGvV9TpmRQq5zgy1qCZqOt5oE9H3"
client_secret = "9IWqPBwVK2Ep3g2nkEe2nXVmNQlaT4L3EJTFfrTCJKwHQPPMnl"
redirect_uri = "https://openapi.ctrader.com/apps/40034/playground"

code = input("Lipeste codul de pe ecran aici si apasa Enter: ").strip()

print("\nSe proceseaza...")
res = requests.post("https://openapi.ctrader.com/api/auth/token", data={
    "grant_type": "authorization_code",
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri
})

if res.status_code == 200:
    token = res.json().get("access_token")
    set_key(".env", "CT_ACCESS_TOKEN", token)
    print("🎉 SUCCES FINAL! Token-ul a fost salvat in fisierul .env")
else:
    print(f"❌ Eroare: {res.text}")
