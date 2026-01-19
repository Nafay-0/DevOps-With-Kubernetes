#!/usr/bin/env python3
"""
Greeter Service
Simple HTTP service that responds with a greeting message
"""

import os
from http.server import HTTPServer, BaseHTTPRequestHandler


class GreeterHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/greet":
            # Get greeting message from environment variable or use default
            greeting = os.getenv("GREETING", "Hello from version 1")
            
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(greeting.encode())
        elif self.path == "/healthz":
            # Health check endpoint
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP request logging
        pass


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    print(f"Greeter server started on port {port}")
    server = HTTPServer(("0.0.0.0", port), GreeterHandler)
    server.serve_forever()

