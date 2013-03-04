"""
:author: samu
:created: 3/4/13 11:02 PM
"""

import time

import pygame

from .utils import Colors, lazy_property, SeekableIterator, wrap_pygame_text


MESSAGE_MIN_SHOW_TIME = 5
MESSAGE_MAX_SHOW_TIME = 10
FADE_IN_TIME = .5
FADE_OUT_TIME = 2.
FADE_IN_EASING = lambda x: x  # Linear
FADE_OUT_EASING = lambda x: x  # Linear
SCREEN_PADDING = 40
MESSAGES_PADDING = 40
FONT_SIZE = 40
FRAME_RATE = 60


colors = Colors()


class Message(object):
    """Representation of a text message"""

    ST_NOTYET = 0
    ST_FADEIN = 1
    ST_SHOWN = 2
    ST_FADEOUT = 3
    ST_EXPIRED = 4

    def __init__(self, text, font=None, width=None, color=None,
                 show_time=MESSAGE_MAX_SHOW_TIME):
        """
        :param text: Message text
        :param font: Font in which to render the message
        :param width: The maximum width this message can take
        :param color: The color in which to render this message
        :param show_time: For how long to show the message
        """

        self.text = text
        self.font = font
        self.width = width
        self.color = color or colors.next()

        self.max_show_time = show_time  # For how long to show
        self.shown_at = None  # First call of .render()

        self._fade_in_time = FADE_IN_TIME
        self._fade_in_easing = FADE_IN_EASING
        self._fade_out_time = FADE_OUT_TIME
        self._fade_out_easing = FADE_OUT_EASING

    def get_shown_time(self):
        if self.shown_at is None:
            return 0
        return time.time() - self.shown_at

    def get_time_left(self):
        return self.hide_time - time.time()

    def get_state(self):
        shown_time = self.get_shown_time()

        if shown_time == 0:
            return self.ST_NOTYET

        if shown_time > self.max_show_time:
            return self.ST_EXPIRED

        if shown_time > (self.max_show_time - self._fade_out_time):
            return self.ST_FADEOUT

        if shown_time < self._fade_in_time:
            return self.ST_FADEIN

        return self.ST_SHOWN

    @property
    def hide_time(self):
        if self.shown_at is None:
            return None
        return self.shown_at + self.max_show_time

    def _render(self, text, width, font, color):
        """
        Render the text on its own surface, considering
        word wrapping etc.
        """

        line_spacing = 10
        rendered_lines = []

        ## First of all, render all the lines of text, wrapped to fit the size
        for line in text.splitlines():
            line = line.strip()
            for new_line in wrap_pygame_text(font, line, width):
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

    @lazy_property
    def _rendered(self):
        return self._render(
            self.text,
            width=self.width,
            font=self.font,
            color=self.color)

    def render(self):
        """Return the rendered surface, with alpha applied"""

        if self.shown_at is None:
            self.shown_at = time.time()

        msg_state = self.get_state()
        rendered = self._rendered

        if msg_state == self.ST_FADEIN:
            alpha = FADE_IN_EASING(self.get_fadein_percent())

        elif msg_state == self.ST_SHOWN:
            alpha = 1

        elif msg_state == self.ST_FADEOUT:
            alpha = FADE_OUT_EASING(self.get_fadeout_percent())

        elif msg_state in (self.ST_NOTYET, self.ST_EXPIRED):
            alpha = 0

        else:
            raise ValueError("Invalid state: %d" % msg_state)

        rendered.set_alpha(255 * alpha)
        return rendered

    def hide(self, delta=0):
        self.max_show_time = min(self.max_show_time, time.time() + delta)

    @property
    def rect(self):
        return self._rendered.get_rect()

    @property
    def height(self):
        return self.rect.height

    def get_fadein_percent(self):
        state = self.get_state()
        if state < self.ST_FADEIN:
            return 0.
        elif state > self.ST_FADEIN:
            return 1.
        delta = 1. * self.get_shown_time() / self._fade_in_time
        return min(1., max(0., delta))

    def get_fadeout_percent(self):
        state = self.get_state()
        if state < self.ST_FADEOUT:
            return 0.
        elif state > self.ST_FADEOUT:
            return 1.
        delta = 1. * self.get_time_left() / self._fade_in_time
        return min(1., max(0., delta))

    def is_expired(self):
        return self.get_state() == self.ST_EXPIRED
