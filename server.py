#  coding: utf-8
import os.path
import socketserver
import re

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


class MyWebServer(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)
        self.data = None
        self.method = None
        self.route = None
        self.is_directory = False
        self.incomplete_path = False
        self.extension = None
        self.mime_type = None
        self.response_code = None
        self.content = None

    def extract_request(self):
        self.data = self.request.recv(1024).strip()

    def extract_method(self):
        m = re.search("([A-Z]+)\s([-a-z/A-Z0-9@:%._\+~#=]+)\sHTTP/1.1", self.data.decode())
        self.method = m.group(1)

    def extract_route(self):
        m = re.search("([A-Z]+)\s([-a-z/A-Z0-9@:%._\+~#=]+)\sHTTP/1.1", self.data.decode())
        self.route = m.group(2)

    def check_is_directory(self):
        if re.fullmatch("[^.]+[.][^.]+", self.route.rstrip("/").split("/")[-1]):
            self.is_directory = False
            self.route = self.route.rstrip("/")
        else:
            self.is_directory = True

    def detect_incomplete_path(self):
        self.incomplete_path = self.is_directory and self.route[-1] != "/"

    def serve_index_files(self):
        if self.is_directory and not self.incomplete_path:
            self.route += "index.html"

    def extract_file_extension(self):
        parts = self.route.split(".")
        self.extension = parts[-1].rstrip("/") if len(parts) > 1 else None

    def extract_mime_type(self):
        mime_types = {"css": "text/css", "html": "text/html", "xml": "text/xml", "csv": "text/csv", "txt": "text/plain",
                      "jpg": "image/jpeg", "png": "image/png", "js": "application/javascript", "pdf": "application/pdf",
                      "json": "application/json", "zip": "application/zip"}
        self.mime_type = mime_types[self.extension] if self.extension in mime_types else None

    def extract_response_code(self):
        if self.method != "GET":
            self.response_code = 405
        elif self.incomplete_path:
            self.response_code = 301
        elif not os.path.isfile("www" + self.route):
            self.response_code = 404
        else:
            self.response_code = 200

    def generate_content(self):
        if self.response_code == 200 and self.extension in ["css", "html", "xml", "csv", "txt", "js", "json"]:
            f = open("www" + self.route)
            self.content = f.read().encode()
            f.close()
        elif self.response_code == 200 and self.extension in ["jpg", "png", "pdf", "zip"]:
            f = open("www" + self.route, mode="rb")
            self.content = f.read()
            f.close()
        else:
            self.content = None

    @staticmethod
    def build_response(code: int, content=None, mime_type=None, **kwargs):
        status_codes = {200: "OK", 301: "Moved Permanently", 400: "Bad Request", 403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed"}
        if content and mime_type:
            return f"HTTP/1.1 {code} {status_codes[code]}\r\nContent-Type: {mime_type}\r\nContent-length: {len(content)}\r\n\r\n".encode() + content
        elif content:
            return f"HTTP/1.1 {code} {status_codes[code]}\r\nContent-length: {len(content)}\r\n\r\n".encode() + content
        elif code == 301 and "location" in kwargs:
            return f"HTTP/1.1 301 {status_codes[301]}\r\nLocation: {kwargs['location']}\r\n\r\n".encode()
        return f"HTTP/1.1 {code} {status_codes[code]}\r\n".encode()

    def handle(self):
        self.extract_request()
        self.extract_method()
        self.extract_route()
        self.check_is_directory()
        self.detect_incomplete_path()
        self.serve_index_files()
        self.extract_file_extension()
        self.extract_mime_type()
        self.extract_response_code()
        self.generate_content()

        if self.response_code == 301:
            self.request.sendall(self.build_response(self.response_code, self.content, self.mime_type, location=self.route+"/"))
        else:
            self.request.sendall(self.build_response(self.response_code, self.content, self.mime_type))


def main():
    host, port = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((host, port), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()


if __name__ == "__main__":
    main()
