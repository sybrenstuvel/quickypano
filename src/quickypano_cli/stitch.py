#!/usr/bin/env python

import glob
import argparse
import time
import quickypano.hugin


def main():
    """Stitches a single project."""

    parser = argparse.ArgumentParser(description='Switches a Hugin file to different input files.')
    parser.add_argument('--hugin', metavar='HUGIN_DIR', type=str, help="Hugin's directory", nargs='?')
    parser.add_argument('filename', metavar='FILENAME', type=str, help='the PTO filename', nargs='?')

    args = parser.parse_args()
    quickypano.hugin.find_hugin(args.hugin)

    start_time = time.time()

    if not args.filename:
        ptos = glob.glob('*.pto')
        if len(ptos) != 1:
            raise SystemExit("Found %i PTO files, don't know what to do!" % len(ptos))

        args.filename = ptos[0]

    quickypano.hugin.stitch_project(args.filename)

    end_time = time.time()

    print(50 * '-')
    duration = end_time - start_time
    str_duration = time.strftime('%H:%M:%S', time.gmtime(duration))
    print('Stitching done! Duration: %s' % str_duration)


if __name__ == '__main__':
    main()
