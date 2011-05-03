Twitter Util
============

These are some Python scripts useful for relaying Twitter messages to IRC (and
in the future, do other fun things with it).


stream.py
---------

Connect to Twitter Streaming API and spit it back out on stdout. This handles
reconnecting, backoff, etc.

    $ python stream.py --help
    usage: stream.py [-h] --username USERNAME --password PASSWORD [track]

    Read from the Twitter Streaming API, streaming data to stdout.

    positional arguments:
      track                 keywords to track (optional, uses sample stream if
                            omitted)

    optional arguments:
      -h, --help            show this help message and exit
      --username USERNAME, -u USERNAME
                            twitter api username (required)
      --password PASSWORD, -p PASSWORD
                            twitter api password (required)


parse.py
--------

Convert raw Twitter data into IRC messages of the form: `username: tweet text`

    $ python parse.py


irc.py
------

Connect to an IRC server and relay input (from stdin) to a list of channels (one line per message). Answers PING messages, handles reconnects, autojoins, etc.

TODO:

- rate limiting


    $ python irc.py --help
    usage: irc.py [-h] [--ident IDENT] [--realname REALNAME] [--password PASSWORD]
                  [--port PORT] [--ssl]
                  host nick [channels [channels ...]]

    Read messages from stdin and relay to irc.

    positional arguments:
      host                  server to connect to
      nick                  irc nickname to use
      channels              list of channels to join

    optional arguments:
      -h, --help            show this help message and exit
      --ident IDENT, -i IDENT
                            value to send for ident command
      --realname REALNAME, -r REALNAME
                            value to send for real name (default: same as nick)
      --password PASSWORD, -p PASSWORD
                            value to send for pass command (default: same as nick)
      --port PORT           port to connect to (default: 6667)
      --ssl, -s             use ssl for connection
