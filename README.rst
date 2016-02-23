===============================
QuickyPano
===============================

Simple (well, for me) panorama project creator for Hugin, aimed at
360/180 degree panoramas

* Free software: GPL license v2.0

Project structure
==================================================

QuickyPano expects a certain project structure for it to work:

top-level dir:
    Contains the PTO files.
`jpeg`:
    Contains JPEG files, which are the basis for the `qp_create`
    command. These are used to do the control point finding and
    alignment.
`tiff`:
    Contains optional TIFF files with higher quality versions of the
    JPEG images. These are optionally used for the final stitching to
    ensure the highest quality in the final output.


CLI commands
==================================================

qp_create:
    Creates the Hugin PTO file.

qp_stitch:
    Stitches the Hugin PTO file.

qp_switch:
    Switches the PTO file between JPEG and TIFF images, so you can
    quickly align & tweak the panorama using the JPEGs, and when
    everything is ready switch over to high-quality TIFFs for the best
    result.

