#!/usr/bin/env python

"""
:author: samu
:created: 3/2/13 3:06 AM
"""

import sys
import threading

import pygame


## === Configuration ===========================================================
import time

MESSAGE_MIN_SHOW_TIME = 5
MESSAGE_MAX_SHOW_TIME = 30
FADE_IN_TIME = .5
FADE_OUT_TIME = 2.
FADE_IN_EASING = lambda x: x  # Linear
FADE_OUT_EASING = lambda x: x  # Linear
SCREEN_PADDING = 40
MESSAGES_PADDING = 40
FONT_SIZE = 40
FRAME_RATE = 60
# SHOW_FPS = True
## =============================================================================


from .utils import Colors, lazy_property, SeekableIterator, Counter
from .message import Message


## We want to display all the messages; each message should be shown for
## at least N seconds, then it can go out of screen..

class RPCServerThread(threading.Thread):
    """Thread object to expose a ZeroRPC service"""

    daemon = True

    parent = None
    address = "tcp://0.0.0.0:4242"

    def run(self):
        import zerorpc

        app = self.parent

        class RPCObject(object):
            def add_message(self, name, color=None):
                return app.add_message(name, color=color)

            def list_messages(self):
                pass

        self.socket = zerorpc.Server(RPCObject())
        self.socket.bind(self.address)
        self.socket.run()


class Application(object):
    def __init__(self, initial_size=(1280, 1024), fullscreen=False,
                 show_fps=True):

        ## Container for the messages
        self.messages = {}

        pygame.init()

        ## Clock, used to calculate FPS
        self.clock = pygame.time.Clock()

        self._window_res = initial_size
        self._fullscreen_res = 0, 0

        self._set_video_mode(fullscreen=fullscreen)


        # _screen_flags = pygame.DOUBLEBUF | pygame.RESIZABLE
        # if fullscreen:
        #     _screen_flags |= pygame.FULLSCREEN
        # self.screen = pygame.display.set_mode(initial_size, _screen_flags)

        pygame.display.set_caption("Spotted Wall (main window)")

        #self.messages_font = pygame.font.Font('fonts/Vera.ttf', FONT_SIZE)
        # self.messages_font = pygame.font.SysFont('sans-serif', FONT_SIZE)
        self.messages_font = pygame.font.SysFont('monospace', FONT_SIZE)

        self.show_fps = show_fps

        self.thread_rpc = RPCServerThread()
        self.thread_rpc.parent = self  # Needed to interact

        self.message_id = Counter()
        self.show_clock = True

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
        self.thread_rpc.start()
        self.main_loop()

    def _set_video_mode(self, resolution=None, fullscreen=False):
        _screen_flags = pygame.DOUBLEBUF | pygame.RESIZABLE
        self._fullscreen = fullscreen
        if resolution is None:
            resolution = self._fullscreen_res if fullscreen else self._window_res
        if fullscreen:
            _screen_flags |= pygame.FULLSCREEN
            self._fullscreen_res = resolution
        else:
            self._window_res = resolution
        self.screen = pygame.display.set_mode(resolution, _screen_flags)

    def _toggle_fullscreen(self):
        self._set_video_mode(fullscreen=not self._fullscreen)

    def _quit(self):
        print "Quitting..."
        sys.exit()

    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_f, pygame.K_F11):
                    self._toggle_fullscreen()

                elif event.key == pygame.K_q:
                    self._quit()

            elif event.type == pygame.VIDEORESIZE:
                self._set_video_mode(event.size, self._fullscreen)

    def main_loop(self):
        while 1:
            self._check_events()

            ## todo: If the queue is too full, decrease the show time

            ## Cleanup expired messages
            for k in self.messages.keys():  # *NOT* iterkeys() !!
                if self.messages[k].is_expired():
                    del self.messages[k]

            ## Blank the screen before drawing
            self.screen.fill((0, 0, 0))

            _filled_space = SCREEN_PADDING

            messages_iterator = iter(sorted(self.messages.iteritems()))

            while True:  # Loop until we finish space or messages..

                try:
                    message_id, message = messages_iterator.next()
                except StopIteration:
                    break  # no more messages..

                if _filled_space + message.height + SCREEN_PADDING \
                        > self.height:
                    break  # no more space..
                    ## todo: "pause" the messages? this is needed to handle out-of-screen etc..

                rendered = message.render()
                self.screen.blit(rendered, (SCREEN_PADDING, _filled_space))
                _filled_space += message.height + MESSAGES_PADDING

            if self.show_fps:
                fps = self.clock.get_fps()
                fpslabel = self.service_font.render(
                    str(int(fps)), True, (255, 255, 255))
                rec = fpslabel.get_rect(top=5, right=self.width - 5)
                self.screen.blit(fpslabel, rec)

            if self.show_clock:
                clock_time = time.strftime('%T')
                clock_label = self.service_font.render(clock_time, True, (255, 255, 255))
                rec = fpslabel.get_rect(bottom=self.height - 5, centerx=self.width/2)
                self.screen.blit(clock_label, rec)

            pygame.display.flip()
            self.clock.tick(FRAME_RATE)

    @lazy_property
    def service_font(self):
        #return pygame.font.Font('fonts/Vera.ttf', 16)
        return pygame.font.SysFont('monospace', 16)

    def add_message(self, text, color=None):
        """Add a message to the wall"""

        print "Added message: {}".format(text)
        message = Message(
            text,
            font=self.messages_font,
            width=(self.width - (2 * SCREEN_PADDING)),
            color=color)
        message_id = self.message_id.next()
        self.messages[message_id] = message
        return message_id

    def list_messages(self):
        """List all the messages"""

        for message_id, message in self.messages.iteritems():
            yield {
                'id': message_id,
                'text': message.text,
                'color': message.color,
            }

    def delete_message(self, message_id, immediate=False):
        """Delete all the messages"""

        if immediate:
            del self.messages[message_id]
        else:
            self.messages[message_id].fadeOut(FADE_OUT_TIME)
