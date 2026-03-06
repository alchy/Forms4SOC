#!/usr/bin/env python3
"""
Stáhne Ace Editor pro lokální použití (bez připojení k internetu).

Spusť jednorázově před prvním použitím editoru šablon:
    python scripts/download_ace.py
"""
import urllib.request
from pathlib import Path

ACE_VERSION = "1.32.9"
BASE_URL = f"https://cdnjs.cloudflare.com/ajax/libs/ace/{ACE_VERSION}"

# (url_soubor, lokální_název)
FILES = [
    ("ace.min.js",            "ace.js"),
    ("mode-json.min.js",      "mode-json.js"),
    ("theme-tomorrow.min.js", "theme-tomorrow.js"),
]

target_dir = Path(__file__).parent.parent / "app" / "static" / "vendor" / "ace"
target_dir.mkdir(parents=True, exist_ok=True)

print(f"Target dir: {target_dir}\n")
for url_file, local_name in FILES:
    url = f"{BASE_URL}/{url_file}"
    target = target_dir / local_name
    print(f"Stahuji {url} ...")
    urllib.request.urlretrieve(url, target)
    size_kb = target.stat().st_size // 1024
    print(f"  → {local_name} ({size_kb} KB)\n")

print("Done. Ace Editor ready in app/static/vendor/ace/")
