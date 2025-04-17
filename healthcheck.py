import os
import http.server
import socketserver
import threading
import json
import datetime

# Define port for health check server
# Use a different port than the webhook server to avoid conflicts
HEALTH_PORT = int(os.environ.get("HEALTH_PORT", 8080))

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Check if this is the root path or a specific path
        if self.path == '/' or self.path == '/health':
            # Basic health check
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Gather system information
            health_data = {
                "status": "healthy",
                "timestamp": datetime.datetime.now().isoformat(),
                "environment": {
                    "python_version": os.popen('python --version').read().strip(),
                    "system": os.name,
                    "render": os.environ.get('RENDER', 'false'),
                    "render_url": os.environ.get('RENDER_EXTERNAL_URL', 'not set'),
                    "port": os.environ.get('PORT', '10000'),
                    "health_port": HEALTH_PORT
                },
                "message": "Bot health check endpoint is working"
            }
            
            self.wfile.write(json.dumps(health_data, indent=2).encode())
        elif self.path == '/ping':
            # Simple ping endpoint
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'pong')
        else:
            # Handle other paths with a simple 404
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not found')
        
    def log_message(self, format, *args):
        # Log only errors to avoid cluttering logs
        if args[1] != '200':
            print(f"Health server: {args[0]} - {args[1]}")

def start_health_server():
    with socketserver.TCPServer(("", HEALTH_PORT), HealthCheckHandler) as httpd:
        print(f"Health check server started at port {HEALTH_PORT}")
        print(f"Health check URL: http://localhost:{HEALTH_PORT}/health")
        httpd.serve_forever()

def run_health_server():
    # Start server in a separate thread
    server_thread = threading.Thread(target=start_health_server)
    server_thread.daemon = True  # Daemon thread will shut down with the main program
    server_thread.start()
    print(f"Health check thread started on port {HEALTH_PORT}")

if __name__ == "__main__":
    # For testing the health server directly
    run_health_server()
    
    # Keep main thread alive for testing
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Health check server stopped") 