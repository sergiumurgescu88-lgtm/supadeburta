import http.server
import socketserver
import urllib.parse
import requests
import os
from dotenv import load_dotenv, set_key

load_dotenv()
client_id = os.getenv("CT_CLIENT_ID")
client_secret = os.getenv("CT_CLIENT_SECRET")
redirect_uri = "http://187.77.64.99:9090/callback"

class AuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback?code='):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get('code', [None])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = "<h1 style='color:green; font-family:sans-serif;'>SUCCES! Token salvat.</h1><p>Te poti intoarce in terminal.</p>"
            self.wfile.write(html.encode('utf-8'))
            
            print("\n[+] Cod primit! Obtinem token-ul de la cTrader...")
            res = requests.post("https://openapi.ctrader.com/api/auth/token", data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            })
            if res.status_code == 200:
                set_key(".env", "CT_ACCESS_TOKEN", res.json().get("access_token"))
                print("🎉 SUCCES FINAL! Token-ul a fost salvat in fisierul .env")
            else:
                print(f"❌ Eroare: {res.text}")
            os._exit(0)
        else:
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, format, *args):
        pass

print("="*70)
print("1. COPIAZA SI DESCHIDE ACEST LINK IN BROWSER:")
print(f"https://openapi.ctrader.com/api/auth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=trading")
print("2. Logheaza-te si apasa 'Authorize'.")
print("3. VPS-ul va prelua codul automat.")
print("="*70)

socketserver.TCPServer(("0.0.0.0", 9090), AuthHandler).serve_forever()
