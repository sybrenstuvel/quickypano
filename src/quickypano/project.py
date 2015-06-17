"""
Data model for projects.
"""

import copy
import json
import os.path
import logging
import os
import threading
import math
import PIL.Image
import PIL.ExifTags

from . import settings, hugin

log = logging.getLogger(__name__)

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

# Params that are always cloned from the anchor image in the stack
CLONE_FROM_STACK = 'y p r TrX TrY TrZ j'.split()


class Image:
    def __init__(self, filename):
        self.parameters = DEFAULT_PARAMS.copy()
        self.filename = filename

        self.calculate_ev()

    def calculate_ev(self):
        img = PIL.Image.open(self.filename)
        exif = {PIL.ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in PIL.ExifTags.TAGS}

        # Determine width/height in pixels too, now that we have the file open anyway.
        width, height = img.size
        self.parameters['w'] = width
        self.parameters['h'] = height

        # Source: http://en.wikipedia.org/wiki/Exposure_value
        f_nr = exif['FNumber'][0] / exif['FNumber'][1]
        t = exif['ExposureTime'][0] / exif['ExposureTime'][1]
        ev = math.log2(f_nr ** 2 / t)

        self.parameters['Eev'] = ev

class Project:
    def __init__(self):
        self.filename = ''
        self.hugin_filename = ''
        self.photos = []  # list of Image objects
        self.stack_size = 1  # Number of photos in each HDR stack; 1 = LDR
        self.settings = settings.DEFAULT_SETTINGS()
        self.control_points = []  # list of control point line strings
        self.average_ev = 0.0  # average exposure value

    @property
    def is_hdr(self) -> bool:
        return self.stack_size > 1

    def load_photos(self, filenames):
        self.photos = [Image(filename) for filename in sorted(filenames)]

    def move_anchor(self, anchor_idx):
        """Moves the N'th image to the front of each stack."""

        if not self.is_hdr:
            return

        ssize = self.stack_size
        for stack_idx in range(len(self.photos) // ssize):
            stack_slice = slice(stack_idx * ssize, (stack_idx + 1) * ssize)
            stack = self.photos[stack_slice]
            anchor = stack[anchor_idx]
            del stack[anchor_idx]
            self.photos[stack_slice] = [anchor] + stack

    def set_variables(self):
        # TODO: make nice row -> position mapping for this.
        start_middle = self.settings.start_offset('MIDDLE')
        next_middle = self.settings.next_offset('MIDDLE')
        start_down = self.settings.start_offset('DOWN')
        next_down = self.settings.next_offset('DOWN')
        start_up = self.settings.start_offset('UP')
        next_up = self.settings.next_offset('UP')
        start_zenith = self.settings.start_offset('ZENITH')
        next_zenith = self.settings.next_offset('ZENITH')
        start_nadir = self.settings.start_offset('NADIR')
        next_nadir = self.settings.next_offset('NADIR')

        self.photos[0].parameters['v'] = self.settings.VERTICAL_FOV

        for idx, image in enumerate(self.photos):
            stack_idx = idx // self.stack_size
            stack_anchor = stack_idx * self.stack_size  # Always the first image in the stack

            if start_middle <= stack_idx < next_middle:
                # Middle row
                idx_in_row = stack_idx
                row_size = self.settings.ROW_MIDDLE
                pitch = 0
            elif start_down <= stack_idx < next_down:
                # Down row
                idx_in_row = stack_idx - start_down
                row_size = self.settings.ROW_DOWN
                pitch = -45
            elif start_up <= stack_idx <= next_up:
                # Up row
                idx_in_row = stack_idx - start_up
                row_size = self.settings.ROW_UP
                pitch = 45
            elif start_zenith <= stack_idx <= next_zenith:
                idx_in_row = stack_idx - start_zenith
                row_size = self.settings.ROW_ZENITH
                pitch = -90
            elif start_nadir <= stack_idx <= next_nadir:
                idx_in_row = stack_idx - start_nadir
                row_size = self.settings.ROW_NADIR
                pitch = 90
            else:
                log.warn('Unknown what to do with photo on stack index %i', stack_idx)
                idx_in_row = 0
                row_size = 1
                pitch = 0

            yaw = 360 * idx_in_row / row_size
            variables = {'y': yaw, 'p': pitch, 'r': 0.0}

            # Clone from first image or stack
            if idx > 0:
                for param in CLONE_FROM_FIRST:
                    variables[param] = '=0'
            if self.is_hdr and idx != stack_anchor:
                for param in CLONE_FROM_STACK:
                    variables[param] = '=%i' % stack_anchor

            image.parameters.update(variables)

        self.average_ev = sum(img.parameters['Eev'] for img in self.photos) / len(self.photos)


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
        tmpproj_pto = os.path.join(basedir, 'tmppto-%i-%i.pto' %
                                   (os.getpid(), threading.get_ident()))

        hugin.pto_var(self.hugin_filename, tmpproj_pto)
        os.unlink(self.hugin_filename)
        os.rename(tmpproj_pto, self.hugin_filename)

        log.debug('Saved project as %s', self.hugin_filename)

    def get_slice(self, indices):
        # Clone the project
        clone = Project()
        clone.filename = self.filename
        clone.hugin_filename = self.hugin_filename
        clone.photos = [copy.deepcopy(self.photos[i]) for i in indices]
        clone.stack_size = self.stack_size
        clone.settings = self.settings

        # Fix up references to other photos by copying the referred value.
        for photo in clone.photos:
            new_params = {}
            for key, value in photo.parameters.items():
                # Keep following references until we've found an actual value.
                while isinstance(value, str) and value.startswith('='):
                    refidx = int(value[1:])
                    value = self.photos[refidx].parameters[key]
                new_params[key] = value

            photo.parameters.update(new_params)

        return clone

