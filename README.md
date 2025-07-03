# 🌐 Website Status Monitor

A real-time web application that monitors the status of major websites and services, built with Flask and featuring a beautiful, responsive dashboard.

![Website Status Monitor](https://img.shields.io/badge/status-active-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-lightgrey.svg)

## ✨ Features

- **Real-time Monitoring**: Continuously monitors 40 major websites every 60 seconds
- **Parallel Checks**: Uses a thread pool for concurrent status updates
- **Beautiful Dashboard**: Modern, responsive UI with gradient backgrounds and animated cards
- **Status Categories**: Categorizes websites as Operational, Degraded, or Down
- **Response Time Tracking**: Measures and displays response times for each service
- **RESTful API**: JSON endpoints for programmatic access to status data
- **Auto-refresh**: Dashboard automatically updates every 60 seconds
- **Mobile Responsive**: Works perfectly on desktop, tablet, and mobile devices

## 🚀 Monitored Services

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

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/website-status-monitor.git
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

If you have any questions or run into issues, please [open an issue](https://github.com/yourusername/website-status-monitor/issues) on GitHub.

---

Made with ❤️ by [craftybot](https://github.com/yourusername) 
