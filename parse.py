"""Read the Twitter stream from stdin, and parse messages.
"""
import sys
import json


def parse(f):
    while True:
        length = int(f.readline())
        message = f.read(length)
        yield json.loads(message)


if __name__ == '__main__':
    import pprint
    for data in parse(sys.stdin):
        pprint.pprint(data)
