- # 🌐 Website Status Monitor

A real-time web application that monitors the status of major websites and services, built with Flask and featuring a beautiful, responsive dashboard.

![Website Status Monitor](https://img.shields.io/badge/status-active-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-lightgrey.svg)

## ✨ Features

- **Real-time Monitoring**: Continuously monitors 40 major websites every 60 seconds
- **Azure Speed Test**: A dashboard to monitor Azure storage endpoints across different regions.
- **Parallel Checks**: Uses a thread pool for concurrent status updates
- **Beautiful Dashboard**: Modern, responsive UI with gradient backgrounds and animated cards
- **Status Categories**: Categorizes websites as Operational, Degraded, or Down
- **Response Time Tracking**: Measures and displays response times for each service
- **RESTful API**: JSON endpoints for programmatic access to status data
- **Auto-refresh**: Dashboard automatically updates every 60 seconds
- **Mobile Responsive**: Works perfectly on desktop, tablet, and mobile devices
- **Cloudflare Compatible**: Optimized to work with Cloudflare caching and CDN
- **Cache-busting**: Advanced cache control for real-time data updates
- **Force Refresh**: Manual cache bypass for immediate fresh data
- **Historical Logging**: Stores every check in a SQLite database with history
  and uptime stats

## 🚀 Monitored Services

### Major Websites
- 🔍 **Google** - Search engine
- 📺 **YouTube** - Video platform
- 👥 **Facebook** - Social network
- 🐦 **Twitter/X** - Microblogging platform
- 📸 **Instagram** - Photo sharing
- 💼 **LinkedIn** - Professional network
- 🐱 **GitHub** - Code repository
- 🎮 **Discord** - Communication platform
- 🎬 **Netflix** - Streaming service
- 📦 **Amazon** - E-commerce platform

### Cloud Services
- **Azure Speed Test**: Monitors Azure storage endpoints across various regions.

## 🛠️ Installation

### Quick Installation (Recommended)

**One-line install** - Downloads, sets up, and runs the monitor automatically:

```bash
curl -fsSL https://raw.githubusercontent.com/craftybot-brr/website-status-monitor/main/quick-install.sh | bash
```

Or with wget:
```bash
wget -qO- https://raw.githubusercontent.com/craftybot-brr/website-status-monitor/main/quick-install.sh | bash
```

This will:
- Download the latest version
- Set up Python virtual environment
- Install all dependencies
- Create management scripts (`start.sh`, `stop.sh`, `status.sh`)
- Run the service in a screen session

### Manual Installation

1. **Download the installer**:
   ```bash
   wget https://raw.githubusercontent.com/craftybot-brr/website-status-monitor/main/install.sh
   chmod +x install.sh
   ./install.sh
   ```

2. **Or clone the repository**:
   ```bash
   git clone https://github.com/craftybot-brr/website-status-monitor.git
   cd website-status-monitor
   ```

2. **Run the setup script (Debian/Ubuntu)**:
   ```bash
   ./setup.sh
   ```

3. **Create a virtual environment manually** (optional):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   # Optional: set PORT and FLASK_DEBUG before running
   PORT=8080 FLASK_DEBUG=0 python app.py
   ```

6. **Access the dashboard**:
   Open your browser and navigate to `http://localhost`

## API Endpoints

- `/api/status`: Get the status of all monitored websites.
- `/api/azure/status`: Get the status of all monitored Azure endpoints.

## 🎮 Service Management

After installation with the automated scripts, you can manage the service with:

```bash
# Start the service (runs in background screen session)
./start.sh

# Check service status
./status.sh

# Stop the service
./stop.sh

# View live logs (attach to screen session)
screen -r status-monitor

# Detach from screen session (leave it running)
# Press: Ctrl+A, then D
```

### Access Points

- **Main Dashboard**: http://localhost
- **EC2 Monitor**: http://localhost/ec2
- **API Endpoints**: http://localhost/api/status

### Environment Variables

- `PORT`: Service port (default: 80)
- `FLASK_DEBUG`: Debug mode (default: 0)

Example:
```bash
PORT=8080 ./start.sh
```

## 📡 API Endpoints

### Get All Website Status
```
GET /api/status
```

Returns comprehensive status information for all monitored websites.

**Response Example**:
```json
{
  "websites": [...],
  "last_update": "2025-07-02 19:33:59",
  "total_websites": 40,
  "operational_count": 9,
  "degraded_count": 1,
  "down_count": 0
}
```

### Get Individual Website Status
```
GET /api/status/<website_name>
```

Returns status information for a specific website.

**Example**: `/api/status/Google`

### Get Website History
```
GET /api/history/<website_name>
```

Returns recent status entries for a website. Use the `limit` query parameter to
control how many records are returned (default `50`).

### Get Website Uptime
```
GET /api/uptime/<website_name>
```

Returns uptime statistics for a website based on stored history.

## 🏗️ Project Structure

```
website-status-monitor/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Dashboard HTML template
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```

## 🔧 Configuration

The application can be configured by modifying the `PAGES` dictionary in `app.py`:

```python
PAGES = {
    1: {
        'name': 'My Page',
        'websites': [
            {
                'name': 'Your Website',
                'url': 'https://your-website.com',
                'icon': '🌟'
            },
            # Add more websites here...
        ]
    },
    # Add more pages here...
}
```

The application reads two optional environment variables:

- `PORT` - Port number for the Flask server (default `8080`)
- `FLASK_DEBUG` - Set to `1` to enable debug mode

## 🎨 Customization

### Adding New Websites

To monitor additional websites, add them under a page inside the `PAGES` dictionary:

```python
PAGES[1]['websites'].append({
    'name': 'New Service',
    'url': 'https://new-service.com',
    'icon': '🆕'
})
```

### Changing Update Intervals

Modify the sleep time in the `background_monitor()` function:

```python
time.sleep(60)  # Update every 60 seconds
```

### Customizing Status Thresholds

Adjust the response time thresholds in the `check_website_status()` function:

```python
elif response_time > 5000:  # 5 seconds for 'down'
    status['status'] = 'degraded'
elif response_time > 2000:  # 2 seconds for 'degraded'
    status['status'] = 'degraded'
```

## 🚀 Deployment

### Production Deployment

For production use, consider using a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:80 app:app
```

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 80
CMD ["python", "app.py"]
```

### Cloudflare Deployment

This application is optimized for Cloudflare. For optimal performance:

1. **Configure Page Rules** (see `CLOUDFLARE_CONFIG.md` for details):
   - `/api/*` → Cache Level: Bypass
   - `/*.js`, `/*.css` → Cache Level: Standard (1 hour)
   - `/` → Cache Level: Standard (30 seconds)

2. **Monitor Cache Status**:
   - Check developer tools for `CF-Cache-Status: BYPASS` on API calls
   - Use the "Force Refresh" link in the web UI to bypass all caches
   - Data age is displayed at the bottom of the page

3. **Troubleshooting**:
   - If data seems stale, click "Force Refresh"
   - Check Cloudflare Page Rules configuration
   - Verify API endpoints return `CF-Cache-Status: BYPASS`

**Quick Cloudflare Setup:**
```bash
# Check if API caching is properly bypassed
curl -I https://yourdomain.com/api/status
# Should show: CF-Cache-Status: BYPASS
```

For detailed Cloudflare configuration, see [`CLOUDFLARE_CONFIG.md`](CLOUDFLARE_CONFIG.md).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) - The lightweight WSGI web application framework
- Icons provided by Unicode emoji
- Styling inspired by modern web design principles

## 📞 Support

If you have any questions or run into issues, please [open an issue](https://github.com/craftybot-brr/website-status-monitor/issues) on GitHub.

---

Made with ❤️ by [craftybot](https://github.com/craftybot-brr)
