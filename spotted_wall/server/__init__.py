"""
Server application
"""

import shlex
import traceback

# noinspection PyUnresolvedReferences
import readline

from spotted_wall.server.screen import SpottedWallScreenThread
from spotted_wall.server.rpc_server import SpottedRpcMethods, RPCServerThread
from spotted_wall.server.utils import Colors, lazy_property, \
    SeekableIterator, Counter


class Application(object):
    def __init__(
            self,
            bind_addresses,

            ## Configuration for the screen
            initial_size=(1280, 1024),
            fullscreen=False,
            show_fps=True,
            show_clock=True,
            rpc_server_address=None,
            enable_web_ui=False,
            web_ui_address=None,
            messages_font_size=None):

        self.running = False

        ## Initialize the threads
        self.thread_screen = SpottedWallScreenThread(self)
        self.thread_rpc = RPCServerThread(self, bind_addresses)

    def run(self):
        ## Fire the threads!
        self.thread_screen.start()
        self.thread_rpc.start()

        ## Commands listening loop
        self.running = True
        while self.running:
            # noinspection PyBroadException
            try:
                self._process_command()

            except KeyboardInterrupt:
                print "^C"

            except:
                ## Anything else, just print
                traceback.print_exc()
                continue

    @property
    def screen(self):
        return self.thread_screen.screen

    @property
    def rpc(self):
        return self.thread_rpc.rpc_server

    def _process_command(self):
        raw = raw_input('spotted-wall> ')
        if not raw.split():
            return  # blank command
        args = shlex.split(raw)
        command, args = args[0], args[1:]

        if command == 'quit':
            ## todo: we should tell threads to terminate..
            self.running = False

        elif command == 'help':
            print "Commands help:"
            print "    help"
            print "    quit"
            print "    msg <message>"

        elif command == 'msg':
            self.screen.add_message(args[0])

        else:
            raise ValueError("Command not found")



# class WebUIThread(threading.Thread):
#     """Thread to expose a Flask-powered Web UI"""
#
#     daemon = True
#     parent = None
#     address = None
#
#     def run(self):
#         app = self.parent
#         from spotted_wall.server.webapp import app as webapp
#         self.webapp = webapp
#         webapp.spotted_wall = app
#         host, port = self.address.split(':')
#         webapp.run(host=host, port=int(port))


