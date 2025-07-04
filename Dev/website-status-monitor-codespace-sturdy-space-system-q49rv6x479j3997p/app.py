from flask import Flask, render_template, jsonify, request, make_response
import requests
import time
import dns.resolver
import threading
from datetime import datetime
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
from ping3 import ping
import socket
from endpoints import EC2_ENDPOINTS, AZURE_ENDPOINTS

app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), "status_history.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT,
            status TEXT,
            status_code TEXT,
            response_time INTEGER,
            checked_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def store_status(status: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO history (name, url, status, status_code, response_time, checked_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            status.get("name"),
            status.get("url"),
            status.get("status"),
            str(status.get("status_code")),
            status.get("response_time"),
            status.get("last_checked"),
        ),
    )
    conn.commit()
    conn.close()

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

# Global variable to store Azure status data
azure_status_data_lock = threading.Lock()
azure_status_data = {}

# Global variable to store status data with thread safety
status_data_lock = threading.Lock()
status_data = {}

# Global variable to store EC2 status data
ec2_status_data_lock = threading.Lock()
ec2_status_data = {}

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

def check_tcp_connectivity(endpoint):
    """Check the status of an EC2 endpoint using TCP connectivity check"""
    name = endpoint["name"]
    hostname = endpoint["ip"]  # This is actually a hostname now
    icon = endpoint["icon"]
    
    try:
        start_time = time.time()
        
        # Use TCP connectivity check instead of ICMP ping (more reliable for cloud services)
        # Most AWS services listen on port 443 (HTTPS)
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(10)  # 10 second timeout
        
        try:
            # Try to connect to port 443 (HTTPS) - most AWS services support this
            result = test_socket.connect_ex((hostname, 443))
            test_socket.close()
            
            total_time = int((time.time() - start_time) * 1000)  # Total time in ms
            
            status = {
                "name": name,
                "ip": hostname,  # Keep the hostname in the ip field for consistency
                "icon": icon,
                "response_time": total_time,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            if result == 0:
                # Successful connection
                status["connection_time"] = total_time
                
                # Determine status based on connection time
                if total_time > 5000:  # 5 seconds
                    status["status"] = "degraded"
                    status["message"] = f"High latency ({total_time} ms)"
                elif total_time > 2000:  # 2 seconds
                    status["status"] = "degraded"
                    status["message"] = f"Elevated latency ({total_time} ms)"
                else:
                    status["status"] = "operational"
                    status["message"] = f"TCP connection OK ({total_time} ms)"
            else:
                # Connection failed
                status["status"] = "down"
                status["connection_time"] = None
                
                # Try to determine why connection failed
                try:
                    socket.gethostbyname(hostname)
                    status["message"] = f"TCP connection failed (port 443 blocked or service down)"
                except socket.gaierror:
                    status["message"] = "DNS resolution failed"
                    
        except socket.timeout:
            status = {
                "name": name,
                "ip": hostname,
                "icon": icon,
                "status": "down",
                "response_time": 10000,  # Timeout time
                "connection_time": None,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": "TCP connection timeout (10s)",
            }
        except Exception as e:
            status = {
                "name": name,
                "ip": hostname,
                "icon": icon,
                "status": "down",
                "response_time": None,
                "connection_time": None,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"TCP connection error: {str(e)[:30]}",
            }
            
    except Exception as e:
        status = {
            "name": name,
            "ip": hostname,
            "icon": icon,
            "status": "down",
            "response_time": None,
            "ping_time": None,
            "connection_time": None,
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"Error: {str(e)[:50]}",
        }
    
    return status

def check_azure_connectivity(endpoint):
    """Check the status of an Azure endpoint using TCP connectivity check"""
    name = endpoint["name"]
    hostname = endpoint["endpoint"]
    region = endpoint["region"]
    icon = endpoint["icon"]
    
    try:
        start_time = time.time()
        
        # Use TCP connectivity check to Azure Storage endpoints
        # Azure Storage blob service typically uses port 443 (HTTPS)
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(10)  # 10 second timeout
        
        try:
            # Try to connect to port 443 (HTTPS) - Azure Storage blob service
            result = test_socket.connect_ex((hostname, 443))
            test_socket.close()
            
            total_time = int((time.time() - start_time) * 1000)  # Total time in ms
            
            status = {
                "name": name,
                "endpoint": hostname,
                "region": region,
                "icon": icon,
                "response_time": total_time,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            if result == 0:
                # Successful connection
                status["connection_time"] = total_time
                
                # Determine status based on connection time
                if total_time > 5000:  # 5 seconds
                    status["status"] = "degraded"
                    status["message"] = f"High latency ({total_time} ms)"
                elif total_time > 2000:  # 2 seconds
                    status["status"] = "degraded"
                    status["message"] = f"Elevated latency ({total_time} ms)"
                else:
                    status["status"] = "operational"
                    status["message"] = f"TCP connection OK ({total_time} ms)"
            else:
                # Connection failed
                status["status"] = "down"
                status["connection_time"] = None
                
                # Try to determine why connection failed
                try:
                    socket.gethostbyname(hostname)
                    status["message"] = f"TCP connection failed (port 443 blocked or service down)"
                except socket.gaierror:
                    status["message"] = "DNS resolution failed"
                    
        except socket.timeout:
            status = {
                "name": name,
                "endpoint": hostname,
                "region": region,
                "icon": icon,
                "status": "down",
                "response_time": 10000,  # Timeout time
                "connection_time": None,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": "TCP connection timeout (10s)",
            }
        except Exception as e:
            status = {
                "name": name,
                "endpoint": hostname,
                "region": region,
                "icon": icon,
                "status": "down",
                "response_time": None,
                "connection_time": None,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"TCP connection error: {str(e)[:30]}",
            }
            
    except Exception as e:
        status = {
            "name": name,
            "endpoint": hostname,
            "region": region,
            "icon": icon,
            "status": "down",
            "response_time": None,
            "ping_time": None,
            "connection_time": None,
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"Error: {str(e)[:50]}",
        }
    
    return status

def update_azure_status_data():
    """Update status data for all Azure endpoints using parallel processing."""
    global azure_status_data
    start_time = time.time()
    print(f"\n🔄 Updating Azure status data... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    
    new_status_data = {}
    tasks = {}
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Flatten the list of endpoints to check
        all_endpoints = [endpoint for region in AZURE_ENDPOINTS.values() for endpoint in region["endpoints"]]
        
        # Submit all tasks
        for endpoint in all_endpoints:
            future = executor.submit(check_azure_connectivity, endpoint)
            tasks[future] = endpoint["name"]
            
        # Collect results as they complete
        for future in as_completed(tasks):
            endpoint_name = tasks[future]
            try:
                result = future.result()
                new_status_data[endpoint_name] = result
            except Exception as e:
                print(f"   - Error checking {endpoint_name}: {e}")

    # Thread-safe update
    with azure_status_data_lock:
        azure_status_data = new_status_data
    
    update_duration = time.time() - start_time
    total_endpoints = len(new_status_data)
    operational_count = len([s for s in new_status_data.values() if s['status'] == 'operational'])
    degraded_count = len([s for s in new_status_data.values() if s['status'] == 'degraded'])
    down_count = len([s for s in new_status_data.values() if s['status'] == 'down'])
    
    print(f"📊 Azure update complete: {total_endpoints} endpoints checked in {update_duration:.2f}s")
    print(f"   Status: {operational_count} operational, {degraded_count} degraded, {down_count} down")

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
                store_status(status)
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

def update_ec2_status_data():
    """Update status data for all EC2 endpoints using parallel processing."""
    global ec2_status_data
    start_time = time.time()
    print(f"\n🔄 Updating EC2 status data... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    
    new_ec2_status_data = {}
    tasks = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        for env_name, env_data in EC2_ENDPOINTS.items():
            env_display_name = env_data['name']
            print(f"Checking {env_display_name}")
            
            for endpoint in env_data['endpoints']:
                future = executor.submit(check_tcp_connectivity, endpoint)
                tasks[future] = (env_name, env_display_name, endpoint['name'])
        
        # Collect results
        for future in as_completed(tasks):
            env_name, env_display_name, endpoint_name = tasks[future]
            try:
                status = future.result()
                status['environment'] = env_name
                status['environment_name'] = env_display_name
                new_ec2_status_data[f"{env_name}_{endpoint_name}"] = status
                print(f"  ✓ {endpoint_name}: {status['status']}")
            except Exception as e:
                print(f"  ✗ {endpoint_name}: Error - {str(e)}")

    # Thread-safe update
    with ec2_status_data_lock:
        ec2_status_data = new_ec2_status_data
    
    update_duration = time.time() - start_time
    total_endpoints = len(new_ec2_status_data)
    operational_count = len([s for s in new_ec2_status_data.values() if s['status'] == 'operational'])
    degraded_count = len([s for s in new_ec2_status_data.values() if s['status'] == 'degraded'])
    down_count = len([s for s in new_ec2_status_data.values() if s['status'] == 'down'])
    
    print(f"📊 EC2 Update complete: {total_endpoints} endpoints checked in {update_duration:.2f}s")
    print(f"   Status: {operational_count} operational, {degraded_count} degraded, {down_count} down")
    print(f"   Next update in 60 seconds\n")

# --- Routes ---

@app.route("/")
def index():
    page_num = request.args.get("page", 1, type=int)
    return render_template("index.html", pages=PAGES, current_page=page_num)

@app.route("/ec2")
def ec2_status():
    """Render the EC2 status page"""
    return render_template("ec2.html", regions=EC2_ENDPOINTS)

@app.route("/azure")
def azure_status():
    """Render the Azure status page"""
    return render_template("azure.html", regions=AZURE_ENDPOINTS)

@app.route("/api/status")
def api_status():
    """Return the current status data as JSON"""
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


@app.route("/api/history/<website_name>")
def get_history(website_name):
    """Return recent status history for a website"""
    limit = request.args.get('limit', 50, type=int)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT status, status_code, response_time, checked_at FROM history WHERE name=? ORDER BY id DESC LIMIT ?",
        (website_name, limit),
    )
    rows = c.fetchall()
    conn.close()
    history = [
        {
            "status": r[0],
            "status_code": r[1],
            "response_time": r[2],
            "checked_at": r[3],
        }
        for r in rows
    ]
    return jsonify({"name": website_name, "history": history, "count": len(history)})


@app.route("/api/uptime/<website_name>")
def get_uptime(website_name):
    """Return uptime percentage for a website"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM history WHERE name=?", (website_name,))
    total = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(*) FROM history WHERE name=? AND status='operational'",
        (website_name,),
    )
    operational = c.fetchone()[0]
    conn.close()
    uptime = round((operational / total * 100), 2) if total else None
    return jsonify(
        {
            "name": website_name,
            "total_checks": total,
            "operational_checks": operational,
            "uptime_percentage": uptime,
        }
    )

@app.route("/api/ec2/status", methods=["GET"])
def get_ec2_status():
    """API endpoint to get current status of all EC2 endpoints or a specific environment"""
    environment = request.args.get('env')
    timestamp = request.args.get('_t')  # Cache-busting parameter
    force_id = request.args.get('force')  # Force refresh parameter
    
    # Determine if this is a force refresh request
    is_force_refresh = bool(force_id or request.args.get('bypass') or request.args.get('fresh'))
    
    if is_force_refresh:
        print(f"🚀 FORCE REFRESH EC2 API Request: /api/ec2/status [{datetime.now().strftime('%H:%M:%S')}]")
        print(f"   Force ID: {force_id}")
        # Trigger immediate status update for force refresh
        update_ec2_status_data()
    else:
        print(f"🌐 EC2 API Request: /api/ec2/status?env={environment}&_t={timestamp} [{datetime.now().strftime('%H:%M:%S')}]")
    
    with ec2_status_data_lock:
        # Get cache status from request headers (set by Cloudflare)
        cf_cache_status = request.headers.get('CF-Cache-Status', 'UNKNOWN')
        cf_ray = request.headers.get('CF-RAY', 'UNKNOWN')
        
        # Common response data
        current_timestamp = int(time.time())
        last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if environment and environment in EC2_ENDPOINTS:
            # Return specific environment
            env_endpoints = [status for key, status in ec2_status_data.items() if status.get('environment') == environment]
            total_endpoints = len(env_endpoints)
            operational_count = len([s for s in env_endpoints if s["status"] == "operational"])
            degraded_count = len([s for s in env_endpoints if s["status"] == "degraded"])
            down_count = len([s for s in env_endpoints if s["status"] == "down"])

            response_data = {
                "environment": environment,
                "environment_name": EC2_ENDPOINTS[environment]["name"],
                "endpoints": env_endpoints,
                "last_update": last_update_time,
                "total_endpoints": total_endpoints,
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
            print(f"   📄 Returning environment {environment} data: {total_endpoints} endpoints (CF: {cf_cache_status})")
            return jsonify(response_data)
        else:
            # Return all endpoints
            all_endpoints = list(ec2_status_data.values())
            response_data = {
                'endpoints': all_endpoints,
                'environments': {env: data['name'] for env, data in EC2_ENDPOINTS.items()},
                'last_update': last_update_time,
                'total_endpoints': len(all_endpoints),
                'operational_count': len([s for s in all_endpoints if s['status'] == 'operational']),
                'degraded_count': len([s for s in all_endpoints if s['status'] == 'degraded']),
                'down_count': len([s for s in all_endpoints if s['status'] == 'down']),
                'timestamp': current_timestamp,
                'cache_buster': timestamp,
                'force_refresh': is_force_refresh,
                'cf_cache_status': cf_cache_status,
                'cf_ray': cf_ray,
                'data_freshness': "real-time" if is_force_refresh else "cached"
            }
            print(f"   📄 Returning all EC2 data: {len(all_endpoints)} endpoints across {len(EC2_ENDPOINTS)} environments (CF: {cf_cache_status})")
            return jsonify(response_data)

@app.route("/api/azure/status")
def api_azure_status():
    """Return the current Azure status data as JSON"""
    with azure_status_data_lock:
        return jsonify(azure_status_data)

@app.route("/history")
def history():
    """Display historical status data"""
    return render_template("history.html")

@app.route("/api/history")
def api_history():
    """API endpoint to get historical status data"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    website_name = request.args.get('website')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if website_name:
        c.execute(
            "SELECT status, status_code, response_time, checked_at FROM history WHERE name=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (website_name, limit, offset),
        )
    else:
        c.execute(
            "SELECT name, url, status, status_code, response_time, checked_at FROM history ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
    
    rows = c.fetchall()
    conn.close()
    
    # Format the results
    if website_name:
        history = [
            {
                "status": r[0],
                "status_code": r[1],
                "response_time": r[2],
                "checked_at": r[3],
            }
            for r in rows
        ]
        response_data = {"name": website_name, "history": history, "count": len(history)}
    else:
        history = [
            {
                "name": r[0],
                "url": r[1],
                "status": r[2],
                "status_code": r[3],
                "response_time": r[4],
                "checked_at": r[5],
            }
            for r in rows
        ]
        response_data = {"history": history, "count": len(history)}
    
    return jsonify(response_data)

def run_scheduler(update_function, interval):
    """Run a function periodically with a fixed interval"""
    while True:
        try:
            update_function()
        except Exception as e:
            print(f"Error in scheduler: {e}")
        time.sleep(interval)

# Start the background threads to update data
if __name__ == "__main__":
    init_db()  # Ensure the database is initialized
    
    # Start the website status update thread
    status_thread = threading.Thread(target=run_scheduler, args=(update_status_data, 60))
    status_thread.daemon = True
    status_thread.start()
    
    # Start the EC2 status update thread
    ec2_thread = threading.Thread(target=run_scheduler, args=(update_ec2_status_data, 120))
    ec2_thread.daemon = True
    ec2_thread.start()

    # Start the Azure status update thread
    azure_thread = threading.Thread(target=run_scheduler, args=(update_azure_status_data, 120))
    azure_thread.daemon = True
    azure_thread.start()

    # Run the Flask app
    app.run(host="0.0.0.0", port=80)
