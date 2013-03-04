#!/usr/bin/env python

"""
:author: samu
:created: 3/2/13 3:06 AM
"""

import sys
import time
import threading
import random
import colorsys

import pygame


## === Configuration ===========================================================
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
SHOW_FPS = True
## =============================================================================


messages_text = [
    "This is an example message.",
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Mauris blandit pellentesque ornare. Suspendisse potenti.",
    "Maecenas quis libero nec arcu accumsan vestibulum bibendum sit amet nulla.",
    "Phasellus rutrum diam quis libero consectetur sed congue dolor placerat.",
    "Suspendisse mollis euismod justo, ac pharetra erat condimentum feugiat.",
    "Sed non diam nec sapien ultrices rutrum sit amet et ligula.",
    "Vivamus aliquam augue quis quam fringilla vestibulum eu at dui.",
    "Fusce faucibus leo vulputate mauris lobortis eget placerat dolor feugiat.",
    "Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.",
    "Ut posuere tincidunt mi, id feugiat leo euismod et.",
    "Phasellus vestibulum imperdiet dapibus.",
    "Suspendisse ultrices luctus aliquam.",
    "In risus nulla, dapibus a ultricies ut, suscipit vitae nunc.",
    "Vivamus accumsan, odio imperdiet tempus euismod, elit orci varius nisi, quis varius metus eros a nibh.",
    "Quisque eu risus non turpis molestie rutrum. Ut pellentesque laoreet mollis..",
    "Fusce lacinia egestas iaculis. Vestibulum id justo nisi, dictum blandit elit.",
    "Donec dapibus, nulla sagittis egestas eleifend, nulla nisl dictum turpis, sit amet pretium nisl odio suscipit odio.",
    "Quisque fringilla ante id velit tincidunt viverra.",
    "Praesent aliquam lacus id lectus fermentum sit amet accumsan mauris tincidunt.",
    "Aliquam hendrerit feugiat tortor, et egestas dui faucibus euismod.",
    "Curabitur convallis ante a dui viverra dignissim.",
    "Pellentesque tincidunt rutrum vehicula. Nulla varius augue sed augue lacinia vitae vehicula augue aliquet.",
    "Suspendisse ante magna, facilisis in blandit non, pellentesque eget enim.",
    "Phasellus sagittis mauris at urna condimentum eget sodales velit suscipit.",
    "Phasellus pulvinar elit vitae ante pellentesque sollicitudin..",
    "In ullamcorper felis in sapien imperdiet lobortis.",
    "Ut vestibulum nibh facilisis elit sodales vitae gravida quam rhoncus.",
    "Fusce vel risus et elit fringilla pretium.",
    "Curabitur molestie elit et ligula volutpat bibendum.",
    "Suspendisse nibh metus, fermentum quis fermentum non, tristique ac lacus.",
    "Integer nec risus nec massa pretium rhoncus eget nec mauris. Sed a vestibulum lorem.",
    "Ut sed turpis ut neque scelerisque porttitor. Ut ipsum ante, egestas sit amet laoreet ut, venenatis at massa.",
    "Suspendisse potenti. Nunc mollis leo non tortor bibendum condimentum.",
    "Phasellus tristique magna nec dui facilisis sodales.",
    "Sed convallis, mi vel blandit laoreet, eros neque egestas nulla, sit amet cursus nunc mauris ac dui.",
    "Proin fringilla vehicula faucibus. Aenean gravida risus nec felis malesuada ac aliquam mauris facilisis.",
    "Duis sodales adipiscing libero, non tempor odio pulvinar id.",
    "Nunc mollis iaculis eros, in viverra neque lobortis sit amet.",
    "Nulla sed turpis a metus dictum lacinia.",
    "Mauris lacus diam, feugiat quis facilisis quis, blandit sed leo.",
    "Donec eu fermentum elit.",
]


def circular_generator(items):
    while True:
        for item in items:
            yield item


# colors = circular_generator([
#     (0xff, 0x00, 0x00),
#     (0x00, 0xff, 0x00),
#     (0x00, 0x00, 0xff),
# ])


class Colors(object):
    def next(self):
        return tuple(x * 255
                     for x in colorsys.hsv_to_rgb(random.random(), 1, 1))

# colors = Colors()

colors = circular_generator([
    tuple(x * 255 for x in colorsys.hsv_to_rgb(deg / 360.0, .8, 1))
    for deg in xrange(0, 360, 30)
])


def lazy_property(fn):
    attr_name = '_lazy_' + fn.__name__

    def getter(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    def setter(self, value):
        setattr(self, attr_name, value)

    def deleter(self):
        delattr(self, attr_name)

    return property(fget=getter, fset=setter, fdel=deleter, doc=fn.__doc__)


def apply_alpha(surface, alpha):
    ## Applies a given alpha amount to a surface.
    for x in xrange(surface.get_width()):
        for y in xrange(surface.get_height()):
            color = surface.get_at((x, y))
            color.a = int(color.a * alpha)
            surface.set_at((x, y), color)
    return surface


## We want to display all the messages; each message should be shown for
## at least N seconds, then it can go out of screen..


class SeekableIterator(object):
    def __init__(self, iterable):
        self._iterable = iterable
        self._index = 0

    def next(self):
        try:
            val = self._iterable[self._index]
        except IndexError:
            raise StopIteration()
        else:
            self._index += 1
            return val

    def seek(self, pos):
        self._index += pos

    def jump(self, pos):
        self._index = pos


class Message(object):
    ST_NOTYET = 0
    ST_FADEIN = 1
    ST_SHOWN = 2
    ST_FADEOUT = 3
    ST_EXPIRED = 4

    def __init__(self, text, font=None, width=None, color=None):
        self.text = text
        self._rendered = None
        self._show_time = None
        self._expires_at = None
        self._fade_out_time = None
        self._fade_in_time = None
        self._cache = {}
        self._color = color or colors.next()
        self._width = width
        self._font = font

    def _wrap_text(self, font, words, width, separator=' '):
        if isinstance(words, basestring):
            words = words.split()

        _fulltext = separator.join(words)
        if font.size(_fulltext)[0] <= width:
            yield _fulltext
            return

        words_iter = SeekableIterator(words)

        current_line = []

        try:

            while True:
                next_word = words_iter.next()

                wannabe_nextline = separator.join(current_line + [next_word])
                if font.size(wannabe_nextline)[0] <= width:
                    ## Continue adding to current line
                    current_line.append(next_word)

                else:

                    ## It doesn't fit, so we have to free up things.
                    if len(current_line) > 0:
                        ## Flush the buffer..
                        yield separator.join(current_line)
                        current_line = []
                        words_iter.seek(-1)  # It will be reprocessed again..

                    else:
                        ## the word itself is too long.. wrap it
                        ## todo: I said, *wrap* it!!
                        yield next_word
                        # for piece in self._wrap_text(font, list(next_word),
                        #                              width, ''):
                        #     yield piece

        except StopIteration:
            ## If we have stuff in the buffer, flush it
            if len(current_line) > 0:
                yield separator.join(current_line)

    def _render(self, width, font, color):
        line_spacing = 10
        rendered_lines = []

        ## First of all, render all the lines of text, wrapped to fit the size
        for line in self.text.splitlines():
            line = line.strip()
            for new_line in self._wrap_text(font, line, width):
                rendered_text = font.render(new_line, True, color)
                rendered_lines.append(rendered_text)

        req_height = sum(t.get_height() for t in rendered_lines)
        req_height += line_spacing * (len(rendered_lines) - 1)

        new_surf = pygame.surface.Surface((width, req_height))
        cur_ypos = 0
        for line in rendered_lines:
            new_surf.blit(line, (0, cur_ypos))
            cur_ypos += line.get_height() + line_spacing

        return new_surf

    def set_shown(self):
        if self._show_time is None:
            self._show_time = time.time()

    def get_show_time(self):
        if self._show_time is None:
            return 0
        return time.time() - self._show_time

    @lazy_property
    def rendered(self):
        return self._render(
            width=self._width,
            font=self._font,
            color=self._color)

    def render(self):
        """
        Return the rendered surface, with alpha applied.
        """

        msg_state = self.get_state()

        rendered = self.rendered

        if msg_state == Message.ST_FADEIN:
            alpha = FADE_IN_EASING(self.get_fadein_percent())
            rendered.set_alpha(255 * alpha)

        elif msg_state == Message.ST_FADEOUT:
            alpha = FADE_OUT_EASING(self.get_fadeout_percent())
            rendered.set_alpha(255 * alpha)

        else:
            rendered.set_alpha(255)

        return rendered

    @property
    def rect(self):
        return self.rendered.get_rect()

    @property
    def height(self):
        return self.rendered.get_height()

    def set_font(self, font):
        del self.rendered
        self._font = font

    def set_width(self, width):
        del self.rendered
        self._width = width

    def fadeIn(self, fade_time):
        self._fade_in_time = fade_time
        self.set_shown()

    def get_fadein_percent(self):
        if self._fade_in_time is None:
            return 0
        if self._show_time + self._fade_in_time <= time.time():
            return 1.
        return 1.0 * self.get_show_time() / self._fade_in_time

    def fadeOut(self, fade_time):
        if self._expires_at is not None:
            return
        self._expires_at = time.time() + fade_time
        self._fade_out_time = fade_time

    def is_expired(self):
        if self._expires_at is None:
            return False
        return self._expires_at <= time.time()

    def get_fadeout_percent(self):
        if self._expires_at is None:
            return 0.
        if self.is_expired():
            return 1.
        return 1.0 * (self._expires_at - time.time()) / self._fade_out_time

    def get_state(self):
        st = self.get_show_time()
        if st <= 0:
            return self.ST_NOTYET
        if st < self._fade_in_time:
            return self.ST_FADEIN
        if self._expires_at is None:
            return self.ST_SHOWN
        if not self.is_expired():
            return self.ST_FADEOUT
        return self.ST_EXPIRED


class AddMsgsThread(threading.Thread):
    parent = None

    def run(self):
        ## todo: here we should listen for messages or similar..
        ## todo: use a Flask application to manage..?
        for text in messages_text:
            self.parent.add_message(text)
            if not self.parent.running:
                return
                ## todo find a smarter way to sleep while watching RUNNING..
            time.sleep(random.random() * 3)


class Application(object):
    def __init__(self):
        self.messages = []
        pygame.init()
        self.clock = pygame.time.Clock()
        self.size = self.width, self.height = 1280, 1024
        self.screen = pygame.display.set_mode(self.size, pygame.DOUBLEBUF, 32)
        self.myfont = pygame.font.Font('fonts/Vera.ttf', FONT_SIZE)
        self.fps_font = pygame.font.Font('fonts/Vera.ttf', 16)
        self.th1 = AddMsgsThread()
        self.th1.parent = self
        self.running = False

    def run(self):
        self.running = True
        self.th1.start()
        self.main_loop()

    def main_loop(self):
        while 1:
            ## Check for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print "Quitting..."
                    self.running = False
                    sys.exit()

            ## Clean up the expired messages
            ## Strategy: we want all messages to live at least
            ## MESSAGE_MIN_SHOW_TIME; if the queue is not full, we can
            ## wait MESSAGE_MAX_SHOW_TIME before deleting..

            ## todo: change the expire time depending on queue size..

            def would_fit(height):
                needed_height = 0
                for m in self.messages:
                    if not m.is_expired():
                        needed_height += m.height + MESSAGES_PADDING
                        if needed_height > height:
                            return False
                return True

            ## If the queue is full, try removing the first message
            if would_fit(self.height - (2 * SCREEN_PADDING)):
                try:
                    msg = self.messages[0]
                    if msg.get_show_time() > MESSAGE_MIN_SHOW_TIME:
                        # print ">>> FADING FIRST MESSAGE"
                        msg.fadeOut(FADE_OUT_TIME)

                except IndexError:
                    pass

            else:
                ## Fade out expired messages
                for message in self.messages:
                    if message.get_show_time() > MESSAGE_MAX_SHOW_TIME:
                        # print ">>> FADING HARD EXPIRED MESSAGE"
                        message.fadeOut(FADE_OUT_TIME)

            ## Cleanup expired messages
            self.messages = filter(lambda x: not x.is_expired(), self.messages)

            ## todo: apply the fadeout before deleting messages...

            ## We try to fill up the available space with some messages..
            self.screen.fill((0, 0, 0))  # Cleanup first..

            _filled_space = SCREEN_PADDING
            msgs = iter(self.messages)
            while (_filled_space + SCREEN_PADDING) < self.height:
                try:
                    message = msgs.next()

                except StopIteration:
                    break  # no more messages..

                rendered = message._rendered

                rendered_rc = rendered.get_rect()
                if _filled_space + rendered_rc.height + SCREEN_PADDING\
                        > self.height:
                    break  # no more space..

                message.fadeIn(FADE_IN_TIME)
                rendered = message.render()
                self.screen.blit(rendered, (SCREEN_PADDING, _filled_space))

                _filled_space += rendered_rc.height
                _filled_space += MESSAGES_PADDING  # padding

            if SHOW_FPS:
                fps = self.clock.get_fps()
                fpslabel = self.fps_font.render(str(int(fps)), True,
                                                (255, 255, 255))
                rec = fpslabel.get_rect(top=5, right=self.width - 5)
                self.screen.blit(fpslabel, rec)

            pygame.display.flip()
            self.clock.tick(FRAME_RATE)

    def add_message(self, text):
        print "Added message: {}".format(text)
        msg = Message(text,
                      font=self.myfont,
                      width=(self.width - (2 * SCREEN_PADDING)))
        self.messages.append(msg)


if __name__ == '__main__':
    app = Application()
    try:
        app.run()
    except:
        app.running = False
        raise
