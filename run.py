import logging

from wsgiref import simple_server

from chromarestserver import app

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    httpd = simple_server.make_server('127.0.0.1', 54235, app)
    httpd.serve_forever()
