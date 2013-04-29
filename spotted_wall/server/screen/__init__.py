"""
The PyGame-powered screen
"""

import pygame
import time
import threading

from .message import Message

## Some default configuration for the screen
from spotted_wall.server.utils import lazy_property, Counter

SCREEN_PADDING = 40
MESSAGES_PADDING = 40
FONT_SIZE = 40
FRAME_RATE = 60
SHOW_FPS = True
DEBUG = True


class SpottedWallScreen(object):
    """
    The main Screen application, to be run in its own thread.

    Note: here we need to handle all the thread safety part
    when manipulating the list of messages and stuff.. beware!
    """

    def __init__(self,
                 initial_size=(1280, 1024),
                 fullscreen=False,
                 show_fps=True,
                 show_clock=True,
                 rpc_server_address=None,
                 enable_web_ui=False,
                 web_ui_address=None,
                 messages_font_size=FONT_SIZE):

        ## Container for the messages
        self.messages = {}

        ## threading.Lock() for access to the messages list
        self._msgs_access_lock = threading.Lock()

        ## Counter yielding message ids. Just call .next() to get one.
        self.message_id = Counter()

        ## Initialize pygame
        pygame.init()

        ## The clock, used to calculate FPS etc.
        self.clock = pygame.time.Clock()

        ## Prepare screen resolution sizes
        self._window_res = initial_size
        self._fullscreen_res = max(pygame.display.list_modes())

        ## Set the desired fullscreen mode
        self._set_video_mode(fullscreen=fullscreen)

        ## Set window title
        pygame.display.set_caption("Spotted Wall (main window)")

        ## Some extra configuration options
        self._messages_font_size = messages_font_size
        self.show_fps = show_fps
        self.show_clock = True

    def list_screen_resolutions(self):
        """
        List the available video modes
        """
        return pygame.display.list_modes()

    @property
    def size(self):
        return self.screen.get_size()

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    def run(self):
        """Start threads and main loop"""

        self._set_video_mode(self.size, self._fullscreen)

        self._main_loop()

    def _set_video_mode(self, resolution=None, fullscreen=False):
        """
        Change the current video mode.

        :param resolution:
            The new resolution to set, or None for autodiscover.
            If no resolution is specified, the last one for window/fullscreen
            will be used. If no fullscreen resolution is set, the largest
            available will be autoselect.
        :param fullscreen:
            Whether to go fullscreen or not.
        """
        _screen_flags = pygame.DOUBLEBUF | pygame.RESIZABLE
        self._fullscreen = fullscreen
        if resolution is None:
            resolution = self._fullscreen_res \
                if fullscreen else self._window_res
        if fullscreen:
            _screen_flags |= pygame.FULLSCREEN
            self._fullscreen_res = resolution
        else:
            self._window_res = resolution
        self.screen = pygame.display.set_mode(resolution, _screen_flags)

    def toggle_fullscreen(self):
        self._set_video_mode(fullscreen=not self._fullscreen)

    def _check_events(self):
        """Process all the new pygame events"""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass  # todo: use some kind of event to signal we want to quit?
                #self._quit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_f, pygame.K_F11):
                    self.toggle_fullscreen()

                # elif event.key == pygame.K_q:
                #     pass

            elif event.type == pygame.VIDEORESIZE:
                self._set_video_mode(event.size, self._fullscreen)

    def _cleanup_messages(self):
        """Cleanup the expired messages from queue"""
        with self._msgs_access_lock:
            for k in self.messages.keys():  # *NOT* iterkeys() !!
                if self.messages[k].is_expired():
                    del self.messages[k]

    def _draw_messages(self):
        with self._msgs_access_lock:
            _filled_space = SCREEN_PADDING
            messages_iterator = iter(sorted(self.messages.iteritems()))
            _shown_messages = 0

            while True:  # Loop until we finish space or messages..

                try:
                    message_id, message = messages_iterator.next()
                except StopIteration:
                    break  # no more messages..

                message_width = self.width - (2 * SCREEN_PADDING)
                req_space = \
                    _filled_space + message.get_height(message_width) \
                    + SCREEN_PADDING

                ## We make sure we draw at least one message no matter its
                ## length, to avoid jamming up the queue..
                if (req_space > self.height) and (_shown_messages > 0):
                    message.pause()
                    for message_id, message in messages_iterator:
                        message.pause()
                    break  # no more space..

                message.resume()  # make sure it's not paused..
                rendered = message.render(message_width)
                _shown_messages += 1

                if isinstance(rendered, (float, int)):
                    _filled_space += int(rendered *
                                         (message.height + MESSAGES_PADDING))

                else:
                    self.screen.blit(rendered, (SCREEN_PADDING, _filled_space))
                    _filled_space += rendered.get_height() + MESSAGES_PADDING

    def _draw_fps(self):
        if self.show_fps:
            fps = self.clock.get_fps()
            fpslabel = self.service_font.render(
                str(int(fps)), True, (255, 255, 255))
            rec = fpslabel.get_rect(top=5, right=self.width - 5)
            self.screen.blit(fpslabel, rec)

    def _draw_clock(self):
        if self.show_clock:
            clock_time = time.strftime('%T')
            clock_label = self.service_font.render(
                clock_time, True, (255, 255, 255))
            rec = clock_label.get_rect(
                bottom=self.height - 5, centerx=self.width/2)
            self.screen.blit(clock_label, rec)

    def _main_loop(self):
        """Application main loop"""
        while 1:
            self._check_events()
            self._cleanup_messages()
            self.screen.fill((0, 0, 0))
            self._draw_messages()
            self._draw_fps()
            self._draw_clock()
            pygame.display.flip()
            self.clock.tick(FRAME_RATE)

    @lazy_property
    def service_font(self):
        return pygame.font.SysFont('monospace', 16)

    @lazy_property
    def messages_font(self):
        return pygame.font.SysFont('monospace', self._messages_font_size)

    ##--------------------------------------------------------------------------
    ## Public interface
    ##--------------------------------------------------------------------------

    def add_message(self, text, color=None, duration=None):
        """Add a message to the wall"""

        with self._msgs_access_lock:
            print "Added message: {} {} {}".format(text, color, duration)
            message = Message(text, font=self.messages_font, color=color)

            if duration is not None:
                message.max_show_time = duration
            else:
                message.max_show_time = 10 + int(len(text) * .1)

            message_id = self.message_id.next()
            self.messages[message_id] = message
            return message_id

    def list_messages(self):
        """List all the messages"""

        with self._msgs_access_lock:
            for message_id, message in self.messages.iteritems():
                msg = message.to_dict()
                msg['id'] = message_id
                yield msg

    def get_message(self, message_id):
        """Get the contents of a given message, by id"""
        with self._msgs_access_lock:
            message = self.messages[message_id]
            msg = message.to_dict()
        msg['id'] = message_id
        return msg

    def delete_message(self, message_id, immediate=False):
        """Delete or fade out a message"""

        with self._msgs_access_lock:
            if immediate:
                del self.messages[message_id]
            else:
                self.messages[message_id].fadeOut()

    def hide_message(self, message_id):
        """Delete a specific message"""
        self.delete_message(message_id, immediate=False)

    def edit_message(self, message_id, values):
        """Update the selected message"""
        self.messages[message_id].update(values)

    def flush_messages(self):
        """Empty the list of messages"""
        with self._msgs_access_lock:
            self.messages[:] = []


class SpottedWallScreenThread(threading.Thread):

    daemon = True
    parent = None

    def __init__(self, parent):
        self.parent = parent
        super(SpottedWallScreenThread, self).__init__()
        self.screen = SpottedWallScreen()

    def run(self):
        self.screen.run()
