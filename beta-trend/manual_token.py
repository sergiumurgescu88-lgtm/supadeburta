import requests
import os
from dotenv import load_dotenv, set_key

load_dotenv()
client_id = os.getenv("CT_CLIENT_ID")
client_secret = os.getenv("CT_CLIENT_SECRET")
redirect_uri = "http://187.77.64.99:9090/callback"

print("="*70)
print("1. COPIAZA SI DESCHIDE ACEST LINK IN BROWSER:")
print(f"https://openapi.ctrader.com/api/auth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=trading")
print("2. Logheaza-te cu contul tau si apasa butonul 'Authorize'.")
print("3. Vei ajunge pe o pagina de eroare sau alba ('Site can't be reached' sau '404'). ESTE NORMAL!")
print("4. Uita-te in BARA DE ADRESA DE SUS a browserului.")
print("5. Linkul va arata asa: http://187.77.64.99:9090/callback?code=CODUL_TAU_LUNG_AICI&state=ceva")
print("6. Copiaza DOAR 'CODUL_TAU_LUNG_AICI' (tot ce este dupa 'code=' si inainte de '&').")
print("="*70)

code = input("Lipeste codul lung aici si apasa Enter: ").strip()

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
