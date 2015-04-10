"""
Settings for a project.
"""

import itertools


class AbstractSettings:
    ROW_UP = 0
    ROW_MIDDLE = 0
    ROW_DOWN = 0

    ORDER = ['MIDDLE', 'DOWN', 'UP']

    def to_json(self):
        return {k: getattr(self, k)
                for k in itertools.chain(self.__dict__, self.__class__.__dict__)
                if not k.startswith('_')
        }

    def from_json(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)

    def row(self, label):
        return getattr(self, 'ROW_' + label)

    def start_offset(self, label):
        """Returns the index of the starting photo for the given row.

        >>> sett = SybrenStandard()
        >>> sett.start_offset('MIDDLE')
        0
        >>> sett.start_offset('DOWN')
        12
        >>> sett.start_offset('UP')
        20

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

        order_idx = self.ORDER.index(label)
        return sum(self.row(label) for label in self.ORDER[:order_idx])

    def cp_offset(self, hdr_stack_size: int) -> int:
        """Returns the offset in the HDR stack, for the image used to find control points."""

        return 0


class SybrenStandard(AbstractSettings):
    ROW_UP = 8
    ROW_MIDDLE = 12
    ROW_DOWN = 8

    ORDER = ['MIDDLE', 'DOWN', 'UP', '€ ☮']


class SybrenLX100(AbstractSettings):
    ROW_UP = 8
    ROW_MIDDLE = 12
    ROW_DOWN = 8
    ROW_ZENITH = 1
    ROW_NADIR = 1

    ORDER = ['MIDDLE', 'UP', 'DOWN', 'ZENITH', 'NADIR']

    def cp_offset(self, hdr_stack_size: int) -> int:
        """Returns the offset in the HDR stack, for the image used to find control points.

        >>> sett = SybrenLX100()
        >>> sett.cp_offset(7)
        3
        """

        return hdr_stack_size // 2


DEFAULT_SETTINGS = SybrenStandard

if __name__ == '__main__':
    import doctest
    doctest.testmod()
