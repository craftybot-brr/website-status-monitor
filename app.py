from flask import Flask, render_template, jsonify, request
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import os

app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# 4 Pages of 10 websites each, organized by category
PAGES = {
    1: {
        "name": "Search & Social",
        "websites": [
            {"name": "Google", "url": "https://www.google.com", "icon": "🔍"},
            {"name": "Bing", "url": "https://www.bing.com", "icon": "🔍"},
            {"name": "DuckDuckGo", "url": "https://duckduckgo.com", "icon": "🦆"},
            {"name": "Yahoo", "url": "https://www.yahoo.com", "icon": "📰"},
            {"name": "Facebook", "url": "https://www.facebook.com", "icon": "📘"},
            {"name": "Twitter", "url": "https://www.twitter.com", "icon": "🐦"},
            {"name": "Instagram", "url": "https://www.instagram.com", "icon": "📸"},
            {"name": "LinkedIn", "url": "https://www.linkedin.com", "icon": "💼"},
            {"name": "TikTok", "url": "https://www.tiktok.com", "icon": "🎵"},
            {"name": "Reddit", "url": "https://www.reddit.com", "icon": "👽"},
        ],
    },
    2: {
        "name": "Streaming & Media",
        "websites": [
            {"name": "YouTube", "url": "https://www.youtube.com", "icon": "📺"},
            {"name": "Netflix", "url": "https://www.netflix.com", "icon": "🎬"},
            {"name": "Hulu", "url": "https://www.hulu.com", "icon": "📺"},
            {"name": "Amazon Prime Video", "url": "https://www.primevideo.com", "icon": "🎬"},
            {"name": "Disney+", "url": "https://www.disneyplus.com", "icon": "🧚"},
            {"name": "Spotify", "url": "https://www.spotify.com", "icon": "🎵"},
            {"name": "Apple Music", "url": "https://www.music.apple.com", "icon": "🎶"},
            {"name": "SoundCloud", "url": "https://www.soundcloud.com", "icon": "☁️"},
            {"name": "Twitch", "url": "https://www.twitch.tv", "icon": "🎮"},
            {"name": "Vimeo", "url": "https://www.vimeo.com", "icon": "🎞️"},
        ],
    },
    3: {
        "name": "E-Commerce",
        "websites": [
            {"name": "Amazon", "url": "https://www.amazon.com", "icon": "🛒"},
            {"name": "eBay", "url": "https://www.ebay.com", "icon": "🏷️"},
            {"name": "Walmart", "url": "https://www.walmart.com", "icon": "🛍️"},
            {"name": "Etsy", "url": "https://www.etsy.com", "icon": "🧵"},
            {"name": "Best Buy", "url": "https://www.bestbuy.com", "icon": "💻"},
            {"name": "Shopify", "url": "https://www.shopify.com", "icon": "🛍️"},
            {"name": "Target", "url": "https://www.target.com", "icon": "🎯"},
            {"name": "AliExpress", "url": "https://www.aliexpress.com", "icon": "📦"},
            {"name": "Newegg", "url": "https://www.newegg.com", "icon": "🐣"},
            {"name": "Craigslist", "url": "https://www.craigslist.org", "icon": "📃"},
        ],
    },
    4: {
        "name": "Dev & Infra",
        "websites": [
            {"name": "GitHub", "url": "https://www.github.com", "icon": "🐙"},
            {"name": "GitLab", "url": "https://www.gitlab.com", "icon": "🦊"},
            {"name": "Bitbucket", "url": "https://bitbucket.org", "icon": "🪣"},
            {"name": "Stack Overflow", "url": "https://stackoverflow.com", "icon": "❓"},
            {"name": "Docker Hub", "url": "https://hub.docker.com", "icon": "🐳"},
            {"name": "PyPI", "url": "https://pypi.org", "icon": "📦"},
            {"name": "npm", "url": "https://www.npmjs.com", "icon": "📦"},
            {"name": "Azure", "url": "https://azure.microsoft.com", "icon": "☁️"},
            {"name": "AWS", "url": "https://aws.amazon.com", "icon": "☁️"},
            {"name": "Google Cloud", "url": "https://cloud.google.com", "icon": "☁️"},
        ],
    },
}

status_data_lock = threading.Lock()
status_data = {}  # Populated by update_status_data()

def check_website_status(site):
    name = site["name"]
    url = site["url"]
    icon = site["icon"]

    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = int((time.time() - start_time) * 1000)  # ms

        status = {
            "name": name,
            "url": url,
            "icon": icon,
            "status_code": response.status_code,
            "response_time": response_time,
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if response.status_code >= 500:
            status["status"] = "down"
            status["message"] = f"Server error (HTTP {response.status_code})"
        elif response.status_code == 429:
            status["status"] = "degraded"
            status["message"] = "Rate limited"
        elif response.status_code >= 400 and response.status_code != 403:
            status["status"] = "degraded"
            status["message"] = f"Client error (HTTP {response.status_code})"
        elif response_time > 10000:
            status["status"] = "degraded"
            status["message"] = f"Very slow response ({response_time} ms)"
        elif response_time > 5000:
            status["status"] = "degraded"
            status["message"] = f"Slow response ({response_time} ms)"
        else:
            status["status"] = "operational"
            status["message"] = "OK"
    except Exception as e:
        status = {
            "name": name,
            "url": url,
            "icon": icon,
            "status": "down",
            "status_code": "Error",
            "response_time": None,
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"Unknown error: {str(e)[:50]}",
        }

    return status

def update_status_data():
    """Update status data for all websites across all pages."""
    global status_data
    print("Updating status data for all pages...")

    tasks = {}
    new_status_data = {}

    with ThreadPoolExecutor(max_workers=20) as executor:
        for page_num, page in PAGES.items():
            for site in page["websites"]:
                future = executor.submit(check_website_status, site)
                tasks[future] = (page_num, page["name"])

        for future in as_completed(tasks):
            page_num, page_name = tasks[future]
            status = future.result()
            status["page"] = page_num
            status["page_name"] = page_name
            new_status_data[f"{page_num}_{status['name']}"] = status
            print(f"  ✓ {status['name']}: {status['status']}")

    with status_data_lock:
        status_data = new_status_data

def background_monitor():
    """Background thread that refreshes status data every 60 s."""
    while True:
        update_status_data()
        time.sleep(60)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    """Return status for all websites or for a specific page."""
    page = request.args.get("page", type=int)
    if page and page in PAGES:
        with status_data_lock:
            page_websites = [
                v for k, v in status_data.items() if v["page"] == page
            ]
        total_websites = len(page_websites)
        operational_count = len([s for s in page_websites if s["status"] == "operational"])
        degraded_count = len([s for s in page_websites if s["status"] == "degraded"])
        down_count = len([s for s in page_websites if s["status"] == "down"])

        return jsonify(
            {
                "page": page,
                "page_name": PAGES[page]["name"],
                "websites": page_websites,
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_websites": total_websites,
                "operational_count": operational_count,
                "degraded_count": degraded_count,
                "down_count": down_count,
            }
        )
    else:
        with status_data_lock:
            all_websites = list(status_data.values())
        return jsonify(
            {
                "websites": all_websites,
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_websites": len(all_websites),
                "operational_count": len([s for s in all_websites if s["status"] == "operational"]),
                "degraded_count": len([s for s in all_websites if s["status"] == "degraded"]),
                "down_count": len([s for s in all_websites if s["status"] == "down"]),
            }
        )

@app.route("/api/pages")
def get_pages():
    return jsonify(
        {
            "pages": {num: data["name"] for num, data in PAGES.items()},
            "total_pages": len(PAGES),
        }
    )

@app.route("/api/status/<website_name>")
def get_website_status(website_name):
    with status_data_lock:
        for s in status_data.values():
            if s["name"].lower() == website_name.lower():
                return jsonify(s)
    return jsonify({"error": "Website not found"}), 404

if __name__ == "__main__":
    print("Initializing website status monitor with pages system…")
    print(f"Total pages: {len(PAGES)}")
    print(f"Total websites: {sum(len(p['websites']) for p in PAGES.values())}")

    update_status_data()

    # Background monitor (non-daemon so we can join on shutdown)
    monitor_thread = threading.Thread(target=background_monitor, daemon=False)
    monitor_thread.start()

    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "8080"))

    try:
        app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
    except KeyboardInterrupt:
        print("Keyboard interrupt received, shutting down.")
    finally:
        print("Stopping monitor…")
        monitor_thread.join(timeout=5)
        print("Monitor stopped.")