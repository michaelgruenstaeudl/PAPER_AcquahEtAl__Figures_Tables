#!/usr/bin/env python3

import argparse
import base64
import mimetypes
from pathlib import Path

from PIL import Image
import cairosvg


N_IMAGES = 6
N_COLS = 3
N_ROWS = 2


def parse_args():
    parser = argparse.ArgumentParser(
        description="Arrange six gel images into a labeled 2x3 panel."
    )

    parser.add_argument("-i", "--input", required=True, help="Input folder containing the cropped gel JPEG files.")
    parser.add_argument("-o", "--output", required=True, help="Output path stem without extension. The script writes .svg and .png files.")

    return parser.parse_args()


def image_to_data_uri(path):
    mime_type = mimetypes.guess_type(path)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_panel_items(input_folder):
    return [
        (input_folder / f"scaled_GEL_Inv{i}.jpeg", f"Inversion {i}")
        for i in range(1, N_IMAGES + 1)
    ]


def create_diagram(input_folder, output_stem):
    input_folder = Path(input_folder)

    panel_items = build_panel_items(input_folder)
    missing_files = [str(path) for path, _ in panel_items if not path.exists()]
    if missing_files:
        raise FileNotFoundError("Missing input image(s):\n" + "\n".join(missing_files))

    output_svg = f"{output_stem}.svg"
    output_png = f"{output_stem}.png"

    images = [Image.open(path) for path, _ in panel_items]

    panel_w = max(img.width for img in images)
    panel_h = max(img.height for img in images)

    short_edge = min(panel_w, panel_h)
    gap = max(24, int(round(short_edge * 0.08)))

    font_size = max(30, int(round(short_edge * 0.15 * 0.5)))
    label_height = int(round(font_size * 1.2))
    label_to_image_gap = max(6, int(round(font_size * 0.12)))

    left_label_padding = max(8, int(round(panel_w * 0.02)))

    margin = max(30, int(round(short_edge * 0.07)))

    total_panel_h = panel_h + label_height + label_to_image_gap

    svg_w = (
        N_COLS * panel_w
        + (N_COLS - 1) * gap
        + 2 * margin
    )

    svg_h = (
        N_ROWS * total_panel_h
        + (N_ROWS - 1) * gap
        + 2 * margin
    )

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">',
        f'<rect width="{svg_w}" height="{svg_h}" fill="white"/>',
        f'<g transform="translate({margin}, {margin})">',
    ]

    for i, ((filename, label), img) in enumerate(zip(panel_items, images)):
        row, col = i // N_COLS, i % N_COLS
        x, y = col * (panel_w + gap), row * (total_panel_h + gap)

        svg.append(
            f'<text x="{x + left_label_padding}" y="{y + font_size}" '
            f'font-family="Arial" font-size="{font_size}" font-weight="normal" fill="black">{label}</text>'
        )

        img_x = x + (panel_w - img.width) / 2
        img_y = y + label_height + label_to_image_gap + (panel_h - img.height) / 2
        data_uri = image_to_data_uri(filename)
        svg.append(
            f'<image x="{img_x}" y="{img_y}" width="{img.width}" height="{img.height}" '
            f'href="{data_uri}" xlink:href="{data_uri}"/>'
        )

    svg_text = "\n".join([*svg, "</g>", "</svg>"])

    Path(output_svg).write_text(svg_text, encoding="utf-8")

    print(f"Saved: {output_svg}")

    cairosvg.svg2png(
        bytestring=svg_text.encode("utf-8"),
        write_to=output_png,
    )

    for img in images:
        img.close()

    print(f"Saved: {output_png}")


if __name__ == "__main__":
    args = parse_args()
    create_diagram(args.input, args.output)
