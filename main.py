# Copyright (C) 2021 Bastiaan Teeuwen <bastiaan@mkcl.nl>
# Hogeschool Rotterdam

from flask   import Flask
from OpenSSL import SSL
from hbp     import *
import getopt
import sys

context = SSL.Context(SSL.TLSv1_2_METHOD)
context.use_privatekey_file('../ssl/private/api.key')
context.use_certificate_chain_file('../ssl/certs/api-chain.crt')
# load CA?

app = Flask(__name__)
hbp = None

# only accept GET requests even though this is technically incorrect
# (bcs data in included in the body, which is not allowed according to the spec)
# should've used my server ;)

# Connection test endpoint
@app.route('/test')
def test():
    return 'Test OK', 200, { 'Content-Type': 'application/json; charset=utf-8' }

# Balance query endpoint
@app.route('/balance')
def balance():
    return '{ "balance": 10000 }', 200, { 'Content-Type': 'application/json; charset=utf-8' }

# Transfer money endpoint
@app.route('/transfer')
def transfer():
    return 'OK', 200, { 'Content-Type': 'application/json; charset=utf-8' }

# print usage information
def help():
    print('usage: api.py [-?] [-h | --host=] [-p | --port=] [-P | --listening-port=')

def main(argv):
    global hbp

    # parse command line options
    try:
        opts, args = getopt.getopt(argv, '?h:p:P:', [ 'host=', 'port=', 'listening-port=' ])
    except getopt.GetoptError:
        help()
        sys.exit(1)

    host = '145.24.222.242' # HBP server host
    port = 8420             # HBP server port
    hostPort = 8069         # REST API listening port

    for opt, arg in opts:
        if opt == '-?':
            help()
            sys.exit(0)
        elif opt in ('-h', '--host'):
            host = arg
        elif opt in ('-p', '--port'):
            port = arg
        elif opt in ('-P', '--listening-port'):
            hostPort = arg

    print('Copyright (C) 2021 Herbank REST API server v1.0')
    try:
        hbp = HBP(host, port)
    except ConnectionRefusedError:
        print(f'Failed to connect to {host}:{port}')
        exit(1)
    print(f'Connected to Herbank Server @ {host}:{port}')
    print(f'The server is listening on port {hostPort}')

    app.run(host='0.0.0.0', port=hostPort, ssl_context=context)

if __name__ == "__main__":
    main(sys.argv[1:])
