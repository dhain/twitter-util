import sys
import logging


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
