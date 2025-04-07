import os
import http.server
import socketserver
import threading

# Define port for health check server
# Use a different port than the webhook server to avoid conflicts
HEALTH_PORT = int(os.environ.get("HEALTH_PORT", 8080))

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is healthy')
        
    def log_message(self, format, *args):
        # Silence logs to avoid cluttering
        pass

def start_health_server():
    with socketserver.TCPServer(("", HEALTH_PORT), HealthCheckHandler) as httpd:
        print(f"Health check server started at port {HEALTH_PORT}")
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