import http.server
import socketserver
import urllib.request
import urllib.error
import os

PORT = 5000  # The default port for the proxy - using 5000 as required by Replit
TARGET = "http://localhost:5100"

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = TARGET + self.path
        try:
            response = urllib.request.urlopen(url)
            self.send_response(response.status)
            for header, value in response.getheaders():
                if header.lower() != 'transfer-encoding':
                    self.send_header(header, value)
            self.end_headers()
            self.copyfile(response, self.wfile)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for header, value in e.headers.items():
                if header.lower() != 'transfer-encoding':
                    self.send_header(header, value)
            self.end_headers()
            self.copyfile(e, self.wfile)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        url = TARGET + self.path
        
        request = urllib.request.Request(
            url, 
            data=post_data,
            headers={k: v for k, v in self.headers.items() if k.lower() not in ['host', 'content-length']},
            method='POST'
        )
        
        try:
            response = urllib.request.urlopen(request)
            self.send_response(response.status)
            for header, value in response.getheaders():
                if header.lower() != 'transfer-encoding':
                    self.send_header(header, value)
            self.end_headers()
            self.copyfile(response, self.wfile)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for header, value in e.headers.items():
                if header.lower() != 'transfer-encoding':
                    self.send_header(header, value)
            self.end_headers()
            self.copyfile(e, self.wfile)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(e).encode())

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        print(f"Serving proxy at port {PORT}, forwarding to {TARGET}")
        httpd.serve_forever()