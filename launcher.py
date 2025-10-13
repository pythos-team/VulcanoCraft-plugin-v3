import json
import os
import subprocess
import sys

def run_script(script_name, url):
    """Voert een Python script uit uit de fetchers map met de gegeven URL en retourneert de output"""
    try:
        result = subprocess.run(
            [sys.executable, f'fetchers/{script_name}.py', url],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Fout bij uitvoeren fetchers/{script_name}.py: {e}", file=sys.stderr)
        return ""

def get_plugin_data(url):
    """Haalt alle plugin data op voor een gegeven URL"""
    versions = run_script('versions', url)
    
    titles = run_script('titles', url)
    
    icon = run_script('icon', url)
    
    description = run_script('description', url)
    
    author = run_script('author', url)
    
    # Maak plugin object
    plugin = {
        "url": url,
        "title": titles,
        "description": description,
        "author": author,
        "icon": icon,
        "versions": versions
    }
    
    return plugin

def save_to_file(plugin):
    """Slaat een plugin op in het plugins.json bestand"""
    # Lees bestaande data of initialiseer lege lijst
    if os.path.exists('plugins.json'):
        with open('plugins.json', 'r', encoding='utf-8') as f:
            try:
                plugins = json.load(f)
            except json.JSONDecodeError:
                plugins = []
    else:
        plugins = []
    
    # Verwijder bestaande plugin met dezelfde URL
    plugins = [p for p in plugins if p['url'] != plugin['url']]
    
    # Voeg nieuwe plugin toe
    plugins.append(plugin)
    
    # Schrijf terug naar bestand
    with open('plugins.json', 'w', encoding='utf-8') as f:
        json.dump(plugins, f, indent=4, ensure_ascii=False)
    
    print(f"Plugin {plugin['url']} is opgeslagen in plugins.json!")

def main():
    # Controleer command-line argumenten
    if len(sys.argv) < 2:
        print("Gebruik: python launcher.py <url> [confirm]")
        sys.exit(1)
    
    url = sys.argv[1].strip()
    confirm = len(sys.argv) > 2 and sys.argv[2].lower() == 'confirm'
    
    # Haal plugin data op
    plugin = get_plugin_data(url)
    
    # Toon de JSON structuur
    print(json.dumps(plugin, indent=4, ensure_ascii=False))
    
    # Als confirm is opgegeven, sla dan op
    if confirm:
        save_to_file(plugin)

if __name__ == "__main__":
    main()