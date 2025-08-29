import argparse
import re
import requests
import sys
from urllib.parse import urlparse, urlunparse
from playwright.sync_api import sync_playwright

# -------- MODRINTH --------
def get_modrinth_icon(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        icon_url = data.get("icon_url")
        if icon_url:
            # Verwijder query parameters
            parsed = urlparse(icon_url)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return None
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_icon(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)

            try:
                # Specifiek zoeken naar de resourceIcon zoals in de afbeelding
                page.wait_for_selector("img.resourceIcon", timeout=10000)
                icon_element = page.query_selector("img.resourceIcon")
                
                if icon_element:
                    icon_url = icon_element.get_attribute("src")
                    if icon_url:
                        # Verwijder query parameters (alles na .jpg, .png, etc.)
                        if '?' in icon_url:
                            icon_url = icon_url.split('?')[0]
                        
                        # Make sure the URL is absolute
                        if icon_url.startswith("http"):
                            return icon_url
                        else:
                            # Convert relative URL to absolute
                            parsed_base = urlparse(url)
                            # Voor SpigotMC icons die beginnen met data/
                            if icon_url.startswith("data/"):
                                return f"https://www.spigotmc.org/{icon_url}"
                            else:
                                return f"{parsed_base.scheme}://{parsed_base.netloc}{icon_url}"
            except Exception:
                # Fallback: probeer andere common selectors
                try:
                    page.wait_for_selector("img.resource-icon, .resource-image img", timeout=5000)
                    icon_element = page.query_selector("img.resource-icon, .resource-image img")
                    if icon_element:
                        icon_url = icon_element.get_attribute("src")
                        if icon_url:
                            if '?' in icon_url:
                                icon_url = icon_url.split('?')[0]
                            if icon_url.startswith("http"):
                                return icon_url
                            else:
                                parsed_base = urlparse(url)
                                if icon_url.startswith("data/"):
                                    return f"https://www.spigotmc.org/{icon_url}"
                                else:
                                    return f"{parsed_base.scheme}://{parsed_base.netloc}{icon_url}"
                except:
                    pass
                
                return None
            finally:
                browser.close()
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_icon(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Gebruik het avatarUrl veld en verwijder query parameters
        avatar_url = data.get("avatarUrl")
        if avatar_url:
            parsed = urlparse(avatar_url)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
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

        return None, None
    except Exception:
        return None, None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin icon URL from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL")
        sys.exit(1)

    if platform == "modrinth":
        icon_url = get_modrinth_icon(identifier)
    elif platform == "spigot":
        icon_url = get_spigot_icon(identifier)
    elif platform == "hangar":
        icon_url = get_hangar_icon(identifier)
    else:
        print("Invalid URL")
        sys.exit(1)

    if icon_url is None:
        print("No icon found")
        sys.exit(1)
    else:
        print(icon_url)

if __name__ == "__main__":
    main()