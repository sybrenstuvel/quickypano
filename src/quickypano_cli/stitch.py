#!/usr/bin/env python

import glob
import subprocess
import time
from quickypano import hugin


def main():
    """Stitches a single project."""

    start_time = time.time()

    ptos = glob.glob('*.pto')
    if len(ptos) != 1:
        raise SystemExit("Found %i PTO files, don't know what to do!" % len(ptos))

    pto = ptos[0]
    hugin.stitch_project(pto)

    end_time = time.time()

    print(50 * '-')
    duration = end_time - start_time
    str_duration = time.strftime('%H:%M:%S', time.localtime(duration))
    print('Stitching done! Duration: %s' % str_duration)


if __name__ == '__main__':
    main()
