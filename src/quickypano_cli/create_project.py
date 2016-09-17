#!/usr/bin/env python

"""
Simple Hugin project generator.
"""

import glob
import argparse
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


class DummyExecutor:
    def __init__(self, nr_of_threads=None):
        self.queue = []

    def submit(self, callable, *args):
        self.queue.append((callable, args))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False

        for callable, args in self.queue:
            callable(*args)


def main():
    """Creates a Hugin project."""

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('quickypano')
    log.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description='Creates a 360 Hugin file.')
    parser.add_argument('filename', metavar='FILENAME', type=str, help='the output filename')
    parser.add_argument('--hugin', metavar='HUGIN_DIR', type=str, help="Hugin's directory",
                        default=r'c:\Program Files*\Hugin')
    parser.add_argument('-o', '--hdr-offset', type=int,
                        help="Which photo to pick for CPFind (-1 = middle of stack)",
                        default=-1)
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Run single-threaded for easier debuggin')
    parser.add_argument('--no-cp', action='store_true', default=False,
                        help="Don't find control points")

    args = parser.parse_args()
    basedir = os.path.dirname(args.filename)
    if args.debug:
        quickypano.hugin.set_debugging(True)

    start_time = time.time()

    # Set up the Hugin module
    quickypano.hugin.find_hugin(args.hugin)

    # Create project definition
    photo_glob_lc = os.path.normpath(os.path.join(basedir, 'jpeg/*.jpg'))
    if sys.platform == 'win32':
        photo_fnames = [fn.replace('\\', '/') for fn in glob.glob(photo_glob_lc)]
    else:
        photo_glob_uc = os.path.normpath(os.path.join(basedir, 'jpeg/*.JPG'))
        photo_fnames = glob.glob(photo_glob_lc) + glob.glob(photo_glob_uc)

    project = quickypano.project.Project()
    project.load_photos(photo_fnames)
    project.hugin_filename = args.filename

    # Detect HDR stack size.
    nr_of_photos = len(project.photos)
    for stack_size in (7, 5, 3, 1):
        if nr_of_photos % stack_size == 0:
            project.stack_size = stack_size
            break
    else:
        raise ValueError('Unable to handle %i photos, alter source to support.' % nr_of_photos)

    if project.stack_size > 1:
        print('Detected HDR; ', end='')
    else:
        print('Detected LDR; ', end='')
    print('stack size is %i' % project.stack_size)

    # Choose HDR offset.
    if args.hdr_offset < 0:
        args.hdr_offset = math.floor(project.stack_size / 2)
    print('Using HDR offset %i' % args.hdr_offset)

    project.move_anchor(args.hdr_offset)
    project.set_variables()

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

    def find_cpoints_for_ring(ring_size, ring_offset, executor):
        ring_offset *= project.stack_size

        for stack_idx in range(ring_size):
            next_stack_idx = (stack_idx + 1) % ring_size
            idx = project.stack_size * stack_idx
            next_idx = project.stack_size * next_stack_idx

            log.debug('Calling find_control_points(%i, %i)', idx + ring_offset,
                      next_idx + ring_offset)
            submit_task(executor, idx + ring_offset, next_idx + ring_offset)

    def connect_rings(name1, name2, executor):
        """Determine suitable divisor for inter-ring connections."""

        sett = project.settings

        row_size1 = sett.row(name1)
        row_size2 = sett.row(name2)
        if row_size1 == row_size2:
            # All the same size, divide into quarters
            gcd = 4
        else:
            gcd = math.gcd(row_size1, row_size2)

        log.debug('using gcd: %r', gcd)
        step1 = row_size1 // gcd
        step2 = row_size2 // gcd

        start_idx1 = sett.start_offset(name1)
        start_idx2 = sett.start_offset(name2)
        ssize = project.stack_size

        for stepidx in range(gcd):
            idx1 = ssize * (start_idx1 + stepidx * step1)
            idx2 = ssize * (start_idx2 + stepidx * step2)

            log.debug('Connecting rings step %i, connecting %i - %i', stepidx,  idx1, idx2)
            submit_task(executor, idx1, idx2)

    def find_all_control_points():
        # Create control points for each ring
        # TODO: use order from settings
        project.control_points.clear()

        quickypano.lowpriority()

        if args.debug:
            exec_class = DummyExecutor
        else:
            exec_class = concurrent.futures.ThreadPoolExecutor

        with exec_class(os.cpu_count()) as executor:
            sett = project.settings
            find_cpoints_for_ring(sett.ROW_MIDDLE, sett.start_offset('MIDDLE'), executor)
            find_cpoints_for_ring(sett.ROW_DOWN, sett.start_offset('DOWN'), executor)
            find_cpoints_for_ring(sett.ROW_UP, sett.start_offset('UP'), executor)

            # Connect rings
            connect_rings('MIDDLE', 'DOWN', executor)
            connect_rings('MIDDLE', 'UP', executor)

            # TODO: zenith & nadir shots

        sys.stderr.flush()
        sys.stdout.flush()
        quickypano.normalpriority()

        log.info('Found a total of %i control points', len(project.control_points))

    if not args.no_cp:
        find_all_control_points()

    # Create Hugin project file
    project.create_hugin_project()

    end_time = time.time()
    log.info('Total running time: %.1f seconds', end_time - start_time)

    if hasattr(os, 'startfile'):
        os.startfile(project.hugin_filename)


if __name__ == '__main__':
    main()
