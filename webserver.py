# soketdb_flask_app.py
from flask import Flask, json, jsonify, request, send_file, session
import os
import json as json_module
import urllib.parse
import subprocess
import sys
import hashlib
import secrets
from soketdb import database

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# initialize SocketDB (project name as your DB folder)
db = database("plugin-craft-db")


# -------------------------
# Helpers
# -------------------------
def _esc(val):
    """
    Escape and quote values for SocketDB SQL.
    - dict/list -> JSON string (no quoting around outer DATA usage)
    - str -> single-quoted with single-quotes doubled
    - numbers/bools -> str()
    - None -> ''
    """
    if val is None:
        return "''"
    if isinstance(val, (dict, list)):
        return json_module.dumps(val, ensure_ascii=False)
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val).replace("'", "''")
    return f"'{s}'"


def _row_from_single_list(result):
    """Normalize SELECT response to list of dicts; return [] on error/messages"""
    if isinstance(result, list):
        return result
    return []


# -------------------------
# Plugins (replacing JSON file ops with SocketDB)
# -------------------------
def load_plugins():
    """Laad de plugins data uit de database (alle plugins)."""
    try:
        res = db.execute("SELECT * FROM plugins")
        return _row_from_single_list(res)
    except Exception as e:
        app.logger.exception("Fout bij het laden van plugins")
        return []


def save_plugins(plugins):
    """
    Replace all plugins in the table:
    - DELETE all rows, then re-insert from provided list.
    """
    try:
        for p in plugins:
            payload = json_module.dumps(p, ensure_ascii=False)
            db.execute(f"INSERT INTO plugins DATA={payload}")
        return True
    except Exception as e:
        app.logger.exception("Fout bij het opslaan van plugins")
        return False


def get_user_plugins(username):
    """Haal plugins van specifieke gebruiker op"""
    try:
        username_q = _esc(username)
        res = db.execute(f"SELECT * FROM plugins WHERE owner = {username_q}")
        return _row_from_single_list(res)
    except Exception as e:
        app.logger.exception("Fout bij get_user_plugins")
        return []


def add_user_plugin(username, plugin_data):
    """Voeg plugin toe voor specifieke gebruiker"""
    try:
        plugin_data = dict(plugin_data)
        plugin_data['owner'] = username
        url = plugin_data.get('url')
        if not url:
            return False

        # remove existing same owner+url then insert new
        db.execute(f"DELETE FROM plugins WHERE owner = {_esc(username)} AND url = {_esc(url)}")
        db.execute(f"INSERT INTO plugins DATA={json_module.dumps(plugin_data, ensure_ascii=False)}")
        return True
    except Exception as e:
        app.logger.exception("Fout bij add_user_plugin")
        return False


def delete_user_plugin(username, url):
    """Verwijder plugin van specifieke gebruiker"""
    try:
        res = db.execute(f"DELETE FROM plugins WHERE owner = {_esc(username)} AND url = {_esc(url)}")
        return True
    except Exception as e:
        app.logger.exception("Fout bij delete_user_plugin")
        return False


def delete_any_plugin(url):
    """Verwijder plugin (admin functie)"""
    try:
        res = db.execute(f"DELETE FROM plugins WHERE url = {_esc(url)}")
        return True
    except Exception as e:
        app.logger.exception("Fout bij delete_any_plugin")
        return False


# -------------------------
# Users (replacing users.json)
# -------------------------
def load_users():
    """Laad gebruikers uit users table"""
    try:
        res = db.execute("SELECT * FROM users")
        return _row_from_single_list(res)
    except Exception as e:
        app.logger.exception("Fout bij load_users")
        return []


def save_users(users):
    """Sla gebruikers op: replace all users"""
    try:
        db.execute("DELETE FROM users")
        for u in users:
            payload = json_module.dumps(u, ensure_ascii=False)
            db.execute(f"INSERT INTO users DATA={payload}")
        return True
    except Exception as e:
        app.logger.exception("Fout bij save_users")
        return False


def hash_password(password):
    """Hash wachtwoord (users only)"""
    return hashlib.sha256(password.encode()).hexdigest()


# -------------------------
# Settings (replacing settings.json)
# -------------------------
def load_settings():
    """Laad instellingen uit settings table (returns dict)"""
    try:
        res = db.execute("SELECT * FROM settings")
        rows = _row_from_single_list(res)
        if rows:
            # prefer whole settings row (first row)
            row = rows[0]
            # preserve existing key names (registration_enabled or register_status)
            return row
        # default minimal settings
        return {"registration_enabled": True}
    except Exception as e:
        app.logger.exception("Fout bij load_settings")
        return {"registration_enabled": True}


def save_settings(settings):
    """Sla instellingen op (upsert-like: clear then insert)"""
    try:
        # ensure dict
        if not isinstance(settings, dict):
            return False
        db.execute("DELETE FROM settings")
        db.execute(f"INSERT INTO settings DATA={json_module.dumps(settings, ensure_ascii=False)}")
        return True
    except Exception as e:
        app.logger.exception("Fout bij save_settings")
        return False


# -------------------------
# Auth decorators / helpers
# -------------------------
def require_login(f):
    def wrapper(*args, **kwargs):
        if 'user' not in session and 'admin' not in session:
            return jsonify({'error': 'Login vereist'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def require_admin(f):
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin rechten vereist'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def require_co_admin(f):
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') not in ['admin', 'co-admin']:
            return jsonify({'error': 'Co-Admin rechten vereist'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def get_current_user():
    """Haal huidige gebruiker op (reads users table)"""
    username = session.get('user') or session.get('admin')
    if not username:
        return None
    users = load_users()
    return next((u for u in users if u.get('username') == username), None)


def get_register_status():
    """Return True if registration is allowed (checks settings table)"""
    try:
        s = load_settings()
        # handle either key name
        if isinstance(s, dict):
            if "registration_enabled" in s:
                return bool(s.get("registration_enabled"))
            if "register_status" in s:
                # backward compatibility
                val = s.get("register_status")
                if isinstance(val, bool):
                    return val
                if isinstance(val, str):
                    return val.lower() in ("true", "1")
        return True
    except Exception:
        return True


# -------------------------
# Routes (static pages)
# -------------------------
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
    """Serveer afbeeldingen uit de images map (keeps your old behavior)."""
    try:
        return send_file(f'images/{filename}')
    except FileNotFoundError:
        return "Image not found", 404


# -------------------------
# API: plugins
# -------------------------
@app.route('/api/plugins')
@require_login
def api_plugins():
    """API endpoint voor plugins data van ingelogde gebruiker"""
    # if admin -> return all
    if 'admin' in session:
        plugins = load_plugins()
    else:
        username = session.get('user')
        plugins = get_user_plugins(username)
    return jsonify(plugins)


@app.route('/api/plugins/public')
def api_plugins_public():
    """API endpoint voor alle plugins data (publiek toegankelijk)"""
    # Return all plugins marked public, or all plugins if your schema doesn't have privacy flag
    try:
        # If plugins have a 'public' boolean/property, filter on it; otherwise return all
        res = db.execute("SELECT * FROM plugins WHERE public = 1")
        rows = _row_from_single_list(res)
        if rows:
            return jsonify(rows)
        # fallback - return all
        return jsonify(load_plugins())
    except Exception:
        return jsonify(load_plugins())


# -------------------------
# Registration / Login / Auth
# -------------------------
@app.route('/register', methods=['POST'])
def register():
    """Registreer nieuwe gebruiker"""
    try:
        if not get_register_status():
            return jsonify({'error': 'Registratie is uitgeschakeld'}), 403

        data = request.get_json() or {}
        username = (data.get('username') or "").strip()
        password = data.get('password') or ""

        if not username or not password:
            return jsonify({'error': 'Gebruikersnaam en wachtwoord zijn vereist'}), 400

        # check existing in users table
        existing = db.execute(f"SELECT * FROM users WHERE username = {_esc(username)}")
        if isinstance(existing, list) and existing:
            return jsonify({'error': 'Gebruikersnaam bestaat al'}), 400

        user_row = {"username": username, "password": hash_password(password)}
        db.execute(f"INSERT INTO users DATA={json_module.dumps(user_row, ensure_ascii=False)}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.exception("Fout bij register")
        return jsonify({'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    """Login gebruiker or admin (single route)"""
    try:
        data = request.get_json() or {}
        username = (data.get('username') or "").strip()
        password = data.get('password') or ""

        if not username or not password:
            return jsonify({'error': 'Gebruikersnaam en wachtwoord vereist'}), 400

        # First check admins table (admins have plain passwords)
        admin_res = db.execute(f"SELECT * FROM admins WHERE username = {_esc(username)} AND password = {_esc(password)}")
        if isinstance(admin_res, list) and admin_res:
            session['admin'] = username
            return jsonify({'success': True, 'role': 'admin', 'username': username})

        # Then check users table (password hashed)
        hashed_pw = hash_password(password)
        user_res = db.execute(f"SELECT * FROM users WHERE username = {_esc(username)} AND password = {_esc(hashed_pw)}")
        if isinstance(user_res, list) and user_res:
            # session for normal user
            session['user'] = username
            return jsonify({'success': True, 'role': 'user', 'username': username})

        return jsonify({'error': 'Ongeldige inloggegevens'}), 401
    except Exception as e:
        app.logger.exception("Fout bij login")
        return jsonify({'error': str(e)}), 500


@app.route('/logout', methods=['POST'])
def logout():
    """Logout gebruiker"""
    session.pop('user', None)
    session.pop('admin', None)
    return jsonify({'success': True})


@app.route('/auth-status')
def auth_status():
    """Check login status"""
    user = get_current_user()
    return jsonify({
        'logged_in': ('user' in session) or ('admin' in session), 
        'username': session.get('user') or session.get('admin'),
        'role': user.get('role', 'user') if user else ('admin' if 'admin' in session else None)
    })


@app.route('/registration-status')
def registration_status():
    """Check if registration is enabled"""
    try:
        settings = load_settings()
        # check either key form
        enabled = settings.get('registration_enabled', settings.get('register_status', True))
        return jsonify({'enabled': bool(enabled)})
    except Exception:
        return jsonify({'enabled': True})


# -------------------------
# Admin routes / user management
# -------------------------
@app.route('/admin')
def admin_panel():
    """Admin panel pagina"""
    users = db.execute("SELECT * FROM users")
    plugins = db.execute("SELECT * FROM plugins")
    totalUsers = len(users) if users else 0
    totalPlugins = len(plugins) if plugins else 0
    return render_template('admin/admin.html', totalUsers=totalUsers, totalPlugins=totalPlugins)


@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login (legacy: allow login via users table role too)"""
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    # First, check admins table (plain password)
    admin = db.execute(f"SELECT * FROM admins WHERE username = {_esc(username)} AND password = {_esc(password)}")
    if isinstance(admin, list) and admin:
        session['admin'] = username
        return jsonify({'success': True, 'role': 'admin'})


@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    session.pop('user', None)
    session.pop('admin', None)
    return jsonify({'success': True})


@app.route('/admin/check-session')
def admin_check_session():
    """Check admin session status"""
    user = get_current_user()
    if user and user.get('role') in ['admin', 'co-admin']:
        return jsonify({'logged_in': True, 'role': user.get('role'), 'username': user.get('username')})
    # also allow admin session
    if 'admin' in session:
        return jsonify({'logged_in': True, 'role': 'admin', 'username': session.get('admin')})
    return jsonify({'logged_in': False})


@app.route('/admin/users', methods=['GET'])
@require_co_admin
def admin_get_users():
    """Haal alle gebruikers op met plugin counts"""
    users = load_users()
    plugins = load_plugins()
    user_data = []
    for u in users:
        plugin_count = len([p for p in plugins if p.get('owner') == u.get('username')])
        user_data.append({
            'username': u.get('username'),
            'role': u.get('role', 'user'),
            'plugin_count': plugin_count
        })
    return jsonify(user_data)


@app.route('/admin/users/<username>', methods=['DELETE'])
@require_admin
def admin_delete_user(username):
    """Verwijder gebruiker"""
    if username == 'admin':
        return jsonify({'error': 'Admin kan niet verwijderd worden'}), 400

    # delete from users table
    db.execute(f"DELETE FROM users WHERE username = {_esc(username)}")
    return jsonify({'success': True})


@app.route('/admin/settings', methods=['GET'])
@require_admin
def admin_get_settings():
    """Haal instellingen op"""
    try:
        return jsonify(load_settings())
    except Exception as e:
        app.logger.exception("Fout bij admin_get_settings")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/settings', methods=['POST'])
@require_co_admin
def admin_update_settings():
    """Update instellingen"""
    data = request.get_json() or {}
    if save_settings(data):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij opslaan'}), 500


@app.route('/admin/users/<username>/role', methods=['POST'])
@require_admin
def admin_change_role(username):
    """Wijzig gebruikersrol"""
    data = request.get_json() or {}
    new_role = data.get('role')
    if new_role not in ['user', 'co-admin', 'admin']:
        return jsonify({'error': 'Ongeldige rol'}), 400

    # find user, update role
    users = load_users()
    user = next((u for u in users if u.get('username') == username), None)
    if not user:
        return jsonify({'error': 'Gebruiker niet gevonden'}), 404
    user['role'] = new_role
    # save back (replace users table)
    if save_users(users):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij opslaan'}), 500


@app.route('/admin/plugins', methods=['GET'])
@require_co_admin
def admin_get_plugins():
    """Haal alle plugins op"""
    return jsonify(load_plugins())


@app.route('/admin/plugins/<path:url>', methods=['DELETE'])
@require_co_admin
def admin_delete_plugin(url):
    """Verwijder plugin (admin)"""
    if delete_any_plugin(url):
        return jsonify({'success': True})
    return jsonify({'error': 'Plugin niet gevonden'}), 404


# -------------------------
# Fetch plugin via launcher.py (keeps original behavior)
# -------------------------
@app.route('/fetch_plugin', methods=['POST'])
def fetch_plugin():
    """Haal plugin data op voor een gegeven URL"""
    try:
        data = request.get_json() or {}
        url = data.get('url')
        if not url:
            return jsonify({'error': 'Geen URL opgegeven'}), 400

        # Run launcher.py (same behaviour as original)
        result = subprocess.run(
            [sys.executable, 'launcher.py', url],
            capture_output=True,
            text=True,
            check=True
        )
        plugin_data = json_module.loads(result.stdout)
        return jsonify(plugin_data)
    except subprocess.CalledProcessError as e:
        app.logger.exception("launcher.py failed")
        return jsonify({'error': f'Fout bij ophalen plugin data: {e.stderr}'}), 500
    except Exception as e:
        app.logger.exception("Unexpected fetch_plugin error")
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500


# -------------------------
# Add / Delete plugin endpoints (preserve original names & behavior)
# -------------------------
@app.route('/add_plugin', methods=['POST'])
@require_login
def add_plugin():
    """Voeg een plugin toe aan de repository"""
    try:
        data = request.get_json() or {}
        plugin_data = data.get('plugin_data')
        if not plugin_data:
            return jsonify({'error': 'Geen plugin data opgegeven'}), 400

        username = session.get('admin') or session.get('user')
        success = add_user_plugin(username, plugin_data)
        if success:
            return jsonify({'success': True, 'message': 'Plugin succesvol toegevoegd'})
        return jsonify({'error': 'Fout bij opslaan plugin'}), 500
    except Exception as e:
        app.logger.exception("Unexpected add_plugin error")
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500


@app.route('/delete_plugin', methods=['POST'])
@require_login
def delete_plugin():
    """Verwijder een plugin uit de repository"""
    try:
        data = request.get_json() or {}
        url = data.get('url')
        if not url:
            return jsonify({'error': 'Geen URL opgegeven'}), 400

        username = session.get('user')
        user = get_current_user()

        # Admin en co-admin kunnen elke plugin verwijderen
        if user and user.get('role') in ['admin', 'co-admin']:
            if delete_any_plugin(url):
                return jsonify({'success': True, 'message': 'Plugin succesvol verwijderd'})
        # Normale gebruikers kunnen alleen hun eigen plugins verwijderen
        elif delete_user_plugin(username, url):
            return jsonify({'success': True, 'message': 'Plugin succesvol verwijderd'})

        return jsonify({'error': 'Plugin niet gevonden of fout bij verwijderen'}), 404
    except Exception as e:
        app.logger.exception("Unexpected delete_plugin error")
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@app.route('/change_password', methods=['POST'])
def change_password():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request data"}), 400

    username = data.get("username")
    new_password = data.get("newPassword")
    old_password = data.get("oldPassword")

    if not username or not new_password or not old_password:
        return jsonify({"error": "All fields are required"}), 400

    # ✅ Properly quoted SQL for SoketDB
    is_admin = db.execute(
        f"SELECT password FROM admins WHERE username = '{username}' AND password = '{old_password}'"
    )
    is_user = db.execute(
        f"SELECT password FROM users WHERE username = '{username}' AND password = '{old_password}'"
    )

    if is_admin:
        db.execute(
            f"UPDATE admins SET password = '{new_password}' WHERE username = '{username}' AND password = '{old_password}'"
        )
        return jsonify({"success": "Admin password change successful"})

    elif is_user:
        db.execute(
            f"UPDATE users SET password = '{new_password}' WHERE username = '{username}' AND password = '{old_password}'"
        )
        return jsonify({"success": f"{username} password change successful"})

    else:
        return jsonify({"error": "No user found with these details"}), 404
    
# -------------------------
# Run
# -------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)