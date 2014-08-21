"""
Simple Hugin project generator.
"""

import glob
import argparse
import os
import os.path
import time

import panoflops.project
import panoflops.hugin

parser = argparse.ArgumentParser(description='Creates a 360 Hugin file.')
parser.add_argument('filename', metavar='FILENAME', type=str, help='the output filename')
parser.add_argument('--hugin_bin', metavar='HUGIN_BINDIR', type=str, help="Hugin's bin directory",
                    default=r'c:\Program Files\Hugin\bin')

args = parser.parse_args(
    [r'J:\2014\2014-08-xx Vakantie Kroatie\Haus am Berg panos\1. terras\1_terras.pto'])
basedir = os.path.dirname(args.filename)

start_time = time.time()

# Set up the Hugin module
panoflops.hugin.set_hugin_bindir(args.hugin_bin)

# Create project definition
photo_glob = os.path.normpath(os.path.join(basedir, 'jpeg/*.jpg'))
print('Getting photos from %s' % photo_glob)

project = panoflops.project.Project()
project.load_photos(glob.glob(photo_glob))
project.hugin_filename = args.filename

nr_of_photos = len(project.photos)
if nr_of_photos == 84:
    print('Detected HDR')
    project.is_hdr = True
elif nr_of_photos == 28:
    print('Detected LDR')
    project.is_hdr = False
    raise SystemExit('LDR not supported yet')
else:
    raise ValueError('Unable to handle %i photos, should be 84 or 28' % nr_of_photos)

project.set_variables()


# Find control points
def find_control_points(idx_0, idx_1):
    if idx_0 > idx_1:
        idx_0, idx_1 = idx_1, idx_0

    print('Finding control points for images %i -- %i' % (idx_0, idx_1))

    cpfind_inname = os.path.join(basedir, 'cpfind_in.pto')
    cpfind_outname = os.path.join(basedir, 'cpfind_out.pto')

    clone = project.get_slice([idx_0, idx_1])
    clone.hugin_filename = cpfind_inname
    clone.create_hugin_project()

    panoflops.hugin.cpfind(clone.hugin_filename, cpfind_outname)

    with open(cpfind_outname, 'r', encoding='utf-8') as infile:
        # Load control points
        for line in infile:
            if not line.startswith('c '):
                continue

            # Strip the 'c n0 N1 ' prefix, as it's always the same anyway
            cpoint_info = line[8:].strip()
            project.control_points.append('c n%i N%i %s' % (idx_0, idx_1, cpoint_info))


def find_cpoints_for_ring(ring_size, ring_offset):
    if project.is_hdr:
        ring_offset *= 3
    for idx in range(ring_size):
        next_idx = (idx + 1) % ring_size
        if project.is_hdr:
            idx *= 3
            next_idx *= 3
        find_control_points(idx + ring_offset, next_idx + ring_offset)

# Create control points for each ring
# TODO: use order from settings
find_cpoints_for_ring(project.settings.ROW_MIDDLE, 0)
find_cpoints_for_ring(project.settings.ROW_DOWN,
                      project.settings.ROW_MIDDLE)
find_cpoints_for_ring(project.settings.ROW_UP,
                      project.settings.ROW_DOWN + project.settings.ROW_MIDDLE)

# Create Hugin project file
project.create_hugin_project()

end_time = time.time()
print('Total running time: %.1f seconds' % (end_time - start_time))
