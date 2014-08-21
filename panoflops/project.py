"""
Data model for projects.
"""

import json
import os.path

from . import settings, hugin


DEFAULT_PARAMS = {
    'y': 0.0,
    'p': 0.0,
    'r': 0.0,
    'w': 3456,
    'h': 5184,
    'f': 0,
    'v': 73.739795291688,
    'Ra': 0,
    'Rb': 0,
    'Rc': 0,
    'Rd': 0,
    'Re': 0,
    'Eev': 4,
    'Er': 1,
    'Eb': 1,
    'TrX': 0,
    'TrY': 0,
    'TrZ': 0,
    'j': 0,
    'a': 0,
    'b': 0,
    'c': 0,
    'd': 0,
    'e': 0,
    'g': 0,
    't': 0,
    'Va': 1,
    'Vb': 0,
    'Vc': 0,
    'Vd': 0,
    'Vx': 0,
    'Vy': 0,
    'Vm': 5,
}

# Params that are always cloned from the first image
CLONE_FROM_FIRST = 'v Ra Rb Rc Rd Re a b c d e g t Va Vb Vc Vd Vx Vy'.split()

# Params that are always cloned from the first image in the stack
CLONE_FROM_STACK = 'y p r TrX TrY TrZ j'.split()


class Image:
    def __init__(self, filename):
        self.parameters = DEFAULT_PARAMS.copy()
        self.filename = filename


class Project:
    def __init__(self):
        self.filename = ''
        self.hugin_filename = ''
        self.photos = []
        self.is_hdr = False
        self.settings = settings.DEFAULT_SETTINGS()
        self.control_points = []  # list of control point line strings

    def load_photos(self, filenames):
        self.photos = [Image(filename) for filename in filenames]

    def set_variables(self):

        for idx, image in enumerate(self.photos):
            idx_for_ypr = idx

            if self.is_hdr:
                first_of_stack = idx - (idx % 3)
                idx_for_ypr = first_of_stack / 3

            # TODO: get order from settings
            if idx_for_ypr < self.settings.ROW_MIDDLE:
                # Middle row
                idx_in_row = idx_for_ypr
                row_size = self.settings.ROW_MIDDLE
                pitch = 0
            elif idx_for_ypr < self.settings.ROW_MIDDLE + self.settings.ROW_DOWN:
                # Down row
                idx_in_row = idx_for_ypr - self.settings.ROW_MIDDLE
                row_size = self.settings.ROW_DOWN
                pitch = -45
            else:
                # Up row
                idx_in_row = idx_for_ypr - self.settings.ROW_MIDDLE - self.settings.ROW_DOWN
                row_size = self.settings.ROW_UP
                pitch = 45

            yaw = 360 * idx_in_row / row_size
            variables = {'y': yaw, 'p': pitch, 'r': 0.0}

            # Clone from first image or stack
            if idx > 0:
                for param in CLONE_FROM_FIRST:
                    variables[param] = '=0'
            if self.is_hdr and idx != first_of_stack:
                for param in CLONE_FROM_STACK:
                    variables[param] = '=%i' % first_of_stack

            image.parameters.update(variables)


    @classmethod
    def load(cls, filename: str):
        with open(filename, 'r', encoding='utf-8') as infile:
            data = json.load(infile)

        if data['VERSION'] > 1:
            raise ValueError('Unsupported value %i' % data['VERSION'])

        project = Project()
        for key, value in data['project'].items():
            setattr(project, key, value)

        project.settings = settings.AbstractSettings()
        project.settings.from_json(data['project']['settings'])

    def save(self, filename: str):
        data = {
            'VERSION': 1,
            'project': self.__dict__,
        }
        data['project']['settings'] = data['project']['settings'].to_json()

        with open(filename, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    def create_hugin_project(self):
        # Create the PTO

        with open(self.hugin_filename, 'w', encoding='utf-8') as outfile:
            hugin.write(outfile, self)

        # Modify it using pto_var
        basedir = os.path.dirname(self.hugin_filename)
        tmpproj_pto = os.path.join(basedir, 'tmpproj.pto')
        hugin.pto_var(self.hugin_filename, tmpproj_pto)
        os.unlink(self.hugin_filename)
        os.rename(tmpproj_pto, self.hugin_filename)

        print('Moved to %s' % self.hugin_filename)

    def get_slice(self, indices):
        # Clone the project
        clone = Project()
        clone.filename = self.filename
        clone.hugin_filename = self.hugin_filename
        clone.photos = [self.photos[i] for i in indices]
        clone.is_hdr = self.is_hdr
        clone.settings = self.settings

        return clone
