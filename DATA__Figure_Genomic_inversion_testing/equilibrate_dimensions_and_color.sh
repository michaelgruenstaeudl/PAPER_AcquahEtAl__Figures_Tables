#!/usr/bin/env bash

images=(
    GEL_Inv1.jpeg
    GEL_Inv3.jpeg
    GEL_Inv5.jpeg
    GEL_Inv6.jpeg
)

# Find minimum height
min_h=$(identify -format "%h\n" "${images[@]}" | sort -n | head -1)
echo "Target height: $min_h px"

# Find minimum width after scaling to min height
min_w=$(identify -resize x${min_h} -format "%w\n" "${images[@]}" | sort -n | head -1)
echo "Target width: $min_w px"

# Scale all images to exact dimensions, convert to grayscale, equilibrate tones, and sharpen
for img in "${images[@]}"; do
    convert "$img" -resize x${min_h} -resize "${min_w}x${min_h}!" -colorspace Gray -auto-level -sharpen 0x1.0 "scaled_${img}"
    echo "Saved: scaled_${img}"
done
