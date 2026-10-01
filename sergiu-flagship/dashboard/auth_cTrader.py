from flask import Blueprint, redirect, request, session, jsonify
import requests
import os

auth_bp = Blueprint('auth', __name__)

CLIENT_ID = os.getenv('CT_CLIENT_ID', '40034_3cfKWjo53RDFvbI72kW98rMGvV9TpmRQq5zgy1qCZqOt5oE9H3')
CLIENT_SECRET = os.getenv('CT_CLIENT_SECRET', '9IWqPBwVK2Ep3g2nkEe2nXVmNQlaT4L3EJTFfrTCJKwHQP')
REDIRECT_URI = 'https://g4trade.online/auth/callback'

@auth_bp.route('/login')
def login():
    """Redirecționează utilizatorul la pagina de login cTrader"""
    auth_url = (
        f'https://id.ctrader.com/my/settings/openapi/grantingaccess/'
        f'?client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}'
        f'&scope=trading'
        f'&product=web'
    )
    return redirect(auth_url)

@auth_bp.route('/callback')
def callback():
    """Primește authorization code și îl schimbă cu access token"""
    code = request.args.get('code')
    
    if not code:
        return 'Eroare: Nu am primit codul de autorizare', 400
    
    # Schimbă codul cu access token
    token_url = 'https://openapi.ctrader.com/apps/token'
    params = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.get(token_url, params=params)
    data = response.json()
    
    if 'accessToken' in data:
        # Salvează token-urile în fișierul .env
        with open('/root/ctrader-g4trade-bot/.env', 'w') as f:
            f.write(f'CT_CLIENT_ID={CLIENT_ID}\n')
            f.write(f'CT_CLIENT_SECRET={CLIENT_SECRET}\n')
            f.write(f'CT_ACCESS_TOKEN={data["accessToken"]}\n')
            f.write(f'CT_REFRESH_TOKEN={data["refreshToken"]}\n')
        
        return '✅ Autentificare reușită! Token-urile au fost salvate. Repornește botul cu: pm2 restart gold-bot'
    else:
        return f'Eroare la obținerea token-ului: {data}', 500

