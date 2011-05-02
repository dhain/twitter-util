"""Read the Twitter stream from stdin, and print irc messages.
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


def make_irc_messages(stream):
    log = logging.getLogger('make_irc_messages')
    for obj in stream:
        if 'text' in obj:
            try:
                yield (u'%s: %s' % (
                    obj['user']['screen_name'],
                    obj['text'],
                )).replace('\n', ' ').encode('utf-8')
            except Exception:
                log.traceback('error making message')


if __name__ == '__main__':
    util.initialize_logging()
    stream = parse(sys.stdin)
    stream = make_irc_messages(stream)
    for msg in stream:
        print msg
