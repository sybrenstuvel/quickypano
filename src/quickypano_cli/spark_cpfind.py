#!/usr/bin/env python

"""
Run cpfind only on specific image pairs.
"""

import argparse
import glob
import os
import os.path
import random
import time
import threading
import concurrent.futures
import logging
import sys
import math

import quickypano
import quickypano.project
import quickypano.hugin

from quickypano_cli import create_project

PAIRS = {
    0: (1, 4, 5, 43, 45),
    1: (4, 6, 2, 44, 45),
    2: (6, 10, 3, 14, 41, 44),
    3: (10, 14, 26, 37),
    4: (5, 6, 7),
    5: (6, 7, 8),
    6: (7, 9, 10),
    7: (8, 9, 11),
    8: (9, 11, 12),
    9: (10, 11, 13),
    10: (13, 14, 18),
    11: (12, 13, 15),
    12: (13, 15, 16),
    13: (15, 17, 18),
    14: (18, 26, 37),
    15: (16, 17, 19),
    16: (17, 19, 20),
    17: (18, 19, 21),
    18: (21, 25, 26),
    19: (20, 21, 22),
    20: (21, 22, 23),
    21: (22, 24, 25),
    22: (23, 24, 27),
    23: (24, 27, 28),
    24: (25, 27, 29),
    25: (26, 29, 33, 37),
    26: (33, 37),
    27: (28, 29, 30),
    28: (29, 30, 31),
    29: (30, 32, 33),
    30: (31, 32, 34),
    31: (32, 34, 35),
    32: (33, 34, 36),
    33: (36, 37, 41),
    34: (35, 36, 38),
    35: (36, 38, 39),
    36: (38, 40, 41),
    37: (41, ),
    38: (39, 40, 42),
    39: (40, 42, 43),
    40: (41, 42, 44),
    41: (44, ),
    42: (43, 44, 45),
    43: (44, 45),
    44: (45, ),
    45: (),
}


def expand_pairs():
    for a, others in PAIRS.items():
        for other in others:
            yield a, other


def main():
    """Run cpfind only on specific image pairs for DJI Spark."""

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('quickypano')
    log.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description='Creates a 360 Hugin file.')
    parser.add_argument('filename', metavar='FILENAME', type=str, help='the input filename')
    parser.add_argument('--hugin', metavar='HUGIN_DIR', type=str, help="Hugin's directory",
                        default=r'c:\Program Files*\Hugin')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Run single-threaded for easier debuggin')

    args = parser.parse_args()
    assert args.filename.endswith('.pto')

    basedir = os.path.dirname(args.filename)
    if args.debug:
        quickypano.hugin.set_debugging(True)

        # Basic sanity check for the PAIRS variable
        expanded_pairs = list(expand_pairs())
        assert len(expanded_pairs) == len(set(expanded_pairs))

    start_time = time.time()

    # Set up the Hugin module
    quickypano.hugin.find_hugin(args.hugin)

    project = quickypano.project.Project.load(args.filename)
    project_lock = threading.RLock()

    # Find control points
    def find_control_points(idx_0, idx_1):
        if idx_0 > idx_1:
            idx_0, idx_1 = idx_1, idx_0

        pid = os.getpid()
        rdm = random.randint(0, 2 ** 20)

        log.info('Finding control points for images %i -- %i', idx_0, idx_1)

        cpfind_inname = os.path.join(basedir, 'cpfind_in-%i-%i.pto' % (pid, rdm))
        cpfind_outname = os.path.join(basedir, 'cpfind_out-%i-%i.pto' % (pid, rdm))

        clone = project.get_slice([idx_0, idx_1])
        clone.hugin_filename = cpfind_inname
        clone.anchor_exposure = 0
        # clone.set_variables()
        clone.create_hugin_project()

        quickypano.hugin.cpfind(clone.hugin_filename, cpfind_outname)

        # Merge found control points with our project definition
        with open(cpfind_outname, 'r', encoding='utf-8') as infile:
            # Load control points
            for line in infile:
                if not line.startswith('c '):
                    continue

                cpoint_info = line.split()
                cpoint_line = ' '.join(cpoint_info[3:])
                with project_lock:
                    project.control_points.append('c n%i N%i %s' % (idx_0, idx_1, cpoint_line))

        os.unlink(cpfind_inname)
        os.unlink(cpfind_outname)

    def task_done(future):
        exception = future.exception()
        if exception is None:
            return

        import traceback

        lines = traceback.format_exception_only(type(exception), exception)
        log.error('Exception trying to find control points:\n%s', '\n'.join(lines))

    def submit_task(executor, idx0, idx1):
        future = executor.submit(find_control_points, idx0, idx1)
        future.add_done_callback(task_done)

    def find_all_control_points():
        """Find control points based on shooting order by DJI Spark."""

        project.control_points.clear()
        quickypano.lowpriority()

        if args.debug:
            exec_class = create_project.DummyExecutor
        else:
            exec_class = concurrent.futures.ThreadPoolExecutor

        with exec_class(os.cpu_count()) as executor:
            for idx0, idx1 in expand_pairs():
                log.debug('Calling find_control_points(%i, %i)', idx0, idx1)
            submit_task(executor, idx0, idx1)

        sys.stderr.flush()
        sys.stdout.flush()
        quickypano.normalpriority()

        log.info('Found a total of %i control points', len(project.control_points))

    if not args.no_cp:
        find_all_control_points()

    # Create Hugin project file
    project.hugin_filename = project.hugin_filename.replace('.pto', '-sparked.pto')
    project.create_hugin_project()

    end_time = time.time()
    log.info('Total running time: %.1f seconds', end_time - start_time)

    if hasattr(os, 'startfile'):
        os.startfile(project.hugin_filename)


if __name__ == '__main__':
    main()
