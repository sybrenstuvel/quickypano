"""
Hugin file support
"""

import os
import os.path
import subprocess

_cpfind = None
_pto_var = None
_stitch = None


def set_hugin_bindir(dirname: str):
    global _cpfind, _pto_var, _stitch

    _cpfind = os.path.join(dirname, 'cpfind.exe')
    _pto_var = os.path.join(dirname, 'pto_var.exe')
    _stitch = os.path.join(dirname, 'hugin_stitch_project..exe')


def write_header(outfile, project):

    print('''# hugin project file
#hugin_ptoversion 2
p f2 w6000 h3000 v360 k0 E%f R0 n"TIFF_m c:LZW r:CROP"
m g1 i0 f0 m2 p0.00784314
''' % project.average_ev, file=outfile)


IMAGE_PARAM_ORDER = ('w h f v Ra Rb Rc Rd Re Eev Er Eb '
                     'r p y TrX TrY TrZ j a b c d e g t Va Vb Vc Vd '
                     'Vx Vy Vm').split()


def write_images(outfile, project):
    print('# image lines', file=outfile)

    for idx, image in enumerate(project.photos):
        params = ['%s%s' % (key, image.parameters[key]) for key in IMAGE_PARAM_ORDER]
        print('i %s n"%s"' % (' '.join(params), image.filename), file=outfile)


def write_footer(outfile, project):
    control_points = os.linesep.join(project.control_points)

    print('''


# specify variables that should be optimized
v


# control points
%s

#hugin_optimizeReferenceImage 0
#hugin_blender enblend
#hugin_remapper nona
#hugin_enblendOptions
#hugin_enfuseOptions
#hugin_hdrmergeOptions -m avg -c
#hugin_outputLDRBlended false
#hugin_outputLDRLayers false
#hugin_outputLDRExposureRemapped false
#hugin_outputLDRExposureLayers false
#hugin_outputLDRExposureBlended true
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

''' % control_points, file=outfile)


def write(outfile, project):
    write_header(outfile, project)
    write_images(outfile, project)
    write_footer(outfile, project)


def pto_var(input_filename, output_filename):
    subprocess.check_call([_pto_var,
                           input_filename,
                           '-o', output_filename,
                           '--opt', 'y,p,r,v,Eev'],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)


def cpfind(input_filename, output_filename):
    subprocess.check_call([_cpfind,
                           input_filename,
                           '-o', output_filename],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)


def stitch_project(pto_filename):
    if not pto_filename.endswith('.pto'):
        raise ValueError('pto_filename should end in ".pto"')

    prefix = pto_filename.replace('.pto', '')
    # hugin_stitch_project.exe /w 1_terras.pto /o 1_terras_fused
    subprocess.check_call([_stitch,
                           '/w', pto_filename,
                           '/o', prefix])