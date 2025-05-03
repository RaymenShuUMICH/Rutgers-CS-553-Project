from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import numpy as np
import os
import json
import threading

import random
import time

# TODO connect to actually api
def api_stream():
    return

# Cache to manage storage of json
class Cache:
    def __init__(self, cache_file='cache.json'):
        self.cache_file = cache_file
        self.data = {}
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.data = json.load(f)

    def update_cache(self, new_data):
        self.data.update(new_data)
        self.save_to_storage()

    def save_to_storage(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.data, f)

    def get_cache(self):
        return self.data

def background_processing(cache):
    while True:
    #TODO call api_stream() for new updates, update to cache
    new_data = api_stream()
    cache.update_cache(new_data)
    #sleep?
    return
    

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            message = data.get('message', '')
            print(f"Received message: {message}")
            
            # TODO: process message request from cache data

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

    cache = Cache()
    bg_thread = threading.Thread(target=background_processing, args=(cache), daemon=True)
    bg_thread.start()

    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleHandler)
    print("Server running, http://localhost:8000")
    httpd.serve_forever()
