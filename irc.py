"""Read messages from stdin and relay to irc.
"""
import sys
import logging
import socket
import ssl
import time
import argparse
import threading
from collections import deque
from contextlib import nested

import util


_TIMEOUT = 240 # 4 min
_RECONNECT_WAIT = 5


class ConnectionManager(object):
    def __init__(self, host, port, nick, ident, realname, password=None, channels=()):
        self.log = logging.getLogger(self.__class__.__name__)
        self.host = host
        self.port = port
        self.nick = nick
        self.ident = ident
        self.realname = realname
        self.password = password
        self.channels = set(channels)
        self.sock = None
        self.recv_obj = None
        self.buf = ''
        self.lines = deque()
        self._recv_lock = threading.RLock()
        self._send_lock = threading.RLock()

    def handle_ping(self, msg):
        if msg[0] != 'PING':
            return
        self.log.debug('ping')
        self.send(['PONG', msg[1]])
        self.log.debug('pong')

    def _recv_with_error_handling(self):
        while True:
            try:
                data = self.recv_obj.recv(1024, timeout=_TIMEOUT)
            except util.RecvInterrupted, err:
                if err.args[0] == 'x':
                    return ''
                self.log.warn('receive timed out, reconnecting')
                self.connect()
            except (socket.error, socket.timeout, ssl.SSLError), err:
                self.log.warn('receive error, reconnecting (error was %r)', err)
                self.connect()
            else:
                return data

    def __iter__(self):
        return self

    def next(self):
        if self.sock is None:
            raise StopIteration()
        try:
            line = self.lines.popleft()
        except IndexError:
            with self._recv_lock:
                while not self.lines:
                    data = self._recv_with_error_handling()
                    if not data:
                        raise StopIteration()
                    self.buf += data
                    self.lines.extend(self.buf.split('\r\n'))
                    self.buf = self.lines.pop()
            line = self.lines.popleft()
        msg = line.strip().split()
        for i, token in enumerate(msg):
            if token.startswith(':'):
                if i == 0:
                    continue
                msg = msg[:i] + [' '.join([token[1:]] + msg[i+1:])]
                break
        self.handle_ping(msg)
        return msg

    def send(self, msg):
        if self.sock is None:
            raise StopIteration()
        for i, token in enumerate(msg):
            if token.startswith(':'):
                break
            if ' ' in token:
                msg[i] = ':' + token
                break
        data = ' '.join(msg) + '\r\n'
        with self._send_lock:
            self.sock.sendall(data)

    def join(self, channel):
        self.log.debug('joining %s', channel)
        self.channels.add(channel)
        self.send(['JOIN', channel])

    def connect(self):
        with nested(self._recv_lock, self._send_lock):
            if self.sock is not None:
                self.sock.close()
                self.log.debug('waiting to reconnect')
                time.sleep(_RECONNECT_WAIT)
            self.log.debug('connecting to %s:%d...', self.host, self.port)
            self.buf = ''
            sock = socket.socket()
            sock.connect((self.host, self.port))
            self.log.debug('connected, sending ident')
            self.sock = ssl.wrap_socket(sock)
            self.recv_obj = util.RecvInterrupter(self.sock)
            if self.password is not None:
                self.send(['PASS', ':%s' % (self.password,)])
            self.send(['NICK', self.nick])
            self.send(['USER', self.ident, 'foo', 'bar', ':%s' % (self.realname,)])
            self.log.debug('ident sent')
            for channel in self.channels:
                self.join(channel)

    def shutdown(self):
        self.recv_obj.interrupt('x')
        with nested(self._recv_lock, self._send_lock):
            self.recv_obj = None
            self.sock.close()
            self.sock = None


def print_messages(mgr):
    for msg in mgr:
        print msg


def parse_args(args=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('host', help='server to connect to')
    parser.add_argument('nick', help='irc nickname to use')
    parser.add_argument('channels', nargs='*', help='list of channels to join')
    parser.add_argument('--ident', '-i', help='value to send for ident command')
    parser.add_argument('--realname', '-r', help='value to send for real name (default: same as nick)')
    parser.add_argument('--password', '-p', help='value to send for pass command (default: same as nick)')
    parser.add_argument('--port', type=int, default=6667, help='port to connect to (default: 6667)')
    parser.add_argument('--ssl', '-s', action='store_true', help='use ssl for connection')
    return parser.parse_args(args)


if __name__ == '__main__':
    args = parse_args()
    util.initialize_logging()
    mgr = ConnectionManager(
        args.host,
        args.port,
        args.nick,
        args.ident or args.nick,
        args.realname or args.nick,
        args.password,
        args.channels
    )
    mgr.connect()
    t = threading.Thread(target=print_messages, args=(mgr,))
    t.start()
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            for channel in mgr.channels:
                mgr.send(['PRIVMSG', channel, line])
    finally:
        mgr.shutdown()
        t.join()
