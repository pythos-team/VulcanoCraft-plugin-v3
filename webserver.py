from flask import Flask, json, jsonify, request, send_file
import os
import json as json_module
import urllib.parse
import subprocess

app = Flask(__name__)

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
        print(f"极ut bij het opslaan van plugins: {e}")
        return False

@app.route('/')
def index():
    """Serveer de index.html pagina"""
    return send_file('index.html')

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
def api_plugins():
    """API endpoint voor plugins data"""
    plugins = load_plugins()
    return jsonify(plugins)

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
            ['python', 'launcher.py', url],
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
def add_plugin():
    """Voeg een plugin toe aan de repository"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': '极en URL opgegeven'}), 400
        
        # Voer launcher.py uit met confirm parameter
        result = subprocess.run(
            ['python', 'launcher.py', url, 'confirm'],
            capture_output=True,
            text=True,
            check=True
        )
        
        return jsonify({'success': True, 'message': 'Plugin succesvol toegevoegd'})
        
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Fout bij toevoegen plugin: {e.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@app.route('/delete_plugin', methods=['POST'])
def delete_plugin():
    """Verwijder een plugin uit de repository"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'Geen URL opgegeven'}), 400
        
        # Laad huidige plugins
        plugins = load_plugins()
        
        # Filter de plugin met de opgegeven URL eruit
        new_plugins = [p for p in plugins if p.get('url') != url]
        
        # Controleer of er iets is verwijderd
        if len(new_plugins) == len(plugins):
            return jsonify({'error': 'Plugin niet gevonden'}), 404
        
        # Sla de nieuwe lijst op
        if save_plugins(new_plugins):
            return jsonify({'success': True, 'message': 'Plugin succesvol verwijderd'})
        else:
            return jsonify({'error': 'Fout bij opslaan van plugins'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)