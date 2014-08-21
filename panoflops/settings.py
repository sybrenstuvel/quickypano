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


class SybrenStandard(AbstractSettings):
    ROW_UP = 8
    ROW_MIDDLE = 12
    ROW_DOWN = 8

    ORDER = ['MIDDLE', 'DOWN', 'UP', '€ ☮']


DEFAULT_SETTINGS = SybrenStandard
