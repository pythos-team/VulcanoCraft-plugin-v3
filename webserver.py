from flask import Flask, json, jsonify, request, send_file, session, redirect, url_for
import os
import json as json_module
import urllib.parse
import subprocess
import sys
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def load_plugins():
    """Laad de plugins data uit het JSON bestand"""
    try:
        if os.path.exists('plugins.json'):
            with open('plugins.json', 'r', encoding='utf-8') as f:
                return json_module.load(f)
        return []
    except Exception as e:
        print(f"Fout bij het laden van plugins: {e}")
        return []

def save_plugins(plugins):
    """Sla plugins op in het JSON bestand"""
    try:
        with open('plugins.json', 'w', encoding='utf-8') as f:
            json_module.dump(plugins, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Fout bij het opslaan van plugins: {e}")
        return False

def get_user_plugins(username):
    """Haal plugins van specifieke gebruiker op"""
    plugins = load_plugins()
    return [p for p in plugins if p.get('owner') == username]

def add_user_plugin(username, plugin_data):
    """Voeg plugin toe voor specifieke gebruiker"""
    plugins = load_plugins()
    plugin_data['owner'] = username
    plugins = [p for p in plugins if not (p.get('url') == plugin_data['url'] and p.get('owner') == username)]
    plugins.append(plugin_data)
    return save_plugins(plugins)

def delete_user_plugin(username, url):
    """Verwijder plugin van specifieke gebruiker"""
    plugins = load_plugins()
    new_plugins = [p for p in plugins if not (p.get('url') == url and p.get('owner') == username)]
    return save_plugins(new_plugins) if len(new_plugins) != len(plugins) else False

def load_users():
    """Laad gebruikers uit users.json"""
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                return json_module.load(f)
        return []
    except Exception:
        return []

def save_users(users):
    """Sla gebruikers op in users.json"""
    try:
        with open('users.json', 'w', encoding='utf-8') as f:
            json_module.dump(users, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def hash_password(password):
    """Hash wachtwoord"""
    return hashlib.sha256(password.encode()).hexdigest()

def require_login(f):
    """Decorator voor login vereiste"""
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Login vereist'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def require_admin(f):
    """Decorator voor admin vereiste"""
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            return jsonify({'error': 'Admin rechten vereist'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def load_settings():
    """Laad instellingen"""
    try:
        if os.path.exists('settings.json'):
            with open('settings.json', 'r', encoding='utf-8') as f:
                return json_module.load(f)
        return {'registration_enabled': True}
    except Exception:
        return {'registration_enabled': True}

def save_settings(settings):
    """Sla instellingen op"""
    try:
        with open('settings.json', 'w', encoding='utf-8') as f:
            json_module.dump(settings, f, indent=4)
        return True
    except Exception:
        return False



@app.route('/')
def index():
    """Serveer de index.html pagina"""
    return send_file('index.html')

@app.route('/login-page')
def login_page():
    """Serveer de login.html pagina"""
    return send_file('components/user/login.html')

@app.route('/style.css')
def serve_css():
    """Serveer de CSS file"""
    return send_file('style.css', mimetype='text/css')

@app.route('/app.js')
def serve_js():
    """Serveer de JS file"""
    return send_file('app.js', mimetype='application/javascript')

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serveer afbeeldingen uit de images map"""
    try:
        return send_file(f'images/{filename}')
    except FileNotFoundError:
        return "Image not found", 404

@app.route('/api/plugins')
@require_login
def api_plugins():
    """API endpoint voor plugins data van ingelogde gebruiker"""
    username = session['user']
    plugins = get_user_plugins(username)
    return jsonify(plugins)

@app.route('/api/plugins/public')
def api_plugins_public():
    """API endpoint voor alle plugins data (publiek toegankelijk)"""
    plugins = load_plugins()
    return jsonify(plugins)

@app.route('/register', methods=['POST'])
def register():
    """Registreer nieuwe gebruiker"""
    try:
        settings = load_settings()
        if not settings.get('registration_enabled', True):
            return jsonify({'error': 'Registratie is uitgeschakeld'}), 403
            
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'error': 'Alle velden zijn vereist'}), 400
        
        users = load_users()
        
        # Check of gebruiker of email al bestaat
        if any(u['username'] == username for u in users):
            return jsonify({'error': 'Gebruikersnaam bestaat al'}), 400
        if any(u.get('email') == email for u in users):
            return jsonify({'error': 'Email bestaat al'}), 400
        
        # Voeg nieuwe gebruiker toe
        users.append({
            'username': username,
            'email': email,
            'password': hash_password(password)
        })
        
        if save_users(users):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Fout bij opslaan'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """Login gebruiker"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Gebruikersnaam/email en wachtwoord vereist'}), 400
        
        users = load_users()
        hashed_password = hash_password(password)
        
        # Check both username and email
        user = next((u for u in users if (u['username'] == username or u.get('email', '') == username) and u['password'] == hashed_password), None)
        
        if user:
            session['user'] = user['username']
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Ongeldige inloggegevens'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout gebruiker"""
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/auth-status')
def auth_status():
    """Check login status"""
    return jsonify({'logged_in': 'user' in session, 'username': session.get('user')})

@app.route('/registration-status')
def registration_status():
    """Check if registration is enabled"""
    settings = load_settings()
    return jsonify({'enabled': settings.get('registration_enabled', True)})



@app.route('/admin')
def admin_panel():
    """Admin panel pagina"""
    return send_file('components/admin/admin.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == 'admin' and hash_password(password) == hash_password('admin123'):
        session['admin'] = True
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    session.pop('admin', None)
    return jsonify({'success': True})

@app.route('/admin/check-session')
def admin_check_session():
    """Check admin session status"""
    return jsonify({'logged_in': session.get('admin', False)})

@app.route('/admin/users', methods=['GET'])
@require_admin
def admin_get_users():
    """Haal alle gebruikers op met plugin counts"""
    users = load_users()
    plugins = load_plugins()
    
    user_data = []
    for u in users:
        plugin_count = len([p for p in plugins if p.get('owner') == u['username']])
        user_data.append({
            'username': u['username'], 
            'email': u.get('email', ''),
            'plugin_count': plugin_count
        })
    
    return jsonify(user_data)

@app.route('/admin/users/<username>', methods=['DELETE'])
@require_admin
def admin_delete_user(username):
    """Verwijder gebruiker"""
    if username == 'admin':
        return jsonify({'error': 'Admin kan niet verwijderd worden'}), 400
        
    users = load_users()
    users = [u for u in users if u['username'] != username]
    
    if save_users(users):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij verwijderen'}), 500

@app.route('/admin/settings', methods=['GET'])
@require_admin
def admin_get_settings():
    """Haal instellingen op"""
    return jsonify(load_settings())

@app.route('/admin/settings', methods=['POST'])
@require_admin
def admin_update_settings():
    """Update instellingen"""
    data = request.get_json()
    if save_settings(data):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij opslaan'}), 500

@app.route('/fetch_plugin', methods=['POST'])
def fetch_plugin():
    """Haal plugin data op voor een gegeven URL"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'Geen URL opgegeven'}), 400
        
        # Voer launcher.py uit om plugin data op te halen
        result = subprocess.run(
            [sys.executable, 'launcher.py', url],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse de JSON output
        plugin_data = json_module.loads(result.stdout)
        return jsonify(plugin_data)
        
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Fout bij ophalen plugin data: {e.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@app.route('/add_plugin', methods=['POST'])
@require_login
def add_plugin():
    """Voeg een plugin toe aan de repository"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'Geen URL opgegeven'}), 400
        
        # Voer launcher.py uit om plugin data op te halen
        result = subprocess.run(
            [sys.executable, 'launcher.py', url],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse plugin data en voeg toe aan gebruiker
        plugin_data = json_module.loads(result.stdout)
        username = session['user']
        
        if add_user_plugin(username, plugin_data):
            return jsonify({'success': True, 'message': 'Plugin succesvol toegevoegd'})
        else:
            return jsonify({'error': 'Fout bij opslaan plugin'}), 500
        
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Fout bij toevoegen plugin: {e.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@app.route('/delete_plugin', methods=['POST'])
@require_login
def delete_plugin():
    """Verwijder een plugin uit de repository"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'Geen URL opgegeven'}), 400
        
        username = session['user']
        
        if delete_user_plugin(username, url):
            return jsonify({'success': True, 'message': 'Plugin succesvol verwijderd'})
        else:
            return jsonify({'error': 'Plugin niet gevonden of fout bij verwijderen'}), 404
        
    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)