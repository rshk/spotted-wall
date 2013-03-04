"""
SpottedWall client
"""

import sys
import zerorpc


if __name__ == '__main__':
    c = zerorpc.Client()
    c.connect("tcp://127.0.0.1:4242")

    command = sys.argv[1]
    if command == 'add_message':
        c.add_message(sys.argv[2])
