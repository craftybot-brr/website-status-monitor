# Deployment Instructions

This application includes a shell script to simplify deployment.

## Prerequisites
- Python 3.8+
- `bash`
- Internet access to install Python dependencies

## Steps
1. Clone the repository and move into it:
   ```bash
   git clone https://github.com/craftybot-brr/website-status-monitor.git
   cd website-status-monitor
   ```
2. Make the deployment script executable (only once):
   ```bash
   chmod +x deploy.sh
   ```
3. Run the script:
   ```bash
   ./deploy.sh
   ```
   The script will create a virtual environment, install required packages and start the application using Gunicorn.
4. Access the application in your browser at `http://localhost:8000` or the port specified in the `PORT` environment variable.

## Configuration
- **PORT**: Set this environment variable to change the port (default `8000`). Example:
  ```bash
  PORT=8080 ./deploy.sh
  ```

## Stopping the Service
Use `Ctrl+C` in the terminal running the script to stop the Gunicorn process.
