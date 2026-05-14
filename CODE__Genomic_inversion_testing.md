### Visualization of the principle and results of genomic inversion testing

#### Subplot a: Diagram
This script generates a diagram of the genomic inversion tests using matplotlib

```bash
OUTDIR="VIZ__Figure_Genomic_inversion_testing"

python SCRIPT__create_genomic_inversion_diagram.py \
    -o $OUTDIR/Fig_Genomic_inversion_subplotA_SCHEMATIC
```

#### Subplot b: Arranging and labelling the gel images
This script arranges and labels the gel images

```bash
DATDIR="DATA__Figure_Genomic_inversion_testing"
OUTDIR="VIZ__Figure_Genomic_inversion_testing"

python SCRIPT__arrange_gel_images_in_panel.py \
    -i $DATDIR/ \
    -o $OUTDIR/Fig_Genomic_inversion__subplotB__GELIMAGE_PANEL
```


#### Combining subplots

```bash
pip install svgutils
pip install cairosvg

OUTDIR="VIZ__Figure_Genomic_inversion_testing"

python - <<PY
from svgutils.compose import Figure, SVG, Text
import xml.etree.ElementTree as ET
import cairosvg

def get_size(svgfile):
    root = ET.parse(svgfile).getroot()
    width = float(root.attrib["width"].replace("pt","").replace("px",""))
    height = float(root.attrib["height"].replace("pt","").replace("px",""))
    return width, height

svg1 = "${OUTDIR}/Fig_Genomic_inversion_subplotA_SCHEMATIC.svg"
svg2 = "${OUTDIR}/Fig_Genomic_inversion__subplotB__GELIMAGE_PANEL.svg"

w1, h1 = get_size(svg1)
w2, h2 = get_size(svg2)

target_width = 1000

scale1 = target_width / w1
scale2 = target_width / w2

new_h1 = h1 * scale1
new_h2 = h2 * scale2
title_band = 30

section1_y = 0
section1_image_y = section1_y + title_band

section2_y = section1_image_y + new_h1
section2_image_y = section2_y + title_band

combined_height = section2_image_y + new_h2

combined_svg = "${OUTDIR}/Fig_Genomic_inversion__COMBINED.svg"
combined_png = "${OUTDIR}/Fig_Genomic_inversion__COMBINED.png"

Figure(
    f"{target_width}px",
    f"{combined_height}px",

    SVG(svg1).scale(scale1).move(0, section1_image_y),
    SVG(svg2).scale(scale2).move(0, section2_image_y),
    Text("(a) Schematic of PCR experiments", 12, section1_y + 22, size=24, weight="bold"),
    Text("(b) PCR results", 12, section2_y + 22, size=24, weight="bold")

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

PY
```