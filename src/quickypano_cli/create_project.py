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

import quickypano
import quickypano.project
import quickypano.hugin


def main():
    """Creates a Hugin project."""

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('simpleflops')
    log.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description='Creates a 360 Hugin file.')
    parser.add_argument('filename', metavar='FILENAME', type=str, help='the output filename')
    parser.add_argument('--hugin', metavar='HUGIN_DIR', type=str, help="Hugin's directory",
                        default=r'c:\Program Files*\Hugin')
    parser.add_argument('--hdr-offset', type=int, help="Which photo to pick for CPFind",
                        default=0)

    args = parser.parse_args()
    basedir = os.path.dirname(args.filename)

    start_time = time.time()

    # Set up the Hugin module
    quickypano.hugin.find_hugin(args.hugin)

    # Create project definition
    photo_glob = os.path.normpath(os.path.join(basedir, 'jpeg/*.jpg'))
    print('Getting photos from %s' % photo_glob)

    project = quickypano.project.Project()
    project.load_photos(glob.glob(photo_glob))
    project.hugin_filename = args.filename

    nr_of_photos = len(project.photos)
    if nr_of_photos == 84:
        print('Detected HDR; ', end='')
        project.stack_size = 3
    elif nr_of_photos == 28:
        print('Detected LDR; ', end='')
        project.stack_size = 1
    else:
        raise ValueError('Unable to handle %i photos, should be 84 or 28' % nr_of_photos)

    print('stack size is %i' % project.stack_size)
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

    def find_cpoints_for_ring(ring_size, ring_offset, executor):
        ring_offset *= project.stack_size

        for stack_idx in range(ring_size):
            next_stack_idx = (stack_idx + 1) % ring_size
            idx = project.stack_size * stack_idx
            next_idx = project.stack_size * next_stack_idx

            log.debug('Calling find_control_points(%i, %i)', idx + ring_offset, next_idx + ring_offset)
            executor.submit(find_control_points,
                            idx + ring_offset, next_idx + ring_offset)

    def find_all_control_points():
        # Create control points for each ring
        # TODO: use order from settings
        project.control_points.clear()

        quickypano.lowpriority()

        with concurrent.futures.ThreadPoolExecutor(os.cpu_count()) as executor:
            sett = project.settings
            find_cpoints_for_ring(sett.ROW_MIDDLE, 0, executor)
            find_cpoints_for_ring(sett.ROW_DOWN, sett.ROW_MIDDLE, executor)
            find_cpoints_for_ring(sett.ROW_UP, sett.ROW_DOWN + sett.ROW_MIDDLE, executor)

            # ## Attach rings
            # From start of middle to start of the other rings
            ssize = project.stack_size
            down_start_idx = sett.ROW_MIDDLE * ssize
            up_start_idx = (sett.ROW_MIDDLE + sett.ROW_DOWN) * ssize
            executor.submit(find_control_points, 0, down_start_idx)
            executor.submit(find_control_points, 0, up_start_idx)

            # From mid of middle to mid of the other rings
            row_middle_mid = ssize * sett.ROW_MIDDLE // 2
            executor.submit(find_control_points, row_middle_mid,
                            down_start_idx + ssize * sett.ROW_DOWN // 2)
            executor.submit(find_control_points, row_middle_mid,
                            up_start_idx + ssize * sett.ROW_UP // 2)

        sys.stderr.flush()
        sys.stdout.flush()
        quickypano.normalpriority()

        log.info('Found a total of %i control points', len(project.control_points))

    find_all_control_points()

    # Create Hugin project file
    project.create_hugin_project()

    end_time = time.time()
    log.info('Total running time: %.1f seconds', end_time - start_time)

    if hasattr(os, 'startfile'):
        os.startfile(project.hugin_filename)

if __name__ == '__main__':
    main()
