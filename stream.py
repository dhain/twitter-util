"""Read from the Twitter Streaming API, streaming data to stdout.

Handles reconnection, backoff, etc.
"""
import os
import sys
import time
import urllib
import urllib2
import logging
import argparse

import util


_API_URL = 'http://stream.twitter.com/1/statuses/%s.json?delimited=length'


def copy_response_to_stream(res, dest):
    # peel back the layers to get a real socket object
    # (urllib.addinfourl, httplib.HTTPResponse, socket._fileobject, etc.)
    f = res.fp
    data = f._rbuf.getvalue()
    if data:
        dest.write(data)
    f = f._sock.fp
    data = f._rbuf.getvalue()
    if data:
        dest.write(data)
    sock = f._sock

    sock.settimeout(1.0)
    has_sent_data = False
    while True:
        try:
            data = sock.recv(4096)
        except urllib2.socket.timeout:
            if has_sent_data:
                has_sent_data = False
                dest.flush()
            continue
        except urllib2.socket.error, err:
            if err.args[0] == urllib2.socket.EINTR:
                continue
        if not data:
            break
        has_sent_data = True
        dest.write(data)


def stream(dest, url, username, password, **params):
    log = logging.getLogger('stream')
    pw_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    pw_mgr.add_password(None, url, username, password)
    handler = urllib2.HTTPBasicAuthHandler(pw_mgr)
    opener = urllib2.build_opener(handler)
    while True:
        log.debug('loop start')
        try:
            res = opener.open(url, urllib.urlencode(params))
            log.debug('request made, starting stream')
            copy_response_to_stream(res, dest)
        except Exception, err:
            if isinstance(err, (urllib2.HTTPError, urllib2.URLError)):
                log.error('stream error: %s', err)
            else:
                log.exception('unexpected error')
            if not (yield err):
                return


def handle_http_error_backoff(stream, min_wait=10, max_wait=240):
    log = logging.getLogger('handle_http_error_backoff')
    cur_wait = min_wait
    error = stream.next()
    while True:
        if isinstance(error, urllib2.HTTPError):
            log.info('sleeping %0.2f sec' % (cur_wait,))
            time.sleep(cur_wait)
            if cur_wait < max_wait:
                cur_wait = min(max_wait, cur_wait * 2)
            error = stream.send(True)
        else:
            cur_wait = min_wait
            error = stream.send((yield error))


def handle_network_error_backoff(stream, min_wait=0.25, max_wait=16):
    log = logging.getLogger('handle_network_error_backoff')
    cur_wait = min_wait
    error = stream.next()
    while True:
        if isinstance(error, (urllib2.URLError, urllib2.socket.error)):
            log.info('sleeping %0.2f sec' % (cur_wait,))
            time.sleep(cur_wait)
            if cur_wait < max_wait:
                cur_wait = min(max_wait, cur_wait + min_wait)
            error = stream.send(True)
        else:
            cur_wait = min_wait
            error = stream.send((yield error))


def parse_args(args=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--track')
    return parser.parse_args(args)


if __name__ == '__main__':
    args = parse_args()
    util.initialize_logging()
    log = logging.getLogger(__name__)

    url = _API_URL % ('filter' if args.track else 'sample',)
    username = os.environ['TWITTER_USER']
    password = os.environ['TWITTER_PASS']
    kwargs = {}
    if args.track:
        kwargs['track'] = args.track

    stream = stream(sys.stdout, url, username, password, **kwargs)
    stream = handle_http_error_backoff(stream)
    stream = handle_network_error_backoff(stream)

    error = stream.next()
    log.error("shouldn't get error here, got %s", error)
    stream.send(False)
