#!/usr/bin/env bash

images=(
    GEL_Inv1.jpeg
    GEL_Inv3.jpeg
    GEL_Inv5.jpeg
    GEL_Inv6.jpeg
)

# --------------------------------------------------
# Determine smallest height
# --------------------------------------------------
min_h=100000

for img in "${images[@]}"; do

    h=$(identify -format "%h" "$img")

    echo "$img height: $h"

    if [ "$h" -lt "$min_h" ]; then
        min_h=$h
    fi
done

echo
echo "Target height: $min_h px"

# --------------------------------------------------
# Scale all images to same height
# --------------------------------------------------
scaled_images=()

for img in "${images[@]}"; do

    scaled="scaled_${img}"

    convert "$img" \
        -resize x${min_h} \
        "$scaled"

    scaled_images+=("$scaled")

    echo "Created: $scaled"
done

# --------------------------------------------------
# Determine smallest width after scaling
# --------------------------------------------------
min_w=100000

for img in "${scaled_images[@]}"; do

    w=$(identify -format "%w" "$img")

    echo "$img width after scaling: $w"

    if [ "$w" -lt "$min_w" ]; then
        min_w=$w
    fi
done

echo
echo "Target width after scaling: $min_w px"

# --------------------------------------------------
# Center-crop width only
# --------------------------------------------------
for img in "${scaled_images[@]}"; do

    out="cropped_${img}"

    convert "$img" \
        -gravity center \
        -crop "${min_w}x${min_h}+0+0" \
        +repage \
        "$out"

    echo "Saved: $out"
done
