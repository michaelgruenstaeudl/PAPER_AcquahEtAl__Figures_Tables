#!/usr/bin/env python3

import argparse
import base64
import mimetypes
from pathlib import Path

from PIL import Image
import cairosvg


def parse_args():
    parser = argparse.ArgumentParser(
        description="Arrange six gel images into a labeled 2x3 panel."
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input folder containing the cropped gel JPEG files.",
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output path stem without extension. The script writes .svg and .png files.",
    )

    return parser.parse_args()


def image_to_data_uri(path):
    mime_type = mimetypes.guess_type(path)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def create_diagram(input_folder, output_stem):

    input_folder = Path(input_folder)

    image_files = [
        input_folder / "scaled_GEL_Inv1.jpeg",
        input_folder / "scaled_GEL_Inv2.jpeg",
        input_folder / "scaled_GEL_Inv3.jpeg",
        input_folder / "scaled_GEL_Inv4.jpeg",
        input_folder / "scaled_GEL_Inv5.jpeg",
        input_folder / "scaled_GEL_Inv6.jpeg",
    ]

    labels = [
        "Inversion 1",
        "Inversion 2",
        "Inversion 3",
        "Inversion 4",
        "Inversion 5",
        "Inversion 6",
    ]

    # --------------------------------------------------
    # Validate input
    # --------------------------------------------------
    for f in image_files:

        if not f.exists():
            raise FileNotFoundError(
                f"Missing input image: {f}"
            )

    # --------------------------------------------------
    # Layout parameters
    # --------------------------------------------------
    n_cols = 3
    n_rows = 2

    gap = 60

    label_height = 60
    font_size = 90

    left_label_padding = 8

    margin = 50

    output_svg = f"{output_stem}.svg"
    output_png = f"{output_stem}.png"

    # --------------------------------------------------
    # Read images
    # --------------------------------------------------
    images = [
        Image.open(f)
        for f in image_files
    ]

    panel_w = max(img.width for img in images)
    panel_h = max(img.height for img in images)

    total_panel_h = panel_h + label_height

    svg_w = (
        n_cols * panel_w
        + (n_cols - 1) * gap
        + 2 * margin
    )

    svg_h = (
        n_rows * total_panel_h
        + (n_rows - 1) * gap
        + 2 * margin
    )

    # --------------------------------------------------
    # Build SVG
    # --------------------------------------------------
    svg = []

    svg.append(
        f'<svg '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{svg_w}" '
        f'height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}">'
    )

    svg.append(
        f'<rect width="{svg_w}" '
        f'height="{svg_h}" '
        f'fill="white"/>'
    )

    svg.append(
        f'<g transform="translate({margin}, {margin})">'
    )

    for i, (filename, label, img) in enumerate(zip(image_files, labels, images)):
        row, col = i // n_cols, i % n_cols
        x, y = col * (panel_w + gap), row * (total_panel_h + gap)
        
        svg.append(
            f'<text x="{x + left_label_padding}" y="{y + font_size - 50}" '
            f'font-family="Arial" font-size="{font_size}" font-weight="bold" fill="black">{label}</text>'
        )
        
        img_x = x + (panel_w - img.width) / 2
        img_y = y + label_height + (panel_h - img.height) / 2
        data_uri = image_to_data_uri(filename)
        svg.append(
            f'<image x="{img_x}" y="{img_y}" width="{img.width}" height="{img.height}" '
            f'href="{data_uri}" xlink:href="{data_uri}"/>'
        )

    svg.append("</g>")
    svg.append("</svg>")

    svg_text = "\n".join(svg)

    # --------------------------------------------------
    # Write SVG
    # --------------------------------------------------
    Path(output_svg).write_text(
        svg_text,
        encoding="utf-8"
    )

    print(f"Saved: {output_svg}")

    # --------------------------------------------------
    # Render PNG
    # --------------------------------------------------
    cairosvg.svg2png(
        bytestring=svg_text.encode("utf-8"),
        write_to=output_png,
    )

    print(f"Saved: {output_png}")


if __name__ == "__main__":

    args = parse_args()

    create_diagram(
        args.input,
        args.output
    )
