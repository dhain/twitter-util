import os
import time
import datetime
import logging
import sqlite3
import json


SCHEMA = open(os.path.join(os.path.dirname(__file__), 'db.sql')).read()
MAX_STREAM_FILE_SIZE = 100 * 1024 * 1024 # 100mb


class TweetDb(object):
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.db = sqlite3.connect(
            'db.db', detect_types=sqlite3.PARSE_DECLTYPES)
        if not self.db.execute(
            "select 1 from sqlite_master where type='table' and name='tweet'"
        ).fetchone():
            self.log.debug('new database, creating schema')
            with self.db:
                self.db.executescript(SCHEMA)
        else:
            self.log.debug('opened existing database')
        self.outfile = None

    def _next_outfile(self):
        self.fn = 'stream-%s' % (time.strftime('%Y%m%d-%H%M%S'),)
        self.log.debug('opening new stream file, %r', self.fn)
        self.outfile = open(self.fn, 'a')

    def add(self, obj, data):
        if self.outfile is None or self.outfile.tell() > MAX_STREAM_FILE_SIZE:
            self._next_outfile()
        try:
            timestamp = datetime.datetime.strptime(
                obj['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        except ValueError:
            self.log.warn('invalid timestamp value in tweet: %r', obj['created_at'])
            return False
        offset = self.outfile.tell()
        self.outfile.write(data)
        self.outfile.flush()
        with self.db:
            self.db.execute(
                'insert into tweet (tweet_id, timestamp, name, '
                'screen_name, text, stream_file, stream_offset, '
                'stream_length) values (?, ?, ?, ?, ?, ?, ?, ?)',
                (obj['id'], timestamp, obj['user']['name'],
                 obj['user']['screen_name'], obj['text'], self.fn,
                 offset, len(data))
            )
        return True

    def __getitem__(self, tweet_id):
        cur = self.db.cursor()
        cur.execute('select stream_file, stream_offset, stream_length '
                    'from tweet where tweet_id=?', (tweet_id,))
        try:
            stream_file, stream_offset, stream_length = cur.fetchone()
            with open(stream_file, 'r') as infile:
                infile.seek(stream_offset)
                return json.loads(infile.read(stream_length))
        except (TypeError, IOError, ValueError), err:
            if not isinstance(err, TypeError):
                self.log.exception('error reading tweet')
            raise KeyError(tweet_id)
