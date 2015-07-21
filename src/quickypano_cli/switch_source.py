#!/usr/bin/env python

"""
Switches source images between JPEG and TIFF.
"""

import argparse
import os
import re
import quickypano.hugin

FTYPES = {
    'TIFF': {'path': 'tiff16', 'extension': 'tif'},
    'JPEG': {'path': 'jpeg', 'extension': 'jpg'},
}


def main():
    """Switches source images between JPEG and TIFF."""

    parser = argparse.ArgumentParser(description='Switches a Hugin file to different input files.')
    parser.add_argument('filename', metavar='FILENAME', type=str, help='the PTO filename')
    parser.add_argument('-t', type=str,
                        choices=sorted(FTYPES.keys()),
                        dest='filetype',
                        default='TIFF',
                        help='Type to switch to')
    parser.add_argument('--hugin', metavar='HUGIN_DIR', type=str, help="Hugin's directory",
                        default=r'c:\Program Files*\Hugin')

    args = parser.parse_args()
    quickypano.hugin.find_hugin(args.hugin)

    print('Switching %s to %s' % (args.filename, args.filetype))
    fname_re = re.compile(r'n"\w+[/\\](\w+)\.\w+"')
    ftype = FTYPES[args.filetype]
    target = r'n"%s/\1.%s"' % (ftype['path'], ftype['extension'])

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

    print('Creating %s.mk' % args.filename)
    quickypano.hugin.pto2mk(args.filename)

    print('Done!')


if __name__ == '__main__':
    main()
