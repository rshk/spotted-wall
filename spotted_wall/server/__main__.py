"""
Launch the server
"""

import optparse

from . import Application

parser = optparse.OptionParser()
# parser.add_option('--debug', action='store_true', dest='debug')
parser.add_option('--fullscreen', action='store_true', dest='start_fullscreen', default=False)
parser.add_option('--no-fullscreen', action='store_false', dest='start_fullscreen')
parser.add_option('--resolution', action='store', dest='resolution')
parser.add_option('--list-resolutions', action='store_true', dest='list_resolutions', default=False)
parser.add_option('--rpc-address', action='store', dest='rpc_listen_address')

parser.add_option('--enable-fps', action='store_true', dest='enable_fps', default=False)
parser.add_option('--disable-fps', action='store_false', dest='enable_fps')

parser.add_option('--enable-clock', action='store_true', dest='enable_clock', default=False)
parser.add_option('--disable-clock', action='store_false', dest='enable_clock')


def main():
    options, args = parser.parse_args()

    app = Application(
        fullscreen=options.start_fullscreen,
        initial_size=options.resolution,
        rpc_server_address=options.rpc_listen_address,
        show_fps=options.enable_fps,
        show_clock=options.enable_clock,
    )

    if options.list_resolutions:
        for res in app.list_screen_resolutions():
            print "%dx%d" % res

    app.run()

if __name__ == '__main__':
    main()
