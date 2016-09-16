#!/bin/bash -ex

if [ "x$1" == "x" ]; then
    echo "Usage: $0 {base}" >&2
    exit 1
fi

BASE="$1"
IN="tiff/${BASE}*_exposure_*.tif"
OUT="${BASE}.exr"

OPTS="-alpha off -compress zip"
function resize() {
    FROM=$1
    GEOM_X=$2

    CMDS=""
    while [ $GEOM_X -gt 1000 ]; do
        GEOM_Y=$((GEOM_X / 2))

        if [ $GEOM_X -gt $WIDTH ]; then
            echo "Skipping ${GEOM_X}x${GEOM_Y}"
        else
            K=$((GEOM_X / 1000))
            CMDS="$CMDS -resize ${GEOM_X}x${GEOM_Y} -write ${FROM/.exr/-${K}k.exr}"
        fi

        GEOM_X=${GEOM_Y}
    done

    convert "$FROM" $OPTS $CMDS "null:"
}

qp_exif $IN
luminance-hdr-cli --save $OUT --config weight=gaussian:response_curve=gamma $IN
echo "Created $OUT"

WIDTH=$(identify -format %w $OUT)

resize ${OUT} 16384

luminance-hdr-cli \
    --tmo reinhard02 \
    --tmoptions key=0.08:phi=0 \
    --quality 85 \
    --resize 2048 \
    --output ${OUT/.exr/-preview.jpg} \
    --load $OUT

luminance-hdr-cli \
    --tmo reinhard02 \
    --tmoptions key=0.08:phi=0 \
    --quality 85 \
    --output ${OUT/.exr/.jpg} \
    --load $OUT

# exrstats $OUT
