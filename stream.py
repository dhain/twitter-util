"""Read from the Twitter Streaming API, streaming data to stdout.

Handles reconnection, backoff, etc.
"""
import os
import sys
import time
import urllib
import urllib2
import shutil
import logging


def stream(dest, url, username, password, **params):
    log = logging.getLogger('stream')
    pw_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    pw_mgr.add_password(None, url, username, password)
    handler = urllib2.HTTPBasicAuthHandler(pw_mgr)
    opener = urllib2.build_opener(handler)
    while True:
        try:
            res = opener.open(url, urllib.urlencode(params))
            shutil.copyfileobj(res, dest)
        except Exception, err:
            log.exception('error in stream')
            if (yield err):
                continue
            raise


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


if __name__ == '__main__':
    username = os.environ['TWITTER_USER']
    password = os.environ['TWITTER_PASS']
    stream_type = 'sample'
    stream = stream(
        sys.stdout,
        'http://stream.twitter.com/1/statuses/%s.json?delimited=length' % (stream_type,),
        username, password,
    )
    stream = handle_http_error_backoff(stream)
    stream = handle_network_error_backoff(stream)

    error = stream.next()
    print >>sys.stderr, "shouldn't get error here, got %s" % (error,)
    stream.send(False)
