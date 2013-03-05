"""
:author: samu
:created: 3/4/13 11:02 PM
"""

import time

import pygame

from .utils import Colors, lazy_property, wrap_pygame_text, pygame_color_to_hex


MESSAGE_MIN_SHOW_TIME = 10
MESSAGE_MAX_SHOW_TIME = 30

FADE_IN_TIME = .5
FADE_OUT_TIME = 2.
DISAPPEAR_TIME = 2.

FADE_IN_EASING = lambda x: x  # Linear
FADE_OUT_EASING = lambda x: x  # Linear
DISAPPEAR_EASING = lambda x: x  # Linear

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
    ST_DISAPPEARING = 4
    ST_EXPIRED = 5

    def __init__(self, text, font=None, width=None, color=None,
                 show_time=MESSAGE_MAX_SHOW_TIME):
        """
        :param text: Message text
        :param font: Font in which to render the message
        :param width: The maximum width this message can take
        :param color: The color in which to render this message
        :param show_time: For how long to show the message
        """

        self._color = None

        self.text = text
        self.font = font
        self.color = color or colors.next()
        self._width = width

        self.max_show_time = show_time  # For how long to show
        self.shown_at = None  # First call of .render()

        self._paused_time = None  # Pause start time

        self._fade_in_time = FADE_IN_TIME
        self._fade_in_easing = FADE_IN_EASING
        self._fade_out_time = FADE_OUT_TIME
        self._fade_out_easing = FADE_OUT_EASING
        self._disappear_time = DISAPPEAR_TIME
        self._disappear_easing = DISAPPEAR_EASING

    def get_shown_time(self):
        if self.shown_at is None:
            return 0
        return self.get_time() - self.shown_at

    def get_time_left(self):
        return self.hide_time - self.get_time()

    def get_state(self):
        shown_time = self.get_shown_time()

        if shown_time == 0:
            return self.ST_NOTYET

        if shown_time > self.max_show_time:
            if shown_time > (self.max_show_time + self._disappear_time):
                return self.ST_EXPIRED
            return self.ST_DISAPPEARING

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
            pos = line.get_rect(centerx=width / 2, top=cur_ypos)
            new_surf.blit(line, pos)
            #new_surf.blit(line, (0, cur_ypos))
            cur_ypos += line.get_height() + line_spacing

        return new_surf

    @lazy_property
    def _rendered(self):
        return self._render(
            self.text,
            width=self.width,
            font=self.font,
            color=self.color)

    def _flush_caches(self):
        try:
            del self._rendered
        except AttributeError:
            pass

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        if self._width != value:
            self._flush_caches()
        self._width = value

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._flush_caches()
        if value is not None:
            self._color = pygame.color.Color(value)
        else:
            self._color = None

    def get_height(self, width=None):
        self.width = width
        return self._rendered.get_rect().height

    def render(self, width=None):
        """Return the rendered surface, with alpha applied"""

        if width is not None:
            if width != self.width:
                self._flush_caches()
                self.width = width

        if self.shown_at is None:
            self.shown_at = self.get_time()

        msg_state = self.get_state()
        rendered = self._rendered

        if msg_state == self.ST_FADEIN:
            alpha = self._fade_in_easing(self.get_fadein_percent())

        elif msg_state == self.ST_SHOWN:
            alpha = 1

        elif msg_state == self.ST_FADEOUT:
            alpha = self._fade_out_easing(self.get_fadeout_percent())

        elif msg_state in (self.ST_NOTYET, self.ST_EXPIRED):
            #return pygame.surface.Surface((0, 0))
            return 0.

        elif msg_state == self.ST_DISAPPEARING:
            return self._disappear_easing(1. - self.get_disappear_percent())
            # new_height = self.height * \
            #     self._disappear_easing(1. - self.get_disappear_percent())
            #return pygame.surface.Surface((0, new_height))
            # return new_height

        else:
            raise ValueError("Invalid state: %d" % msg_state)

        rendered.set_alpha(255 * alpha)
        return rendered

    def hide(self, delta=0):
        self.max_show_time = min(self.max_show_time, self.get_time() + delta)

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

    def get_disappear_percent(self):
        state = self.get_state()
        if state < self.ST_DISAPPEARING:
            return 0.
        if state > self.ST_DISAPPEARING:
            return 1.
        delta = 1. * (self.get_time() - self.hide_time) / self._disappear_time
        return min(1., max(0., delta))

    def is_expired(self):
        return self.get_state() == self.ST_EXPIRED

    def get_time(self):
        if self._paused_time is not None:
            return self._paused_time
        return time.time()

    def pause(self):
        if self.shown_at is None:
            return  # Ignore pause
        if self._paused_time is None:
            self._paused_time = self.get_time()

    def resume(self):
        if self._paused_time is not None:
            delta = time.time() - self._paused_time
            self.shown_at += delta
        self._paused_time = None

    def fadeOut(self):
        """Start the fadeOut right now.."""
        if self.get_state() < self.ST_FADEOUT:
            self.max_show_time = self.get_time() + self._fade_out_time

    def update(self, values):
        self._flush_caches()  #todo: only if changed..?
        for key in ['color', 'text', 'font']:
            if key in values:
                setattr(self, key, values[key])
        if 'max_show_time' in values:
            self._max_show_time = values['max_show_time']

    def to_dict(self, withmeta=True):
        data = {
            'text': self.text,
            'color': pygame_color_to_hex(self.color),
        }
        if withmeta:
            data.update({
            '_shown_at': self.shown_at,
            '_max_show_time': self.max_show_time,
            '_shown_time': self.get_shown_time(),
            })
        return data

    @classmethod
    def from_dict(cls, data):
        newcls = cls(data['text'])
        newcls.update(data)
        return newcls
