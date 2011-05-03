import os
import sys
import logging
import select


def initialize_logging():
    logging.basicConfig(
        format=u'%(asctime)s %(levelname)-8s %(name)s: %(message)s',
        level=logging.DEBUG,
        stream=sys.stderr,
    )


def consumer(func):
    def start(*args, **kwargs):
        c = func(*args, **kwargs)
        c.next()
        return c
    return start


class RecvInterrupted(Exception):
    pass

class RecvInterrupter(object):
    def __init__(self, fd):
        self.fd = fd
        self._r, self._w = os.pipe()
        self._wp = select.poll()
        self._wp.register(self._w, select.POLLOUT)
        self._rp = select.poll()
        self._rp.register(self.fd, select.POLLIN)
        self._rp.register(self._r, select.POLLIN)

    def recv(self, bufsize, flags=0, timeout=None):
        events = self._rp.poll(timeout * 1000)
        if not events:
            raise RecvInterrupted(None)
        if (self._r, select.POLLIN) in events:
            flag = os.read(self._r, 1)
            raise RecvInterrupted(flag)
        return self.fd.recv(bufsize, flags)

    def interrupt(self, flag=' '):
        self._wp.poll()
        os.write(self._w, flag)
