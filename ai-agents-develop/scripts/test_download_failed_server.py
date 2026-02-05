"""
Test server for simulating file download failures.
Run this script and navigate to http://localhost:8080
"""

import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class DownloadTestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            # Serve the main page with download buttons
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Download Test Server</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                    }
                    .button-container {
                        margin: 20px 0;
                    }
                    button {
                        padding: 10px 20px;
                        margin: 5px;
                        font-size: 16px;
                        cursor: pointer;
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 4px;
                    }
                    button:hover {
                        background-color: #45a049;
                    }
                    .danger {
                        background-color: #f44336;
                    }
                    .danger:hover {
                        background-color: #da190b;
                    }
                    .status {
                        margin-top: 20px;
                        padding: 10px;
                        background-color: #f0f0f0;
                        border-radius: 4px;
                    }
                </style>
            </head>
            <body>
                <h1>File Download Test Server</h1>
                <p>Test different download failure scenarios:</p>

                <div class="button-container">
                    <h3>Successful Download:</h3>
                    <button onclick="downloadFile('/download/success')">Download Successfully</button>
                </div>

                <div class="button-container">
                    <h3>Failure Scenarios:</h3>
                    <button class="danger" onclick="downloadFile('/download/404')">404 Not Found</button>
                    <button class="danger" onclick="downloadFile('/download/500')">500 Server Error</button>
                    <button class="danger" onclick="downloadFile('/download/timeout')">Connection Timeout</button>
                    <button class="danger" onclick="downloadFile('/download/incomplete')">Incomplete Download</button>
                    <button class="danger" onclick="downloadFile('/download/disconnect')">Connection Drop Mid-Download</button>
                </div>

                <div class="status" id="status"></div>

                <script>
                    function downloadFile(url) {
                        const status = document.getElementById('status');
                        status.innerHTML = 'Starting download from: ' + url;

                        // Use direct link navigation to trigger browser download
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'test_file.txt';
                        document.body.appendChild(a);
                        a.click();
                        a.remove();

                        // Update status after a delay
                        setTimeout(() => {
                            status.innerHTML = 'Download triggered. Check your browser downloads.';
                        }, 500);
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

        elif self.path == "/download/success":
            # Successful download
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header(
                "Content-Disposition", 'attachment; filename="test_file.txt"'
            )
            content = b"This is a test file. Download succeeded!"
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == "/download/404":
            # File not found
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"File not found")

        elif self.path == "/download/500":
            # Server error
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Internal server error")

        elif self.path == "/download/timeout":
            # Simulate timeout by delaying response
            time.sleep(30)  # 30 second delay
            self.send_response(200)
            self.end_headers()

        elif self.path == "/download/incomplete":
            # Send incomplete content (wrong Content-Length)
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header(
                "Content-Disposition", 'attachment; filename="test_file.txt"'
            )
            self.send_header("Content-Length", "10000")  # Claim 10000 bytes
            self.end_headers()
            self.wfile.write(b"Only a few bytes")  # But only send a few

        elif self.path == "/download/disconnect":
            # Start download then disconnect
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header(
                "Content-Disposition", 'attachment; filename="test_file.txt"'
            )
            self.send_header("Content-Length", "1000000")
            self.end_headers()

            # Send some data then close connection
            for i in range(10):
                self.wfile.write(b"A" * 1000)
                self.wfile.flush()
                time.sleep(0.1)
            # Connection will close without sending all promised data

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Custom logging
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, DownloadTestHandler)
    print(f"Starting test server on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    run_server()
