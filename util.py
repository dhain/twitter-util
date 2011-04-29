import sys
import logging


def initialize_logging():
    logging.basicConfig(
        format=u'%(asctime)s %(levelname)-8s %(name)s: %(message)s',
        level=logging.DEBUG,
        stream=sys.stderr,
    )
