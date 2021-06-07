import msgpack
import serial
import socket
import ssl

class HBP:
    HBP_VERSION                     = 1
    HBP_MAGIC                       = 0x4B9A208E
    HBP_PORT                        = 8420
    HBP_HEADER_LENGTH               = 8

    # Constants
    HBP_ERROR_MAX                   = 10
    HBP_LENGTH_MAX                  = 1024
    HBP_IBAN_MIN                    = 9
    HBP_IBAN_MAX                    = 34
    HBP_PIN_MIN                     = 4
    HBP_PIN_MAX                     = 12
    HBP_PINTRY_MAX                  = 3
    HBP_TIMEOUT                     = (5 * 60)
    HBP_CID_MAX                     = 12

    # Types of requests
    HBP_REQ_LOGIN                   = 0
    HBP_REQ_LOGOUT                  = 1
    HBP_REQ_INFO                    = 2
    HBP_REQ_BALANCE                 = 3
    HBP_REQ_TRANSFER                = 4

    # Types of replies
    HBP_REP_LOGIN                   = 128
    HBP_REP_TERMINATED              = 129
    HBP_REP_INFO                    = 130
    HBP_REP_BALANCE                 = 131
    HBP_REP_TRANSFER                = 132
    HBP_REP_ERROR                   = 133

    # Indicates whether the login failed or succeeded
    HBP_LOGIN_GRANTED               = 0
    HBP_LOGIN_DENIED                = 1
    HBP_LOGIN_BLOCKED               = 2

    # Indicates why the session has ended/the server will disconnect
    HBP_TERM_LOGOUT                 = 0
    HBP_TERM_EXPIRED                = 1
    HBP_TERM_CLOSED                 = 2

    # Result status of a transfer
    HBP_TRANSFER_SUCCESS            = 0
    HBP_TRANSFER_PROCESSING         = 1
    HBP_TRANSFER_INSUFFICIENT_FUNDS = 2

    def __init__(self, host, port):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile='crt/ca.crt')
        context.load_cert_chain(certfile='crt/client.crt', keyfile='crt/client.key')

        plainsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock = context.wrap_socket(plainsock, server_side=False, server_hostname=host)
        self.sock.connect((host, int(port)))

    def _send(self, request_type, data):
        packed = msgpack.packb(data, use_bin_type=True)

        header = bytearray()

        # magic
        # TODO get with masks, too lazy r.n.
        header.append(0x8E)
        header.append(0x20)
        header.append(0x9A)
        header.append(0x4B)

        # version
        header.append(self.HBP_VERSION)

        # type
        header.append(request_type)

        # length
        header.append((len(packed) & 0xFF))
        header.append(((len(packed) >> 8) & 0xFF))

        # send our request
        self.sock.sendall(header)
        self.sock.sendall(packed)

    def _receive(self):
        # wait for the header to arrive
        header = self.sock.recv(self.HBP_HEADER_LENGTH)

        # check if the magic number is correct
        if header[0] != 0x8E or header[1] != 0x20 or header[2] != 0x9A or header[3] != 0x4B:
            print('received invalid HBP magic')
            exit(1)

        # check if we're using a compatible HBP version
        if header[4] != self.HBP_VERSION:
            print('received invalid HBP version')
            exit(1)

        # read the other fields into memory
        reply_type = header[5]
        length = header[6] | header[7] << 8

        # receive the msgpack data
        data = self.sock.recv(length)

        if reply_type == self.HBP_REP_ERROR:
            return (reply_type, 0)
        else:
            return (reply_type, msgpack.unpackb(data, raw=False))

    def replyType(self, reply_type):
        # TODO should put this in a list or something but I was lazy
        if reply_type == self.HBP_REP_LOGIN:
            return 'HBP_REP_LOGIN'
        elif reply_type == self.HBP_REP_TERMINATED:
            return 'HBP_REP_TERMINATED'
        elif reply_type == self.HBP_REP_INFO:
            return 'HBP_REP_INFO'
        elif reply_type == self.HBP_REP_BALANCE:
            return 'HBP_REP_BALANCE'
        elif reply_type == self.HBP_REP_TRANSFER:
            return 'HBP_REP_TRANSFER'
        elif reply_type == self.HBP_REP_ERROR:
            return 'HBP_REP_ERROR'

    def request(self, request_type, data):
        self._send(request_type, data)
        return self._receive()

    # FIXME all these functions below can be written way more compactly, but again, I'm lazy

    def login(self, card_id, iban, pin):
        # send a login request to the server
        request = [card_id, iban, pin]
        reply = self.request(self.HBP_REQ_LOGIN, request)

        # check the server's reply
        reply_type = reply[0]
        if reply_type != self.HBP_REP_LOGIN:
            # return the type of reply that was received instead of the expected one
            return self.replyType(reply_type)

        # return the login status if successful
        return reply[1]

    def logout(self):
        # send a logout request to the server
        request = []
        reply = self.request(self.HBP_REQ_LOGOUT, request)

        # check the server's reply
        reply_type = reply[0]
        if reply_type != self.HBP_REP_TERMINATED:
            # return the type of reply that was received instead of the expected one
            return self.replyType(reply_type)

        # return the logout reason otherwise (which should always be HBP_TERM_LOGOUT)
        return reply[1]

    def info(self):
        # send an info request to the server
        request = []
        reply = self.request(self.HBP_REQ_INFO, request)

        # check the server's reply
        reply_type = reply[0]
        if reply_type != self.HBP_REP_INFO:
            # return the type of reply that was received instead of the expected one
            return self.replyType(reply_type)

        # return the first and last name in an array if successful
        return reply[1]

    def balance(self):
        # send an info request to the server
        request = []
        reply = self.request(self.HBP_REQ_BALANCE, request)

        # check if the server's reply
        reply_type = reply[0]
        if reply_type != self.HBP_REP_BALANCE:
            # return the type of reply that was received instead of the expected one
            return self.replyType(reply_type)

        # return the first and last name in an array if successful
        return reply[1]

    def transfer(self, iban, amount):
        # send a transfer request to the server
        request = [iban, amount]
        reply = self.request(self.HBP_REQ_TRANSFER, request)

        # check if the server's reply
        reply_type = reply[0]
        if reply_type != self.HBP_REP_TRANSFER:
            # return the type of reply that was received instead of the expected one
            return self.replyType(reply_type)

        # return the first and last name in an array if successful
        return reply[1]
