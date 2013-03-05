"""
:author: samu
:created: 3/4/13 10:27 PM
"""

import colorsys
import random


def circular_generator(items):
    while True:
        for item in items:
            yield item


# colors = circular_generator([
#     (0xff, 0x00, 0x00),
#     (0x00, 0xff, 0x00),
#     (0x00, 0x00, 0xff),
# ])

# colors = circular_generator([
#     tuple(x * 255 for x in colorsys.hsv_to_rgb(deg / 360.0, .8, 1))
#     for deg in xrange(0, 360, 30)
# ])


class Colors(object):
    _colors = [
        tuple(int(x * 255) for x in colorsys.hsv_to_rgb(deg / 360.0, .8, 1))
        for deg in xrange(0, 360, 30)
    ]
    _prev_color = None

    def next(self):
        _color = random.choice(self._colors)
        if _color == self._prev_color:
            return self.next()
        self._prev_color = _color
        return _color

# colors = Colors()


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


class Counter(object):
    def __init__(self, current=1):
        self._count = current

    def next(self):
        c = self._count
        self._count += 1
        return c


def wrap_pygame_text(font, words, width, separator=' '):
    """Wrap some text to fit a given width"""

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

    except StopIteration:
        ## If we have stuff in the buffer, flush it
        if len(current_line) > 0:
            yield separator.join(current_line)


def pygame_color_to_hex(c):
    """
    Converts a Pygame Color to its string representation,
    for use in CSS.
    """
    return '#%02x%02x%02x%02x' % (c.r, c.g, c.b, c.a)


def pygame_color_from_hex(color):
    import pygame
    return pygame.color.Color(color)
