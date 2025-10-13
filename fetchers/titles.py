import argparse
import re
import requests
import sys
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# -------- MODRINTH --------
def get_modrinth_title(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("title")
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_title(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='domcontentloaded')

            try:
                page.wait_for_selector("h1.resource-title__name", timeout=3000)
                title_element = page.query_selector("h1.resource-title__name")
                
                if title_element:
                    full_text = title_element.inner_text().strip()
                    title = full_text.rsplit(' ', 1)[0]
                    browser.close()
                    return title
            except Exception:
                title = page.title()
                if title and "|" in title:
                    title = title.split("|")[0].strip()
                browser.close()
                return title

            browser.close()
            return None
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_title(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("name")
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
    parser = argparse.ArgumentParser(description="Extract plugin title from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if platform == "modrinth":
        title = get_modrinth_title(identifier)
    elif platform == "spigot":
        title = get_spigot_title(identifier)
    elif platform == "hangar":
        title = get_hangar_title(identifier)
    else:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if title is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(title)

if __name__ == "__main__":
    main()