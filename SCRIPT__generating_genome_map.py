from pathlib import Path
import argparse
import re
import xml.etree.ElementTree as ET
import cairosvg


def get_svg_size(svg_path):
    """Return SVG width and height from viewBox or width/height."""
    root = ET.parse(svg_path).getroot()

    viewbox = root.get("viewBox")
    if viewbox:
        _, _, w, h = map(float, viewbox.replace(",", " ").split())
        return w, h

    def parse_length(value):
        return float(re.sub(r"[^\d.]", "", value))

    return parse_length(root.get("width")), parse_length(root.get("height"))


def strip_outer_svg(svg_path):
    """Return SVG content without the outer <svg> tag."""
    text = Path(svg_path).read_text(encoding="utf-8")

    text = re.sub(r"<\?xml.*?\?>", "", text, flags=re.DOTALL)
    text = re.sub(r"<!DOCTYPE.*?>", "", text, flags=re.DOTALL)

    inner = re.sub(r"^.*?<svg[^>]*>", "", text, flags=re.DOTALL)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.DOTALL)

    return inner.strip()


def combine_svgs(
    large_svg,
    small_svg,
    output_svg,
    output_png,
    large_size,
    small_size,
    small_exaggeration,
    gap,
):
    large_w, large_h = get_svg_size(large_svg)
    small_w, small_h = get_svg_size(small_svg)

    displayed_linear_ratio = (
        (large_size / small_size) / small_exaggeration
    )

    # Scale smaller SVG
    target_small_w = large_w / displayed_linear_ratio
    small_scale = target_small_w / small_w
    target_small_h = small_h * small_scale

    # Add generous spacing between SVGs
    effective_gap = gap + (0.15 * large_w)

    canvas_w = large_w + effective_gap + target_small_w
    canvas_h = max(large_h, target_small_h)

    large_inner = strip_outer_svg(large_svg)
    small_inner = strip_outer_svg(small_svg)

    combined_svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:cc="http://creativecommons.org/ns#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
    width="{canvas_w}"
    height="{canvas_h}"
    viewBox="0 0 {canvas_w} {canvas_h}">

    <!-- White background -->
    <rect width="100%" height="100%" fill="white"/>

    <!-- Large SVG -->
    <g id="large_svg"
       transform="translate(0, {(canvas_h - large_h) / 2})">
        {large_inner}
    </g>

    <!-- Scaled small SVG -->
    <g id="small_svg_scaled"
       transform="translate({large_w + effective_gap},
                            {(canvas_h - target_small_h) / 2})
                  scale({small_scale})">
        {small_inner}
    </g>

</svg>
'''

    # Write SVG
    Path(output_svg).write_text(combined_svg, encoding="utf-8")

    # Export PNG
    cairosvg.svg2png(
        bytestring=combined_svg.encode("utf-8"),
        write_to=output_png,
    )

    print(f"Displayed linear ratio: {displayed_linear_ratio:.4f}:1")
    print(f"Small SVG scale factor: {small_scale:.6f}")
    print(f"Effective gap: {effective_gap:.2f}")
    print(f"SVG written to: {output_svg}")
    print(f"PNG written to: {output_png}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Combine two SVG genome maps into a single SVG and PNG "
            "while exaggerating the smaller genome map."
        )
    )

    parser.add_argument(
        "--large-svg",
        required=True,
        help="Path to SVG representing the larger genome"
    )

    parser.add_argument(
        "--small-svg",
        required=True,
        help="Path to SVG representing the smaller genome"
    )

    parser.add_argument(
        "--output-prefix",
        required=True,
        help="Output file prefix"
    )

    parser.add_argument(
        "--large-size",
        type=float,
        required=True,
        help="Actual size represented by the larger genome"
    )

    parser.add_argument(
        "--small-size",
        type=float,
        required=True,
        help="Actual size represented by the smaller genome"
    )

    parser.add_argument(
        "--small-exaggeration",
        type=float,
        default=100,
        help=(
            "Visual exaggeration factor for the smaller genome. "
            "Default: 100"
        )
    )

    parser.add_argument(
        "--gap",
        type=float,
        default=100,
        help="Additional spacing between SVGs. Default: 100"
    )

    args = parser.parse_args()

    output_svg = f"{args.output_prefix}.svg"
    output_png = f"{args.output_prefix}.png"

    combine_svgs(
        large_svg=args.large_svg,
        small_svg=args.small_svg,
        output_svg=output_svg,
        output_png=output_png,
        large_size=args.large_size,
        small_size=args.small_size,
        small_exaggeration=args.small_exaggeration,
        gap=args.gap,
    )


if __name__ == "__main__":
    main()
