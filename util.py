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


def slice_to_limit(limit_slice):
    if isinstance(limit_slice, (int, long)):
        limit_slice = slice(limit_slice)
    if limit_slice.step is not None:
        raise TypeError('step is not supported')
    if (
        (limit_slice.stop is not None and limit_slice.stop < 0) or
        (limit_slice.start is not None and limit_slice.start < 0)
    ):
        raise NotImplementedError('negative slice values not supported')
    if (
        (limit_slice.stop is not None and
         not isinstance(limit_slice.stop, (int, long))) or
        (limit_slice.start is not None and
         not isinstance(limit_slice.start, (int, long)))
    ):
        raise TypeError('slice values must be numbers')
    if (
        limit_slice.start is not None and
        limit_slice.stop is not None and
        limit_slice.stop < limit_slice.start
    ):
        raise ValueError('stop must be greater than start')
    offset = limit_slice.start
    limit = (None if limit_slice.stop is None else (
        limit_slice.stop if limit_slice.start is None
        else limit_slice.stop - limit_slice.start))
    if offset is None and limit is None:
        return ''
    if offset is None:
        return 'limit %d' % (limit,)
    if limit is None:
        return 'limit %d, -1' % (offset,)
    return 'limit %d, %d' % (offset, limit)
