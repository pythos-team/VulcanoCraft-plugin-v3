import json
import time
import subprocess
import os
import sys
from datetime import datetime, timedelta

def load_plugins():
    """Laad de plugins data uit het JSON bestand"""
    try:
        if os.path.exists('plugins.json'):
            with open('plugins.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Fout bij het laden van plugins: {e}")
        return []

def update_plugin(url):
    """Voer launcher.py uit voor een specifieke plugin URL met confirm"""
    try:
        print(f"Bijwerken plugin: {url}")
        
        # Gebruik dezelfde Python interpreter als het huidige proces
        python_executable = sys.executable
        
        # Voer launcher.py uit met confirm parameter
        result = subprocess.run(
            [python_executable, 'launcher.py', url, 'confirm'],
            capture_output=True,
            text=True,
            check=True,
            timeout=300  # Timeout na 5 minuten
        )
        
        # Toon de output van launcher.py
        if result.stdout:
            print(result.stdout)
        
        print(f"Plugin succesvol bijgewerkt: {url}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Fout bij bijwerken plugin {url}:")
        print(f"Error output: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        return False
    except subprocess.TimeoutExpired:
        print(f"Timeout bij bijwerken plugin {url}")
        return False
    except Exception as e:
        print(f"Onverwachte fout bij bijwerken plugin {url}: {e}")
        return False

def main():
    """Hoofdfunctie die elk uur alle plugins bijwerkt"""
    print("Cron service gestart - Ctrl+C om te stoppen")
    print(f"Python executable: {sys.executable}")
    print("-" * 50)
    
    # Oneindige loop
    while True:
        try:
            # Laad huidige plugins
            plugins = load_plugins()
            
            if not plugins:
                print("Geen plugins gevonden om bij te werken")
            else:
                print(f"Start bijwerken van {len(plugins)} plugin(s)")
                
                # Bijwerken van elke plugin
                success_count = 0
                for plugin in plugins:
                    url = plugin.get('url')
                    if url:
                        if update_plugin(url):
                            success_count += 1
                    else:
                        print("Plugin zonder URL gevonden, overslaan...")
                
                print(f"Bijwerken voltooid: {success_count}/{len(plugins)} plugins succesvol bijgewerkt")
            
            # Wacht 1 uur tot volgende update
            next_run = datetime.now() + timedelta(hours=1)
            print(f"Volgende update om: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)
            
            # Wacht 1 uur (3600 seconden)
            time.sleep(3600)
            
        except KeyboardInterrupt:
            print("\nCron service gestopt door gebruiker")
            break
        except Exception as e:
            print(f"Onverwachte fout in hoofdloop: {e}")
            # Wacht 5 minuten voordat we opnieuw proberen bij een fout
            time.sleep(300)

if __name__ == "__main__":
    main()