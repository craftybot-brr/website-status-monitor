from flask import Flask, render_template, jsonify, request, make_response
import requests
import time
import threading
from datetime import datetime
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Add cache control headers to prevent API response caching
def add_cache_headers(response):
    """Add headers to prevent caching of API responses for both browsers and Cloudflare"""
    # Browser cache control
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['ETag'] = str(int(time.time()))
    
    # Cloudflare-specific headers to prevent edge caching
    response.headers['CF-Cache-Status'] = 'BYPASS'
    response.headers['Edge-Cache-TTL'] = '0'
    response.headers['CDN-Cache-Control'] = 'no-cache'
    
    # Ensure real-time data
    response.headers['Vary'] = 'Accept, Accept-Encoding, User-Agent'
    
    return response

def add_static_cache_headers(response):
    """Add cache headers for static content that should be cached by Cloudflare"""
    # Cache static assets for 1 hour at edge, 1 day in browser
    response.headers['Cache-Control'] = 'public, max-age=86400'  # 24 hours browser cache
    response.headers['Edge-Cache-TTL'] = '3600'  # 1 hour Cloudflare cache
    response.headers['CDN-Cache-Control'] = 'public, max-age=3600'
    
    return response

def add_html_cache_headers(response):
    """Add cache headers for HTML content with short cache time"""
    # Short cache for HTML to allow updates but improve performance
    response.headers['Cache-Control'] = 'public, max-age=60'  # 1 minute browser cache
    response.headers['Edge-Cache-TTL'] = '30'  # 30 seconds Cloudflare cache
    response.headers['CDN-Cache-Control'] = 'public, max-age=30'
    
    return response

@app.after_request
def after_request(response):
    """Add appropriate cache control headers based on content type"""
    # API endpoints - no caching
    if request.path.startswith('/api/'):
        response = add_cache_headers(response)
    # Static assets - long cache
    elif request.path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf')):
        response = add_static_cache_headers(response)
    # HTML pages - short cache
    elif request.path.endswith('.html') or request.path == '/':
        response = add_html_cache_headers(response)
    
    # Add CORS headers for API requests
    if request.path.startswith('/api/'):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Cache-Control, Pragma'
    
    return response

# 4 Pages of 10 websites each, organized by category
PAGES = {
    1: {
        "name": "Search & Social",
        "websites": [
            {"name": "Google", "url": "https://www.google.com", "icon": "🔍"},
            {"name": "YouTube", "url": "https://www.youtube.com", "icon": "📺"},
            {"name": "Facebook", "url": "https://www.facebook.com", "icon": "📘"},
            {"name": "Instagram", "url": "https://www.instagram.com", "icon": "📸"},
            {"name": "Twitter/X", "url": "https://www.twitter.com", "icon": "🐦"},
            {"name": "LinkedIn", "url": "https://www.linkedin.com", "icon": "💼"},
            {"name": "TikTok", "url": "https://www.tiktok.com", "icon": "🎵"},
            {"name": "Reddit", "url": "https://www.reddit.com", "icon": "👽"},
            {"name": "Pinterest", "url": "https://www.pinterest.com", "icon": "📌"},
            {"name": "Snapchat", "url": "https://www.snapchat.com", "icon": "👻"},
        ],
    },
    2: {
        "name": "Tech & Development",
        "websites": [
            {"name": "GitHub", "url": "https://www.github.com", "icon": "🐙"},
            {"name": "Stack Overflow", "url": "https://stackoverflow.com", "icon": "❓"},
            {"name": "Microsoft", "url": "https://www.microsoft.com", "icon": "🏢"},
            {"name": "Apple", "url": "https://www.apple.com", "icon": "🍎"},
            {"name": "AWS", "url": "https://aws.amazon.com", "icon": "☁️"},
            {"name": "Cloudflare", "url": "https://www.cloudflare.com", "icon": "🌩️"},
            {"name": "Atlassian", "url": "https://www.atlassian.com", "icon": "🔧"},
            {"name": "Docker", "url": "https://www.docker.com", "icon": "🐳"},
            {"name": "NPM", "url": "https://www.npmjs.com", "icon": "📦"},
            {"name": "PyPI", "url": "https://pypi.org", "icon": "🐍"},
        ],
    },
    3: {
        "name": "Entertainment & Media",
        "websites": [
            {"name": "Netflix", "url": "https://www.netflix.com", "icon": "🎬"},
            {"name": "Spotify", "url": "https://www.spotify.com", "icon": "🎵"},
            {"name": "Disney+", "url": "https://www.disneyplus.com", "icon": "🧚"},
            {"name": "Twitch", "url": "https://www.twitch.tv", "icon": "🎮"},
            {"name": "Steam", "url": "https://store.steampowered.com", "icon": "🎮"},
            {"name": "Epic Games", "url": "https://www.epicgames.com", "icon": "🎮"},
            {"name": "PlayStation", "url": "https://www.playstation.com", "icon": "🎮"},
            {"name": "Xbox", "url": "https://www.xbox.com", "icon": "🎮"},
            {"name": "HBO Max", "url": "https://www.hbomax.com", "icon": "🎬"},
            {"name": "Hulu", "url": "https://www.hulu.com", "icon": "📺"},
        ],
    },
    4: {
        "name": "E-commerce & Services",
        "websites": [
            {"name": "Amazon", "url": "https://www.amazon.com", "icon": "🛒"},
            {"name": "eBay", "url": "https://www.ebay.com", "icon": "🏷️"},
            {"name": "PayPal", "url": "https://www.paypal.com", "icon": "💳"},
            {"name": "Stripe", "url": "https://www.stripe.com", "icon": "💳"},
            {"name": "Shopify", "url": "https://www.shopify.com", "icon": "🛍️"},
            {"name": "Etsy", "url": "https://www.etsy.com", "icon": "🧵"},
            {"name": "Uber", "url": "https://www.uber.com", "icon": "🚗"},
            {"name": "Airbnb", "url": "https://www.airbnb.com", "icon": "🏠"},
            {"name": "DoorDash", "url": "https://www.doordash.com", "icon": "🚪"},
            {"name": "Zoom", "url": "https://www.zoom.us", "icon": "📹"},
        ],
    },
}

# Global variable to store status data with thread safety
status_data_lock = threading.Lock()
status_data = {}

def check_website_status(site):
    """Check the status of a single website"""
    name = site["name"]
    url = site["url"]
    icon = site["icon"]
    
    # Headers to make requests look more like a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        start_time = time.time()
        response = requests.get(url, timeout=15, headers=headers)
        response_time = int((time.time() - start_time) * 1000)  # Convert to ms

        status = {
            "name": name,
            "url": url,
            "icon": icon,
            "status_code": response.status_code,
            "response_time": response_time,
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Determine status based on response code and time
        if response.status_code >= 500:
            status["status"] = "down"
            status["message"] = f"Server error (HTTP {response.status_code})"
        elif response.status_code == 429:
            status["status"] = "degraded"
            status["message"] = "Rate limited"
        elif response.status_code >= 400 and response.status_code != 403:
            status["status"] = "degraded"
            status["message"] = f"Client error (HTTP {response.status_code})"
        elif response_time > 15000:  # 15 seconds
            status["status"] = "down"
            status["message"] = f"Very slow response ({response_time} ms)"
        elif response_time > 5000:  # 5 seconds
            status["status"] = "degraded"
            status["message"] = f"Slow response ({response_time} ms)"
        elif response.status_code == 403:
            # Many sites return 403 for automated requests - consider operational if fast
            status["status"] = "operational" if response_time < 5000 else "degraded"
            status["message"] = f"Access restricted (HTTP 403) - {response_time} ms"
        else:
            status["status"] = "operational"
            status["message"] = f"OK - {response_time} ms"

    except requests.exceptions.Timeout:
        status = {
            "name": name,
            "url": url,
            "icon": icon,
            "status": "down",
            "status_code": "Timeout",
            "response_time": None,
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Connection timeout (15s)",
        }
    except requests.exceptions.ConnectionError:
        status = {
            "name": name,
            "url": url,
            "icon": icon,
            "status": "down",
            "status_code": "Connection Error",
            "response_time": None,
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Connection failed",
        }
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
    """Update status data for all websites across all pages using parallel processing."""
    global status_data
    start_time = time.time()
    print(f"\n🔄 Updating status data for all pages... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    
    new_status_data = {}
    tasks = {}
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Submit all tasks
        for page_num, page_data in PAGES.items():
            page_name = page_data['name']
            print(f"Checking Page {page_num}: {page_name}")
            
            for website in page_data['websites']:
                future = executor.submit(check_website_status, website)
                tasks[future] = (page_num, page_name, website['name'])
        
        # Collect results
        for future in as_completed(tasks):
            page_num, page_name, website_name = tasks[future]
            try:
                status = future.result()
                status['page'] = page_num
                status['page_name'] = page_name
                new_status_data[f"{page_num}_{website_name}"] = status
                print(f"  ✓ {website_name}: {status['status']}")
            except Exception as e:
                print(f"  ✗ {website_name}: Error - {str(e)}")

    # Thread-safe update
    with status_data_lock:
        status_data = new_status_data
    
    update_duration = time.time() - start_time
    total_sites = len(new_status_data)
    operational_count = len([s for s in new_status_data.values() if s['status'] == 'operational'])
    degraded_count = len([s for s in new_status_data.values() if s['status'] == 'degraded'])
    down_count = len([s for s in new_status_data.values() if s['status'] == 'down'])
    
    print(f"📊 Update complete: {total_sites} sites checked in {update_duration:.2f}s")
    print(f"   Status: {operational_count} operational, {degraded_count} degraded, {down_count} down")
    print(f"   Next update in 60 seconds\n")

def background_monitor():
    """Background thread that refreshes status data every 60 seconds."""
    while True:
        update_status_data()
        time.sleep(60)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    """API endpoint to get current status of all websites or a specific page"""
    page = request.args.get('page', type=int)
    timestamp = request.args.get('_t')  # Cache-busting parameter
    force_id = request.args.get('force')  # Force refresh parameter
    
    # Determine if this is a force refresh request
    is_force_refresh = bool(force_id or request.args.get('bypass') or request.args.get('fresh'))
    
    if is_force_refresh:
        print(f"🚀 FORCE REFRESH API Request: /api/status [{datetime.now().strftime('%H:%M:%S')}]")
        print(f"   Force ID: {force_id}")
        # Trigger immediate status update for force refresh
        update_status_data()
    else:
        print(f"🌐 API Request: /api/status?page={page}&_t={timestamp} [{datetime.now().strftime('%H:%M:%S')}]")
    
    with status_data_lock:
        # Get cache status from request headers (set by Cloudflare)
        cf_cache_status = request.headers.get('CF-Cache-Status', 'UNKNOWN')
        cf_ray = request.headers.get('CF-RAY', 'UNKNOWN')
        
        # Common response data
        current_timestamp = int(time.time())
        last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if page and page in PAGES:
            # Return specific page
            page_websites = [status for key, status in status_data.items() if status.get('page') == page]
            total_websites = len(page_websites)
            operational_count = len([s for s in page_websites if s["status"] == "operational"])
            degraded_count = len([s for s in page_websites if s["status"] == "degraded"])
            down_count = len([s for s in page_websites if s["status"] == "down"])

            response_data = {
                "page": page,
                "page_name": PAGES[page]["name"],
                "websites": page_websites,
                "last_update": last_update_time,
                "total_websites": total_websites,
                "operational_count": operational_count,
                "degraded_count": degraded_count,
                "down_count": down_count,
                "timestamp": current_timestamp,
                "cache_buster": timestamp,
                "force_refresh": is_force_refresh,
                "cf_cache_status": cf_cache_status,
                "cf_ray": cf_ray,
                "data_freshness": "real-time" if is_force_refresh else "cached"
            }
            print(f"   📄 Returning page {page} data: {total_websites} websites (CF: {cf_cache_status})")
            return jsonify(response_data)
        else:
            # Return all websites
            all_websites = list(status_data.values())
            response_data = {
                'websites': all_websites,
                'pages': {num: data['name'] for num, data in PAGES.items()},
                'last_update': last_update_time,
                'total_websites': len(all_websites),
                'operational_count': len([s for s in all_websites if s['status'] == 'operational']),
                'degraded_count': len([s for s in all_websites if s['status'] == 'degraded']),
                'down_count': len([s for s in all_websites if s['status'] == 'down']),
                'timestamp': current_timestamp,
                'cache_buster': timestamp,
                'force_refresh': is_force_refresh,
                'cf_cache_status': cf_cache_status,
                'cf_ray': cf_ray,
                'data_freshness': "real-time" if is_force_refresh else "cached"
            }
            print(f"   📄 Returning all data: {len(all_websites)} websites across {len(PAGES)} pages (CF: {cf_cache_status})")
            return jsonify(response_data)

@app.route("/api/pages")
def get_pages():
    """API endpoint to get all pages"""
    timestamp = request.args.get('_t')  # Cache-busting parameter
    print(f"🌐 API Request: /api/pages?_t={timestamp} [{datetime.now().strftime('%H:%M:%S')}]")
    
    response_data = {
        "pages": {num: data["name"] for num, data in PAGES.items()},
        "total_pages": len(PAGES),
        "timestamp": int(time.time()),
        "cache_buster": timestamp
    }
    print(f"   📄 Returning {len(PAGES)} pages")
    return jsonify(response_data)

@app.route("/api/status/<website_name>")
def get_website_status(website_name):
    """API endpoint to get status of a specific website"""
    with status_data_lock:
        for status in status_data.values():
            if status['name'].lower() == website_name.lower():
                return jsonify(status)
    
    return jsonify({'error': 'Website not found'}), 404

if __name__ == "__main__":
    print("Initializing website status monitor with pages system...")
    print(f"Total pages: {len(PAGES)}")
    print(f"Total websites: {sum(len(p['websites']) for p in PAGES.values())}")

    # Initial status update
    update_status_data()

    # Start background monitor
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()

    # Get configuration
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "80"))

    print("Starting Flask application...")
    try:
        app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, shutting down...")
    except Exception as e:
        print(f"Error starting application: {e}")
    finally:
        print("Application stopped.")