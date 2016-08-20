#!/usr/bin/env python

from pprint import pprint
import argparse
import collections
import itertools
import re
from pathlib import Path
import subprocess

import exifread

from quickypano import huginpto

SourceImage = collections.namedtuple(
    'SourceImage',
    ('ev', 'fname', 'sspeed', 'exposure', 'aperture', 'fnumber', 'iso', 'exposure_bias'))
TagImage = collections.namedtuple('TagImage', ('source_index', 'darkened_by', 'fname'))
tag_image_re = re.compile(r'_(?P<source_index>[0-9]+)(-(?P<darkened_by>[0-9]))?\.[a-z]+$')


def parse_cli() -> (Path, [Path], int):
    """Parses the CLI arguments.

    :returns: (PTO filename, [file to tag, file to tag, ...], ev-offset)
    """

    parser = argparse.ArgumentParser(description='Sets EXIF data on output .')
    parser.add_argument('-f', '--filename', metavar='PTO', type=str,
                        nargs='?',
                        help='The PTO filename. Optional if there is only one PTO file.')
    parser.add_argument('-e', '--ev-offset', metavar='EV', type=int,
                        nargs='?',
                        help='EV-offset for all photos; positive numbers result in darker HDRs.')
    parser.add_argument('files_to_tag', type=str, help='Files to change the EXIF of.', nargs='+')
    args = parser.parse_args()

    if not args.filename:
        ptos = list(Path('.').glob('*.pto'))
        if len(ptos) != 1:
            raise SystemExit("Found %i PTO files, don't know what to do!" % len(ptos))
        pto = ptos[0]
    else:
        pto = Path(args.filename)

    if not pto.exists():
        raise SystemExit('File %s does not exist.' % pto)

    return pto, [Path(fname) for fname in args.files_to_tag], args.ev_offset or 0


def parse_pto(pto_fname: Path) -> [SourceImage]:
    pto = huginpto.HuginPto(str(pto_fname))

    # Parse only the first HDR stack.
    source_images = []
    for img in pto.parsed['i']:
        if source_images and not img['y'].startswith('='):
            # This is the start of the next stack; we're done.
            break

        fname = Path(img['n'].strip('"'))

        # Parse EXIF of source image
        with fname.open('rb') as infile:
            exif = exifread.process_file(infile, details=False)
        # pprint(sorted(exif.keys()))

        simg = SourceImage(
            ev=img['Eev'],
            fname=fname,
            sspeed=exif['EXIF ShutterSpeedValue'].values[0],
            exposure=exif['EXIF ExposureTime'].values[0],
            aperture=exif['EXIF ApertureValue'].values[0],
            fnumber=exif['EXIF FNumber'].values[0],
            iso=exif['EXIF ISOSpeedRatings'].values[0],
            exposure_bias=exif['EXIF ExposureBiasValue'].values[0],
        )
        source_images.append(simg)

    return source_images


def find_tag_images(files_to_tag: [Path]) -> [TagImage]:
    """Finds images to tag."""

    tag_images = []
    for fname in files_to_tag:
        m = tag_image_re.search(fname.name)
        if not m:
            raise ValueError('Filename %s does not match expected pattern',
                             fname.name)
        timg = TagImage(
            source_index=int(m.group('source_index'), 10),
            darkened_by=int(m.group('darkened_by') or '1', 10) - 1,
            fname=fname
        )
        tag_images.append(timg)

    return tag_images


def main():
    pto, files_to_tag, ev_offset = parse_cli()

    source_images = parse_pto(pto)
    tag_images = find_tag_images(files_to_tag)

    pprint(source_images)
    # pprint(tag_images)

    for timg in tag_images:
        simg = source_images[timg.source_index]

        sspeed = simg.sspeed
        exposure = simg.exposure
        exposure_bias = (simg.exposure_bias.num / simg.exposure_bias.den)
        if timg.darkened_by or ev_offset:
            offset = timg.darkened_by - ev_offset
            # We have to update the shutter speed & exposure values.
            # sspeed is in logarithmic scale, so we can just add the denominator.
            sspeed = exifread.utils.Ratio(sspeed.num + offset * sspeed.den, sspeed.den)
            # exposure is in linear scale.
            exposure = exifread.utils.Ratio(exposure.num, exposure.den * 2 ** offset)
            exposure_bias -= offset

        # Update the image's EXIF information
        cmd = ['exiftool',
               '-overwrite_original_in_place',
               '-ShutterSpeedValue=%s' % sspeed,
               '-ExposureTime=%s' % exposure,
               '-ApertureValue=%s' % simg.fnumber,  # exiftool converts to APEX itself.
               '-FNumber=%s' % simg.fnumber,
               '-ISO=%s' % simg.iso,
               '-ExposureCompensation=%i' % exposure_bias,
               str(timg.fname),
               ]
        print(cmd)
        subprocess.check_call(cmd)
