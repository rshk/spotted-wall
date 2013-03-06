"""
SpottedWall client
"""

## Todo: This should be moved!

import optparse

import zerorpc

parser = optparse.OptionParser()
parser.disable_interspersed_args()
parser.add_option('--address', action='store', dest='address', metavar='ADDR',
                  help="Address of the server we want to connect to.")
parser.add_option('--help-commands', action='store_true', dest='help_commands',
                  help="Show help on the accepted commands")

help_commands = """\
Commands:

add
    Create a new message

list
    List messages on board

update <id>
    Update the selected message (not yet)

delete <id>
    Delete the selected message
"""


def command_add(connection, args):
    parser = optparse.OptionParser()
    parser.add_option('-c', '--color', dest='color', metavar='COLOR',
                      help="Set the message color.")
    parser.add_option('-d', '--duration', dest='duration', metavar='SECONDS',
                      help="Specify for how long the message will be shown"
                           "on the screen.")
    options, args = parser.parse_args(args)

    connection.add_message(args[0],
                           color=options.color,
                           duration=options.duration)


def command_list(connection, args):
    for message in connection.list_messages():
        print message


def command_update(connection, args):
    parser = optparse.OptionParser()
    parser.add_option('-c', '--color', dest='color', metavar='COLOR',
                      help="Set the message color.")
    parser.add_option('-d', '--duration', dest='duration', metavar='SECONDS',
                      help="Specify for how long the message will be shown"
                           "on the screen.")
    options, args = parser.parse_args(args)

    updates = {}

    for key in ('color', 'duration'):
        value = getattr(options, key)
        if value is not None:
            updates[key] = value

    connection.update_message(int(args[0]), updates)


def command_delete(connection, args):
    connection.delete_message(int(args[0]))


if __name__ == '__main__':
    options, args = parser.parse_args()
    address = options.address or 'tcp://127.0.0.1:4242'

    c = zerorpc.Client()
    c.connect(address)

    command = args.pop(0)

    if command == 'add':
        command_add(c, args)

    elif command == 'list':
        command_list(c, args)

    elif command == 'update':
        command_update(c, args)

    elif command == 'delete':
        command_delete(c, args)

    else:
        raise RuntimeError("Unknown command %s" % command)
