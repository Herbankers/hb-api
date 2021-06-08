# Copyright (C) 2021 Bastiaan Teeuwen <bastiaan@mkcl.nl>
# Hogeschool Rotterdam

from flask   import Flask, request
from hbp     import *
import getopt
import sys

context = ('../ssl/certs/api-chain.crt', '../ssl/private/api.key')
# load CA?

app = Flask(__name__)
hbp = None

def login(data):
    if data == None:
        return ('Json wrong', 432)

    try:
        # check if we know this bank (unfortunately the other group didn't make it... so only INGrid for now)
        if data['header']['receiveBankName'] != 'INGB':
            return ('Account not registered', 433)

        reply = hbp.login('', data['body']['iban'], data['body']['pin'])
    except KeyError:
        return ('Json wrong', 432)

    # check the reply status
    if reply == hbp.HBP_LOGIN_GRANTED:
        return None
    elif reply == hbp.HBP_LOGIN_DENIED:
        return ('Pincode wrong', 435)
    elif reply == hbp.HBP_LOGIN_BLOCKED:
        return ('Account blocked', 434)
    else:
        return ('Account not registered', 433)

# only accept GET requests even though this is technically incorrect
# (bcs data in included in the body, which is not allowed according to the spec)
# should've used my server ;)

# Connection test endpoint
@app.route('/test')
def test():
    return 'Test OK', 200

# Balance query endpoint
@app.route('/balance')
def balance():
    # attempt to login
    login_reply = login(request.get_json())
    if login_reply != None:
        return login_reply

    # retrieve the balance and log out
    balance = hbp.balance()
    hbp.logout()

    return (balance, 208)

# Withdraw money endpoint
@app.route('/withdraw')
def withdraw():
    data = request.get_json()

    # attempt to login
    login_reply = login(data)
    if login_reply != None:
        return login_reply

    try:
        transfer = hbp.transfer('', data['body']['amount'] * 100)
    except KeyError:
        hbp.logout()
        return ('Json wrong', 432)
    hbp.logout()

    if transfer in (hbp.HBP_TRANSFER_SUCCESS, hbp.HBP_TRANSFER_PROCESSING):
        return ('OK', 208)
    elif reply == hbp.HBP_TRANSFER_INSUFFICIENT_FUNDS:
        return ('Balance too low', 437)
    else:
        return ('Account not registered', 433)

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
