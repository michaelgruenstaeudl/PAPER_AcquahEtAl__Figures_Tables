### Visualization of 16S rRNA metagenomic results across samples

#### Subplot a: Genetic diversity
This script visualizes the metagenomic diversity across different samples at different taxonomic levels.

```bash
DATDIR="DATA__Figure_16S_rRNA_metagenomics"
OUTDIR="VIZ__Figure_16S_rRNA_metagenomics"

python SCRIPT__vertically_stacked_taxonomy_barcharts.py \
    $DATDIR/ \
    -o $OUTDIR/Fig_16S_rRNA_metagenomics \
    -t 1 \
    --metadata $DATDIR/metadata__genus-table.csv
```

#### Subplot b: Diversity indices
This script visualizes the diversity indices across different samples.

```bash
DATDIR="DATA__Figure_16S_rRNA_metagenomics"
OUTDIR="VIZ__Figure_16S_rRNA_metagenomics"

python SCRIPT__horizontally_stacked_diversity_index_barcharts.py \
    $DATDIR/ \
    -o $OUTDIR/Fig_16S_rRNA_diversityIndices \
    --metadata $DATDIR/metadata__METRICS.csv
```

#### Combining subplots

```bash
pip install svgutils
pip install cairosvg

OUTDIR="VIZ__Figure_16S_rRNA_metagenomics"

python - <<PY
from svgutils.compose import Figure, SVG, Text
import xml.etree.ElementTree as ET
import cairosvg

def get_size(svgfile):
    root = ET.parse(svgfile).getroot()
    width = float(root.attrib["width"].replace("pt","").replace("px",""))
    height = float(root.attrib["height"].replace("pt","").replace("px",""))
    return width, height

svg1 = "${OUTDIR}/Fig_16S_rRNA_metagenomics.svg"
svg2 = "${OUTDIR}/Fig_16S_rRNA_diversityIndices.svg"

w1, h1 = get_size(svg1)
w2, h2 = get_size(svg2)

target_width = 1000

scale1 = target_width / w1
scale2 = target_width / w2

new_h1 = h1 * scale1
new_h2 = h2 * scale2
title_band = 12

section1_y = 0
section1_image_y = section1_y + title_band

section2_y = section1_image_y + new_h1
section2_image_y = section2_y + title_band

combined_height = section2_image_y + new_h2

combined_svg = "${OUTDIR}/Fig_16S_rRNA__COMBINED.svg"
combined_png = "${OUTDIR}/Fig_16S_rRNA__COMBINED.png"
combined_pdf = "${OUTDIR}/Fig_16S_rRNA__COMBINED.pdf"

Figure(
    f"{target_width}px",
    f"{combined_height}px",

    SVG(svg1).scale(scale1).move(0, section1_image_y),
    SVG(svg2).scale(scale2).move(0, section2_image_y),
    Text("A", 0, section1_image_y + 12, size=20, weight="bold"),
    Text("B", 0, section2_image_y + 12, size=20, weight="bold")

).save(combined_svg)

# Ensure the SVG itself has an opaque white background.
tree = ET.parse(combined_svg)
root = tree.getroot()
bg = ET.Element(
    "{http://www.w3.org/2000/svg}rect",
    {
        "x": "0",
        "y": "0",
        "width": "100%",
        "height": "100%",
        "fill": "white",
    },
)
root.insert(0, bg)
tree.write(combined_svg, encoding="utf-8", xml_declaration=True)


# Also enforce white when rasterizing to PNG.
cairosvg.svg2png(url=combined_svg, write_to=combined_png, background_color="white")

# Save a vector PDF copy.
cairosvg.svg2pdf(url=combined_svg, write_to=combined_pdf)

PY
```
