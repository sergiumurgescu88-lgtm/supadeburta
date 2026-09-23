import http.server
import socketserver
import urllib.parse
import requests
import os
from dotenv import load_dotenv, set_key

load_dotenv()
client_id = os.getenv("CT_CLIENT_ID")
client_secret = os.getenv("CT_CLIENT_SECRET")
redirect_uri = "http://187.77.64.99:3000/callback"

class AuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback?code='):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get('code', [None])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            # Folosim encode('utf-8') pentru a permite caractere normale
            html_response = "<h1 style='font-family: sans-serif; color: green;'>SUCCES! Poti inchide aceasta fereastra.</h1><p>VPS-ul a procesat token-ul automat.</p>"
            self.wfile.write(html_response.encode('utf-8'))
            
            print("\n[+] Cod primit de la browser! Se obtine token-ul de la cTrader...")
            token_url = "https://openapi.ctrader.com/api/auth/token"
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            }
            response = requests.post(token_url, data=data)
            if response.status_code == 200:
                token = response.json().get("access_token")
                set_key(".env", "CT_ACCESS_TOKEN", token)
                print("SUCCES FINAL! Token-ul a fost salvat in fisierul .env")
            else:
                print(f"Eroare la obtinerea token-ului: {response.text}")
            
            os._exit(0)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

PORT = 3000
print("="*70)
print("SERVERUL VPS ASCULTA ACUM PE PORTUL 3000")
print("="*70)
print("1. COPIAZA SI DESCHIDE ACEST LINK IN BROWSERUL TAU:")
print(f"https://openapi.ctrader.com/api/auth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=trading")
print("2. Logheaza-te cu contul tau si apasa 'Authorize'.")
print("3. NU MAI FACE NIMIC. VPS-ul va face restul automat...\n")

with socketserver.TCPServer(("0.0.0.0", PORT), AuthHandler) as httpd:
    httpd.serve_forever()
