"""
Settings for a project.
"""

import itertools
import functools


class AbstractSettings:
    ROW_UP = 0
    ROW_MIDDLE = 0
    ROW_DOWN = 0

    ORDER = ['MIDDLE', 'DOWN', 'UP']

    VERTICAL_FOV = 90

    def to_json(self):
        return {k: getattr(self, k)
                for k in itertools.chain(self.__dict__, self.__class__.__dict__)
                if not k.startswith('_')
                }

    def from_json(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)

    @functools.lru_cache()
    def row(self, label):
        return getattr(self, 'ROW_' + label)

    @functools.lru_cache()
    def start_offset(self, label):
        """Returns the index of the starting photo for the given row.

        >>> sett = Sybren7D()
        >>> sett.start_offset('MIDDLE')
        0
        >>> sett.start_offset('DOWN')
        12
        >>> sett.start_offset('UP')
        20
        >>> sett.start_offset('ZENITH')
        -1
        >>> sett.start_offset('NADIR')
        -1

        >>> sett = SybrenLX100()
        >>> sett.start_offset('MIDDLE')
        0
        >>> sett.start_offset('DOWN')
        20
        >>> sett.start_offset('UP')
        12
        >>> sett.start_offset('ZENITH')
        28
        >>> sett.start_offset('NADIR')
        29

        """

        if label not in self.ORDER:
            return -1

        order_idx = self.ORDER.index(label)
        return sum(self.row(label) for label in self.ORDER[:order_idx])

    @functools.lru_cache()
    def next_offset(self, label):
        """Returns the index of the next photo for the given row.

        >>> sett = Sybren7D()
        >>> sett.next_offset('MIDDLE')
        12
        >>> sett.next_offset('DOWN')
        20
        >>> sett.next_offset('UP')
        28
        >>> sett.next_offset('ZENITH')
        -1
        >>> sett.next_offset('NADIR')
        -1

        >>> sett = SybrenLX100()
        >>> sett.next_offset('MIDDLE')
        12
        >>> sett.next_offset('DOWN')
        28
        >>> sett.next_offset('UP')
        20
        >>> sett.next_offset('ZENITH')
        29
        >>> sett.next_offset('NADIR')
        30

        """

        if label == self.ORDER[-1]:
            # Last one, just sum everything
            order_idx = len(self.ORDER)
        elif label not in self.ORDER:
            return -1
        else:
            order_idx = self.ORDER.index(label) + 1

        return sum(self.row(label) for label in self.ORDER[:order_idx])


class Sybren7D(AbstractSettings):
    ROW_UP = 8
    ROW_MIDDLE = 12
    ROW_DOWN = 8

    ORDER = ['MIDDLE', 'DOWN', 'UP']

    VERTICAL_FOV = 73.739795291688  # 10mm lens on Canon 7D


class SybrenLX100(AbstractSettings):
    ROW_UP = 8
    ROW_MIDDLE = 12
    ROW_DOWN = 8
    ROW_ZENITH = 1
    ROW_NADIR = 1

    ORDER = ['MIDDLE', 'UP', 'DOWN', 'ZENITH', 'NADIR']

    VERTICAL_FOV = 53.2190900384409  # 24mm, i.e. zoomed out fully


class SybrenLX100DoubleNadir(SybrenLX100):
    ROW_NADIR = 2

    ORDER = ['MIDDLE', 'UP', 'DOWN', 'NADIR', 'ZENITH']


class SybrenLX100NoNadir(SybrenLX100):
    ROW_NADIR = 0

    ORDER = ['MIDDLE', 'UP', 'DOWN', 'ZENITH']


class SybrenLX100SmallSteps(SybrenLX100):
    ROW_UP = 12
    ROW_MIDDLE = 12
    ROW_DOWN = 12
    ROW_ZENITH = 1
    ROW_NADIR = 0

    ORDER = ['MIDDLE', 'DOWN', 'UP', 'ZENITH']


class SybrenLX100SmallStepsNadirZenith(SybrenLX100):
    ROW_UP = 12
    ROW_MIDDLE = 12
    ROW_DOWN = 12
    ROW_ZENITH = 1
    ROW_NADIR = 1

    ORDER = ['MIDDLE', 'UP', 'DOWN', 'ZENITH', 'NADIR']


class SybrenLX100SmallStepsZenith(SybrenLX100):
    ROW_UP = 12
    ROW_MIDDLE = 12
    ROW_DOWN = 12
    ROW_ZENITH = 1
    ROW_NADIR = 1

    ORDER = ['MIDDLE', 'DOWN', 'UP', 'ZENITH', 'NADIR']


DEFAULT_SETTINGS = SybrenLX100SmallStepsZenith


# def iter_settings():
#     """Generator, yields all AbstractSettings subclasses."""
#



if __name__ == '__main__':
    import doctest

    doctest.testmod()
