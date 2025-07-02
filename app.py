from flask import Flask, render_template, jsonify
import requests
import time
import threading
from datetime import datetime
import json

app = Flask(__name__)

# List of 10 major websites/services to monitor
WEBSITES = [
    {
        'name': 'Google',
        'url': 'https://www.google.com',
        'icon': '🔍'
    },
    {
        'name': 'YouTube',
        'url': 'https://www.youtube.com',
        'icon': '📺'
    },
    {
        'name': 'Facebook',
        'url': 'https://www.facebook.com',
        'icon': '👥'
    },
    {
        'name': 'Twitter/X',
        'url': 'https://twitter.com',
        'icon': '🐦'
    },
    {
        'name': 'Instagram',
        'url': 'https://www.instagram.com',
        'icon': '📸'
    },
    {
        'name': 'LinkedIn',
        'url': 'https://www.linkedin.com',
        'icon': '💼'
    },
    {
        'name': 'GitHub',
        'url': 'https://github.com',
        'icon': '🐱'
    },
    {
        'name': 'Discord',
        'url': 'https://discord.com',
        'icon': '🎮'
    },
    {
        'name': 'Netflix',
        'url': 'https://www.netflix.com',
        'icon': '🎬'
    },
    {
        'name': 'Amazon',
        'url': 'https://www.amazon.com',
        'icon': '📦'
    }
]

# Global variable to store status data
status_data = {}

def check_website_status(website):
    """Check the status of a single website"""
    try:
        start_time = time.time()
        response = requests.get(
            website['url'], 
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        response_time = round((time.time() - start_time) * 1000, 2)  # Convert to milliseconds
        
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
        
        # Determine status based on response code and time
        if response.status_code >= 500:
            status['status'] = 'down'
            status['message'] = f'Server error (HTTP {response.status_code})'
        elif response.status_code >= 400:
            status['status'] = 'degraded'
            status['message'] = f'Client error (HTTP {response.status_code})'
        elif response_time > 5000:  # More than 5 seconds
            status['status'] = 'degraded'
            status['message'] = f'Slow response ({response_time}ms)'
        elif response_time > 2000:  # More than 2 seconds
            status['status'] = 'degraded'
            status['message'] = f'Slower than usual ({response_time}ms)'
            
    except requests.exceptions.Timeout:
        status = {
            'name': website['name'],
            'url': website['url'],
            'icon': website['icon'],
            'status': 'down',
            'status_code': 'Timeout',
            'response_time': None,
            'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': 'Request timeout'
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
    """Update status data for all websites"""
    global status_data
    print("Updating status data...")
    
    new_status_data = {}
    for website in WEBSITES:
        status = check_website_status(website)
        new_status_data[website['name']] = status
        print(f"✓ {website['name']}: {status['status']}")
    
    status_data = new_status_data

def background_monitor():
    """Background thread to continuously monitor websites"""
    while True:
        update_status_data()
        time.sleep(30)  # Update every 30 seconds

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """API endpoint to get current status of all websites"""
    return jsonify({
        'websites': list(status_data.values()),
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_websites': len(WEBSITES),
        'operational_count': len([s for s in status_data.values() if s['status'] == 'operational']),
        'degraded_count': len([s for s in status_data.values() if s['status'] == 'degraded']),
        'down_count': len([s for s in status_data.values() if s['status'] == 'down'])
    })

@app.route('/api/status/<website_name>')
def get_website_status(website_name):
    """API endpoint to get status of a specific website"""
    if website_name in status_data:
        return jsonify(status_data[website_name])
    else:
        return jsonify({'error': 'Website not found'}), 404

if __name__ == '__main__':
    # Initialize status data
    print("Initializing website status monitor...")
    update_status_data()
    
    # Start background monitoring thread
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    print("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=8080) 