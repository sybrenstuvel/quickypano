"""
Hugin file support
"""

import os
import os.path
import subprocess
import sys
import distutils.spawn

_cpfind = None
_pto_var = None
_stitch = None
_pto2mk = None
_make = None

redirect_out = subprocess.DEVNULL


def set_debugging(debugging: bool):
    global redirect_out

    if debugging:
        redirect_out = None
    else:
        redirect_out = subprocess.DEVNULL


def set_hugin_bindir(dirname: str):
    global _cpfind, _pto_var, _stitch, _pto2mk, _make

    ext = '.exe' if sys.platform == 'win32' else ''

    _cpfind = os.path.join(dirname, 'cpfind' + ext)
    _pto_var = os.path.join(dirname, 'pto_var' + ext)
    _stitch = os.path.join(dirname, 'hugin_stitch_project' + ext)
    _pto2mk = os.path.join(dirname, 'pto2mk' + ext)
    _make = os.path.join(dirname, 'make' + ext)


def find_hugin(dirname: str='c:/Program Files*/Hugin'):
    """Finds Hugin, then calls set_hugin_bindir(found dir)."""

    import glob

    if sys.platform == 'win32':
        exes = glob.glob(os.path.join(dirname, 'bin/hugin.exe'))
        if not exes:
            raise RuntimeError('Unable to find hugin.exe in %s' % dirname)

        bindir = os.path.dirname(exes[0])
    else:
        exename = distutils.spawn.find_executable('hugin')
        bindir = os.path.dirname(exename)

    set_hugin_bindir(bindir)


def write_header(outfile, project):
    print('''# hugin project file
#hugin_ptoversion 2
p f2 w8192 h4096 v360 k0 E%f R0 n"TIFF_m c:LZW r:CROP"
m g1 i0 f0 m2 p0.00784314
''' % project.average_ev, file=outfile)


IMAGE_PARAM_ORDER = ('w h f v Ra Rb Rc Rd Re Eev Er Eb '
                     'r p y TrX TrY TrZ j a b c d e g t Va Vb Vc Vd '
                     'Vx Vy Vm').split()


def write_images(outfile, project):
    print('# image lines', file=outfile)

    for idx, image in enumerate(project.photos):
        disabled = '' if idx % project.stack_size == 0 else ' disabled'

        params = ['%s%s' % (key, image.parameters[key]) for key in IMAGE_PARAM_ORDER]
        print('#-hugin  cropFactor=1%s' % disabled, file=outfile)
        print('i %s n"%s"' % (' '.join(params), image.filename), file=outfile)


def write_footer(outfile, project):
    control_points = os.linesep.join(project.control_points)

    params = {
        'control_points': control_points,
        'hugin_outputLDRBlended': str(not project.is_hdr).lower(),
        'hugin_outputLDRExposureBlended': str(project.is_hdr).lower(),
    }

    print('''


# specify variables that should be optimized
v


# control points
%(control_points)s

#hugin_optimizeReferenceImage 0
#hugin_blender enblend
#hugin_remapper nona
#hugin_enblendOptions --no-ciecam
#hugin_enfuseOptions
#hugin_hdrmergeOptions -m avg -c
#hugin_outputLDRBlended %(hugin_outputLDRBlended)s
#hugin_outputLDRLayers false
#hugin_outputLDRExposureRemapped false
#hugin_outputLDRExposureLayers false
#hugin_outputLDRExposureBlended %(hugin_outputLDRExposureBlended)s
#hugin_outputLDRStacks false
#hugin_outputLDRExposureLayersFused false
#hugin_outputHDRBlended false
#hugin_outputHDRLayers false
#hugin_outputHDRStacks false
#hugin_outputLayersCompression LZW
#hugin_outputImageType tif
#hugin_outputImageTypeCompression LZW
#hugin_outputJPEGQuality 90
#hugin_outputImageTypeHDR exr
#hugin_outputImageTypeHDRCompression LZW
#hugin_outputStacksMinOverlap 0.7
#hugin_outputLayersExposureDiff 0.5
#hugin_optimizerMasterSwitch 6
#hugin_optimizerPhotoMasterSwitch 20

''' % params, file=outfile)


def write(outfile, project):
    write_header(outfile, project)
    write_images(outfile, project)
    write_footer(outfile, project)


def pto_var(input_filename, output_filename):
    subprocess.check_call([_pto_var,
                           input_filename,
                           '-o', output_filename,
                           '--opt', 'y,p,r,v,Eev'],
                          stdout=redirect_out,
                          stderr=redirect_out)


def cpfind(input_filename, output_filename):
    subprocess.check_call([_cpfind,
                           input_filename,
                           '-o', output_filename],
                          stdout=redirect_out,
                          stderr=redirect_out)


def pto2mk(pto_filename) -> str:
    mk_filename = pto_filename + '.mk'
    prefix = pto_filename.replace('.pto', '')

    subprocess.check_call([_pto2mk,
                           '-p', prefix,
                           '-o', mk_filename,
                           pto_filename])

    return mk_filename


def stitch_project(pto_filename):
    if not pto_filename.endswith('.pto'):
        raise ValueError('pto_filename should end in ".pto"')

    prefix = pto_filename.replace('.pto', '')
    # hugin_stitch_project.exe /w 1_terras.pto /o 1_terras_fused
    subprocess.check_call([_stitch,
                           '/w', pto_filename,
                           '/o', prefix])


def make(pto_filename, make_args=None, on_gpu=False):
    makefile = pto2mk(pto_filename)

    if make_args is None:
        make_args = []

    args = [_make, 'ENBLEND=enblend --no-ciecam', '-f', makefile]
    if on_gpu:
        args += ['NONA=nona -t 1 -g', '-j4']
    else:
        args += ['NONA=nona -t 1', '-j8']

    subprocess.check_call(args + make_args)
