"""
Launch the server
"""

import optparse

from spotted_wall.server import Application


def get_parser():
    parser = optparse.OptionParser()

    def o(parser, *a, **kw):
        parser.add_option(*a, **kw)

    def flag(parser, name, default=False, **kw):
        var = 'flag_{}'.format(name.replace('-', '_'))
        optname = name.replace('_', '-')
        if 'help' in kw and kw['help']:
            kw['help'] += ' (default: {})'.format(str(default))
        parser.add_option(
            '--{}'.format(optname),
            action='store_true', dest=var, default=default, **kw)
        parser.add_option(
            '--no-{}'.format(optname),
            action='store_false', dest=var)

    group = optparse.OptionGroup(parser, 'Commands')
    o(group, '--list-resolutions',
      action='store_true', dest='cmd_list_resolutions',
      default=False,
      help='Prints the list of allowed resolutions and exits.')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Base configuration')
    o(group, '--resolution', action='store', dest='resolution',
      help='Default resolution for the screen. Defaults to the maximum '
           'resolution available.')
    o(group, '--rpc-address', action='append', dest='rpc_listen_address',
      metavar='ADDRESS', help='Address to which to bind the server. '
                              'Can be specified multiple times.')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Flags')
    flag(group, 'fullscreen', False, help='Start in fullscreen mode')
    flag(group, 'fps', False, help='Show frame rate')
    flag(group, 'clock', False, help='Show clock')
    parser.add_option_group(group)

    return parser


def main():
    parser = get_parser()
    options, args = parser.parse_args()

    if options.resolution is not None:
        resolution = options.resolution.split('x')
    else:
        resolution = (1280, 1024)

    app = Application(
        bind_addresses=options.rpc_listen_address,
        fullscreen=options.flag_fullscreen,
        initial_size=resolution,
        show_fps=options.flag_fps,
        show_clock=options.flag_clock,
    )

    if options.cmd_list_resolutions:
        print "Supported resolutions:"
        for res in app.thread_screen.screen.list_screen_resolutions():
            print "    %dx%d" % res
        return

    app.run()

if __name__ == '__main__':
    main()
