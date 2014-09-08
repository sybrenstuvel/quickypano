#!/usr/bin/env python

import glob
import subprocess
import time


def main():
    """Stitches a single project."""

    start_time = time.time()

    exes = glob.glob('c:/Program Files*/Hugin/bin/hugin_stitch_project.exe')
    if not exes:
        raise SystemExit('Unable to find hugin_stitch_project.exe')
    exe = exes[0]

    ptos = glob.glob('*.pto')
    if len(ptos) != 1:
        raise SystemExit("Found %i PTO files, don't know what to do!" % len(ptos))

    pto = ptos[0]
    prefix = pto.replace('.pto', '')
    assert pto != prefix

    subprocess.check_call([exe,
        '/w', pto,
        '/o', prefix
    ])

    end_time = time.time()

    print(50 * '-')
    duration = end_time - start_time
    str_duration = time.strftime('%H:%M:%S', time.localtime(duration))
    print('Stitching done! Duration: %s' % str_duration)


if __name__ == '__main__':
    main()
