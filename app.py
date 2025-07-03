from flask import Flask, render_template, jsonify, request
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import os

app = Flask(__name__)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE="Lax")

# 4 Pages of 10 websites each, organized by category
PAGES = {
    1: {
        'name': 'Search & Social',
        'websites': [
            {'name': 'Google', 'url': 'https://www.google.com', 'icon': '🔍'},
            {'name': 'YouTube', 'url': 'https://www.youtube.com', 'icon': '📺'},
            {'name': 'Facebook', 'url': 'https://www.facebook.com', 'icon': '👥'},
            {'name': 'Instagram', 'url': 'https://www.instagram.com', 'icon': '📸'},
            {'name': 'Twitter/X', 'url': 'https://x.com', 'icon': '🐦'},
            {'name': 'LinkedIn', 'url': 'https://www.linkedin.com', 'icon': '💼'},
            {'name': 'TikTok', 'url': 'https://www.tiktok.com', 'icon': '🎵'},
            {'name': 'Reddit', 'url': 'https://www.reddit.com', 'icon': '🤖'},
            {'name': 'Pinterest', 'url': 'https://www.pinterest.com', 'icon': '📌'},
            {'name': 'Snapchat', 'url': 'https://www.snapchat.com', 'icon': '👻'}
        ]
    },
    2: {
        'name': 'Tech & Development',
        'websites': [
            {'name': 'GitHub', 'url': 'https://github.com', 'icon': '🐱'},
            {'name': 'Stack Overflow', 'url': 'https://stackoverflow.com', 'icon': '📚'},
            {'name': 'Microsoft', 'url': 'https://www.microsoft.com', 'icon': '🪟'},
            {'name': 'Apple', 'url': 'https://www.apple.com', 'icon': '🍎'},
            {'name': 'AWS', 'url': 'https://aws.amazon.com', 'icon': '☁️'},
            {'name': 'Cloudflare', 'url': 'https://www.cloudflare.com', 'icon': '🛡️'},
            {'name': 'Atlassian', 'url': 'https://www.atlassian.com', 'icon': '🔧'},
            {'name': 'Docker', 'url': 'https://www.docker.com', 'icon': '🐳'},
            {'name': 'NPM', 'url': 'https://www.npmjs.com', 'icon': '📦'},
            {'name': 'PyPI', 'url': 'https://pypi.org', 'icon': '🐍'}
        ]
    },
    3: {
        'name': 'Entertainment & Media',
        'websites': [
            {'name': 'Netflix', 'url': 'https://www.netflix.com', 'icon': '🎬'},
            {'name': 'Spotify', 'url': 'https://www.spotify.com', 'icon': '🎧'},
            {'name': 'Disney+', 'url': 'https://www.disneyplus.com', 'icon': '🏰'},
            {'name': 'Twitch', 'url': 'https://www.twitch.tv', 'icon': '🎮'},
            {'name': 'Steam', 'url': 'https://store.steampowered.com', 'icon': '🎯'},
            {'name': 'Epic Games', 'url': 'https://www.epicgames.com', 'icon': '🚀'},
            {'name': 'PlayStation', 'url': 'https://www.playstation.com', 'icon': '🎮'},
            {'name': 'Xbox', 'url': 'https://www.xbox.com', 'icon': '🎮'},
            {'name': 'HBO Max', 'url': 'https://www.hbomax.com', 'icon': '📺'},
            {'name': 'Hulu', 'url': 'https://www.hulu.com', 'icon': '📺'}
        ]
    },
    4: {
        'name': 'E-commerce & Services',
        'websites': [
            {'name': 'Amazon', 'url': 'https://www.amazon.com', 'icon': '📦'},
            {'name': 'eBay', 'url': 'https://www.ebay.com', 'icon': '🛒'},
            {'name': 'PayPal', 'url': 'https://www.paypal.com', 'icon': '💳'},
            {'name': 'Stripe', 'url': 'https://stripe.com', 'icon': '💳'},
            {'name': 'Shopify', 'url': 'https://www.shopify.com', 'icon': '🛍️'},
            {'name': 'Etsy', 'url': 'https://www.etsy.com', 'icon': '🎨'},
            {'name': 'Uber', 'url': 'https://www.uber.com', 'icon': '🚗'},
            {'name': 'Airbnb', 'url': 'https://www.airbnb.com', 'icon': '🏠'},
            {'name': 'DoorDash', 'url': 'https://www.doordash.com', 'icon': '🍕'},
            {'name': 'Zoom', 'url': 'https://zoom.us', 'icon': '📹'}
        ]
    }
}

# Global variable to store status data
status_data = {}
status_data_lock = threading.Lock()

DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

session = requests.Session()
session.headers.update(DEFAULT_HEADERS)

def check_website_status(website):
    """Check the status of a single website with improved accuracy"""
    try:
        start_time = time.time()
        
        response = session.get(
            website['url'],
            timeout=15,  # Increased timeout
            allow_redirects=True  # Allow redirects
        )
        response_time = round((time.time() - start_time) * 1000, 2)
        
        status = {
            'name': website['name'],
            'url': website['url'],
            'icon': website['icon'],
            'status': 'operational',
            'status_code': response.status_code,
            'response_time': response_time,
            'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': 'All systems operational'
        }
        
        # More lenient status determination
        if response.status_code >= 500:
            status['status'] = 'down'
            status['message'] = f'Server error (HTTP {response.status_code})'
        elif response.status_code == 429:
            status['status'] = 'degraded'
            status['message'] = 'Rate limited'
        elif response.status_code >= 400 and response.status_code != 403:
            # 403 is often normal for some sites when accessed programmatically
            status['status'] = 'degraded'
            status['message'] = f'Client error (HTTP {response.status_code})'
        elif response_time > 10000:  # More than 10 seconds
            status['status'] = 'degraded'
            status['message'] = f'Very slow response ({response_time}ms)'
        elif response_time > 5000:  # More than 5 seconds
            status['status'] = 'degraded'
            status['message'] = f'Slow response ({response_time}ms)'
        
        # Special handling for sites that commonly return 403 but are operational
        if response.status_code == 403 and website['name'] in ['Twitter/X', 'Instagram', 'LinkedIn']:
            status['status'] = 'operational'
            status['message'] = 'All systems operational (403 expected)'
            
    except requests.exceptions.Timeout:
        status = {
            'name': website['name'],
            'url': website['url'],
            'icon': website['icon'],
            'status': 'down',
            'status_code': 'Timeout',
            'response_time': None,
            'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': 'Request timeout (>15s)'
        }
    except requests.exceptions.ConnectionError:
        status = {
            'name': website['name'],
            'url': website['url'],
            'icon': website['icon'],
            'status': 'down',
            'status_code': 'Connection Error',
            'response_time': None,
            'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': 'Connection failed'
        }
    except Exception as e:
        status = {
            'name': website['name'],
            'url': website['url'],
            'icon': website['icon'],
            'status': 'unknown',
            'status_code': 'Error',
            'response_time': None,
            'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': f'Unknown error: {str(e)[:50]}'
        }
    
    return status

def update_status_data():
    """Update status data for all websites across all pages"""
    global status_data
    print("Updating status data for all pages...")

    tasks = {}
    new_status_data = {}

    with ThreadPoolExecutor(max_workers=20) as executor:
        for page_num, page_data in PAGES.items():
            page_name = page_data['name']
            print(f"Checking Page {page_num}: {page_name}")

            for website in page_data['websites']:
                future = executor.submit(check_website_status, website)
                tasks[future] = (page_num, page_name, website['name'])

        for future in as_completed(tasks):
            page_num, page_name, _ = tasks[future]
            status = future.result()
            status['page'] = page_num
            status['page_name'] = page_name
            new_status_data[f"{page_num}_{status['name']}"] = status
            print(f"  ✓ {status['name']}: {status['status']}")

    with status_data_lock:
        status_data = new_status_data

def background_monitor():
    """Background thread to continuously monitor websites"""
    while True:
        update_status_data()
        time.sleep(60)  # Update every 60 seconds (less frequent to avoid rate limits)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """API endpoint to get current status of all websites"""
    page = request.args.get('page', type=int)

    if page and page in PAGES:
        # Return specific page
        with status_data_lock:
            page_websites = [status for status in status_data.values() if status.get('page') == page]
        total_websites = len(page_websites)
        operational_count = len([s for s in page_websites if s['status'] == 'operational'])
        degraded_count = len([s for s in page_websites if s['status'] == 'degraded'])
        down_count = len([s for s in page_websites if s['status'] == 'down'])
        
        return jsonify({
            'page': page,
            'page_name': PAGES[page]['name'],
            'websites': page_websites,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_websites': total_websites,
            'operational_count': operational_count,
            'degraded_count': degraded_count,
            'down_count': down_count
        })
    else:
        # Return all websites
        with status_data_lock:
            all_websites = list(status_data.values())
        return jsonify({
            'websites': all_websites,
            'pages': {num: data['name'] for num, data in PAGES.items()},
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_websites': len(all_websites),
            'operational_count': len([s for s in all_websites if s['status'] == 'operational']),
            'degraded_count': len([s for s in all_websites if s['status'] == 'degraded']),
            'down_count': len([s for s in all_websites if s['status'] == 'down'])
        })

@app.route('/api/pages')
def get_pages():
    """API endpoint to get available pages"""
    return jsonify({
        'pages': {num: data['name'] for num, data in PAGES.items()},
        'total_pages': len(PAGES)
    })

@app.route('/api/status/<website_name>')
def get_website_status(website_name):
    """API endpoint to get status of a specific website"""
    # Find website across all pages
    with status_data_lock:
        for status in status_data.values():
            if status['name'].lower() == website_name.lower():
                return jsonify(status)
    
    return jsonify({'error': 'Website not found'}), 404

if __name__ == '__main__':
    # Initialize status data
    print("Initializing website status monitor with pages system...")
    print(f"Total pages: {len(PAGES)}")
    print(
        f"Total websites: {sum(len(page_data['websites']) for page_data in PAGES.values())}"
    )

    update_status_data()

    # Start background monitoring thread
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()

    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    port = int(os.getenv('PORT', '8080'))

    print("Starting Flask application...")
    app.run(debug=debug, host='0.0.0.0', port=port)
