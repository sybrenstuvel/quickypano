#!/usr/bin/env python

import argparse
import glob
import time
import os.path

import quickypano.hugin


def main():
    """Makes a PTO file."""

    start_time = time.time()

    parser = argparse.ArgumentParser(description='Renders a panorama using "make".')
    parser.add_argument('--hugin', metavar='HUGIN_DIR', type=str, help="Hugin's directory",
                        default=r'c:\Program Files*\Hugin')
    parser.add_argument('--gpu', help="Run Nona on the GPU",
                        default=False, action='store_true')
    parser.add_argument('-f', '--filename', metavar='PTO', type=str,
                        nargs='?',
                        help='The PTO filename. Optional there is only one PTO file.')
    parser.add_argument('extra_args', type=str, help='Extra Make arguments', nargs='*')
    args = parser.parse_args()

    quickypano.hugin.find_hugin(args.hugin)

    if not args.filename:
        ptos = glob.glob('*.pto')
        if len(ptos) != 1:
            raise SystemExit("Found %i PTO files, don't know what to do!" % len(ptos))
        pto = ptos[0]
    else:
        pto = args.filename

    if not os.path.exists(pto):
        raise SystemExit('File %s does not exist.' % pto)

    print('Processing %s' % pto)
    quickypano.lowpriority()
    quickypano.hugin.make(pto, on_gpu=args.gpu, make_args=args.extra_args)

    end_time = time.time()

    print(50 * '-')
    duration = end_time - start_time
    str_duration = time.strftime('%H:%M:%S', time.gmtime(duration))
    print('Done! Duration: %s' % str_duration)


if __name__ == '__main__':
    main()
