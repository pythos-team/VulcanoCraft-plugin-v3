import argparse
import re
import requests
import sys
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# -------- MODRINTH --------
def get_modrinth_description(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("description")
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_description(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='domcontentloaded')

            try:
                page.wait_for_selector("p.tagline", timeout=3000)
                description_element = page.query_selector("p.tagline")
                description = description_element.inner_text().strip() if description_element else None
            except Exception:
                description_element = page.query_selector('meta[name="description"]')
                if description_element:
                    description = description_element.get_attribute("content")
                else:
                    description = None

            browser.close()
            return description
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_description(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("description")
    except Exception:
        return None

# -------- PLATFORM DETECTION --------
def detect_platform(url):
    try:
        parsed = urlparse(url)
        host = parsed.netloc

        if "modrinth.com" in host:
            match = re.search(r"/(plugin|mod)/([^/]+)/?", parsed.path)
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
    parser = argparse.ArgumentParser(description="Extract plugin description from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if platform == "modrinth":
        description = get_modrinth_description(identifier)
    elif platform == "spigot":
        description = get_spigot_description(identifier)
    elif platform == "hangar":
        description = get_hangar_description(identifier)
    else:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if description is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(description)

if __name__ == "__main__":
    main()