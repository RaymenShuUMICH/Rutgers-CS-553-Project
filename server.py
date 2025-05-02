from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import numpy as np
import os
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            message = data.get('message', '')
            print(f"Received message: {message}")
            
            # TODO: process message request using steam api

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'received', 'message': message}).encode('utf-8'))

        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON')

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleHandler)
    print("Server running, http://localhost:8000")
    httpd.serve_forever()
