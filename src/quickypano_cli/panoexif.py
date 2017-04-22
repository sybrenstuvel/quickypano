import subprocess


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Sets panoramic EXIF tags on JPEG files.')
    parser.add_argument('files', metavar='FILENAME', type=str, help='the filenames', nargs='+')
    args = parser.parse_args()

    cmd = [
        'exiftool',
        '-overwrite_original',
        '-ProjectionType=equirectangular',
        '-UsePanoramaViewer=True',
        "-StitchingSoftware=Dr. Sybren's QuickyPano",
        '-CroppedAreaImageWidthPixels<$ImageWidth',
        '-CroppedAreaImageHeightPixels<$ImageHeight',
        '-FullPanoWidthPixels<$ImageWidth',
        '-FullPanoHeightPixels<$ImageHeight',
        '-CroppedAreaLeftPixels=0',
        '-CroppedAreaTopPixels=0',
    ]

    subprocess.check_call(cmd + args.files)


if __name__ == '__main__':
    main()
