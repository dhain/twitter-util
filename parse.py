"""Read the Twitter stream from stdin, and parse messages.
"""
import sys
import json
import logging

import util


def parse(f):
    log = logging.getLogger('parse')
    while True:
        data = f.readline()
        if not data:
            break
        data = data.strip()
        if not data:
            continue
        try:
            length = int(data)
        except ValueError:
            log.debug('invalid message length: %r', data)
            continue
        data = f.read(length)
        try:
            obj = json.loads(data)
        except ValueError:
            log.debug('invalid json message: %r', data)
            continue
        yield obj


if __name__ == '__main__':
    util.initialize_logging()
    import pprint
    for data in parse(sys.stdin):
        pprint.pprint(data)
