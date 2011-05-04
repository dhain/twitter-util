"""Read the Twitter stream from stdin, and print irc messages.
"""
import sys
import json
import logging
import time

import util
import tweet_db


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
        yield obj, data


def add_to_db(stream, db):
    for obj, data in stream:
        if 'text' in obj:
            db.add(obj, data)
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
    db = tweet_db.TweetDb()
    stream = parse(sys.stdin)
    stream = add_to_db(stream, db)
    stream = make_irc_messages(stream)
    for msg in stream:
        print msg
        sys.stdout.flush()
