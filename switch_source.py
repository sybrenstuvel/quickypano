#!/usr/bin/env python

"""
Switches source images between JPEG and TIFF.
"""

import argparse
import os
import re

FTYPES = {
    'TIFF': {'path': 'tiff16', 'extension': 'tif'},
    'JPEG': {'path': 'jpeg', 'extension': 'jpg'},
}

parser = argparse.ArgumentParser(description='Switches a Hugin file to different input files.')
parser.add_argument('filename', metavar='FILENAME', type=str, help='the PTO filename')
parser.add_argument('-t', type=str,
                    choices=sorted(FTYPES.keys()),
                    dest='filetype',
                    default='TIFF',
                    help='Type to switch to')

args = parser.parse_args()

print('Switching %s to %s' % (args.filename, args.filetype))
fname_re = re.compile(r'n"\w+[/\\](\w+)\.\w+"')
ftype = FTYPES[args.filetype]
sep = os.sep
if sep == '\\':
    sep = '\\\\'  # Escape for regexps
target = r'n"%s%s\1.%s"' % (ftype['path'], sep, ftype['extension'])

basename = os.path.dirname(args.filename)
outname = os.path.join(basename, 'switch_source-%i.pto' % os.getpid())
print('Writing to %s for now.' % outname)
print('Target: %s' % target)

with open(args.filename, 'r', encoding='utf-8') as infile, \
        open(outname, 'w', encoding='utf-8') as outfile:
    for line in infile:
        if line.startswith('i '):
            line = fname_re.sub(target, line)

        outfile.write(line)

print('Moving %s to %s' % (outname, args.filename))
os.unlink(args.filename)
os.rename(outname, args.filename)
