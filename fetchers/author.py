import argparse
import re
import requests
import sys
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# -------- MODRINTH --------
def get_modrinth_author(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        team_id = data.get("team")
        if not team_id:
            return None
            
        team_url = f"https://api.modrinth.com/v2/team/{team_id}/members"
        team_response = requests.get(team_url)
        team_response.raise_for_status()
        team_data = team_response.json()
        
        # Verzamel alle auteurs
        authors = []
        for member in team_data:
            if 'user' in member and isinstance(member['user'], dict):
                username = member['user'].get("username")
                if username:
                    authors.append(username)
        
        # Return alle auteurs gescheiden door spaties
        return " ".join(authors) if authors else None
        
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_author(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='domcontentloaded')

            try:
                page.wait_for_selector('.sidebar .section .secondaryContent', timeout=3000)
                
                author_selectors = [
                    '.author a',
                    '.secondaryContent a[href*="/members/"]',
                    '.secondaryContent a[href*="/authors/"]',
                    '.statistic a[href*="/members/"]',
                    '.statistic a[href*="/authors/"]'
                ]
                
                for selector in author_selectors:
                    author_link = page.query_selector(selector)
                    if author_link:
                        author_name = author_link.inner_text().strip()
                        if author_name and not any(x in author_name.lower() for x in ['tools', 'utilities', 'category', 'download']):
                            browser.close()
                            return author_name
                
                all_links = page.query_selector_all('a')
                for link in all_links:
                    href = link.get_attribute('href') or ''
                    if ('/members/' in href or '/authors/' in href) and not ('/resources/' in href):
                        author_name = link.inner_text().strip()
                        if author_name and len(author_name) > 2 and not any(x in author_name.lower() for x in ['tools', 'utilities', 'category', 'download']):
                            browser.close()
                            return author_name
                
                browser.close()
                return None
                
            except Exception:
                browser.close()
                return None
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_author(combined_slug):
    try:
        # Voor Hangar is de auteur het eerste deel van de slug
        parts = combined_slug.split('/')
        if len(parts) >= 1:
            return parts[0]
        return None
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_author(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(2000)

            try:
                all_links = page.query_selector_all("a[href*='/members/']")
                if all_links:
                    author = all_links[0].inner_text().strip()
                    if author:
                        browser.close()
                        return author
            except Exception:
                pass
            
            browser.close()
            return None
    except Exception:
        return None

# -------- PLATFORM DETECTION --------
def detect_platform(url):
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        if "modrinth.com" in host:
            match = re.search(r"/(plugin|mod|datapack)/([^/]+)/?", parsed.path)
            if match:
                return "modrinth", match.group(2)

        elif "spigotmc.org" in host:
            return "spigot", url

        elif "hangar.papermc.io" in host:
            match = re.search(r"/([^/]+)/([^/]+)/?$", parsed.path)
            if match:
                author = match.group(1)
                project = match.group(2)
                return "hangar", f"{author}/{project}"

        elif "curseforge.com" in host:
            return "curseforge", url

        return None, None
    except Exception:
        return None, None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin author from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if platform == "modrinth":
        author = get_modrinth_author(identifier)
    elif platform == "spigot":
        author = get_spigot_author(identifier)
    elif platform == "hangar":
        author = get_hangar_author(identifier)
    elif platform == "curseforge":
        author = get_curseforge_author(identifier)
    else:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if author is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(author)

if __name__ == "__main__":
    main()