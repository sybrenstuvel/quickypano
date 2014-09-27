#!/usr/bin/env python

import glob
import time

import quickypano.hugin


def main():
    """Creates PTO.MK files for all PTO files."""

    start_time = time.time()

    quickypano.hugin.find_hugin()

    ptos = glob.glob('*.pto')
    if len(ptos) == 0:
        raise SystemExit("Found %i PTO files, don't know what to do!" % len(ptos))

    for pto in ptos:
        print('Processing %s' % pto)
        quickypano.hugin.pto2mk(pto)

    end_time = time.time()

    print(50 * '-')
    duration = end_time - start_time
    str_duration = time.strftime('%H:%M:%S', time.localtime(duration))
    print('Done! Duration: %s' % str_duration)


if __name__ == '__main__':
    main()
