# The MIT License (MIT)
#
# Copyright (c) 2014 Matěj Šmíd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# .pto file format description:
# http://hugin.sourceforge.net/docs/nona/nona.txt
# http://sourceforge.net/p/panotools/libpano13/ci/default/tree/doc/Optimize.txt


class HuginPto:
    """
    Parse and query Hugin pto configuration files.

    >>> pto = HuginPto('cam1 - cam8.pto')
    >>> pto.parsed.keys()
    ['c', 'i', 'k', 'm', 'o', 'p', 'v']

    >>> pto.parsed['c'][0]
    {'N': '1',
     'X': '565',
     'Y': '749',
     'n': '0',
     't': '0',
     'x': '1034',
     'y': '619'}

    >>> pto.parsed['i'][0]
    {'E': ['ev0', 'r1', 'b1'],
     'Ra': '0',
     'Rb': '0',
     'Rc': '0',
     'Rd': '0',
     'Re': '0',
     'TrX': '0',
     'TrY': '0',
     'TrZ': '0',
     'V': ['a1', 'b0', 'c0', 'd0', 'x0', 'y0', 'm5'],
     'a': '0',
     'b': '0',
     'c': '0',
     'd': '0',
     'e': '0',
     'f': '0',
     'g': '0',
     'h': '1024',
     'j': '0',
     'n': '"kamera1.png"',
     'p': '0',
     'r': '0',
     't': '0',
     'v': '50',
     'w': '1280',
     'y': '0'}

    """
    def __init__(self, filename):
        self.commands = {'p': [],
                         'o': [],
                         'i': ['f', 'w', 'h', 'v', 'y', 'p', 'r', 'a', 'b', 'c', 'd', 'e', 'g', 't', 'S', 'C',
                               'o', 'X', 'Y', 'Z', 'n', 'TiX', 'TiY', 'TiZ', 'TiS', 'TrX', 'TrY', 'TrZ', 'Te0',
                               'Te1', 'Te2', 'Te3', 'Ra', 'Rb', 'Rc', 'Rd', 'Re', 'E', 'j', 'V'],
                         'm': [],
                         'k': [],
                         'v': [],
                         'c': ['n', 'N', 'x', 'y', 'X', 'Y', 't']}
        # TODO: add missing definitions

        self.parsed = {}
        for c in self.commands:
            self.parsed[c] = []

        self._parse(filename)

    @staticmethod
    def _add_item(d, key, item):
        """
        Add an item to a dictionary key. Queue items in a list when necessary.

        :param d: dictionary
        :param key: dictionary key, needs not to be present in d
        :param item: item to add
        """
        if key not in d:
            d[key] = item
        elif type(d[key]) is not list:
            d[key] = [d[key], item]
        else:
            d[key].append(item)

    def _parse(self, filename):
        with open(filename) as fr:
            i = 1
            for line in fr:
                line = line.strip()
                if not line:
                    continue
                c = line[0]
                if c in self.commands:
                    sub_command = {}
                    for subc in line.split(' ')[1:]:
                        # handles subcommands up to length of 3
                        if subc == '':
                            continue
                        elif (len(subc) >= 1) and (subc[0] in self.commands[c]):
                            self._add_item(sub_command, subc[0], subc[1:])
                        elif (len(subc) >= 2) and (subc[0:2] in self.commands[c]):
                            self._add_item(sub_command, subc[0:2], subc[2:])
                        elif (len(subc) >= 3) and (subc[0:3] in self.commands[c]):
                            self._add_item(sub_command, subc[0:3], subc[3:])
                        else:
                            self._add_item(sub_command, 'unknown', subc)
                    self.parsed[c].append(sub_command)
                elif c == '#':
                    pass
                else:
                    print('Unknown command on line ' + str(i) + ': ' + line)
                i += 1

    def get_input_files(self):
        """
        Get list of input files.

        :return: input filenames
        :rtype: list
        """
        return [input['n'].strip('"') for input in self.parsed['i']]

    def get_correspondences(self, image1, image2):
        """
        Get correspondences for pairs of images.

        :param image1: image index, see get_input_files()
        :param image2: image index
        :return: point coordinates for both images ([[x1, y1], [x2, y2], ...], [[X1, Y1], [X2, Y2], ...])
        :rtype: tuple of list of lists
        """
        corr1 = []
        corr2 = []
        for c in self.parsed['c']:
            if c['n'] == str(image1) and c['N'] == str(image2):
                corr1.append([float(c['x']), float(c['y'])])
                corr2.append([float(c['X']), float(c['Y'])])
        return corr1, corr2

    def get_correspondences_ndarray(self, image1, image2):
        import numpy as np
        c1, c2 = self.get_correspondences(image1, image2)
        return np.array(c1).T, np.array(c2).T

    def get_available_correspondence_pairs(self):
        """
        Get list of pairs of input images with correspondence(s) defined.

        Pairs [0, 1] and [1, 0] are understand as different.

        :return: list of indices pairs
        :rtype: list of lists
        """
        pairs = []
        for c in self.parsed['c']:
            pair = [int(c['n']), int(c['N'])]
            if pair not in pairs:
                pairs.append(pair)
        return pairs
