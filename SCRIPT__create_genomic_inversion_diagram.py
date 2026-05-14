#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Polygon, FancyArrowPatch, Rectangle, FancyBboxPatch
from matplotlib.transforms import Bbox
import numpy as np

def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a genomic inversion diagram and save PNG and SVG outputs."
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output path stem without an extension. The script writes .png and .svg files next to it.",
    )
    return parser.parse_args()


# ============================================================================
# MODULE-LEVEL CONSTANTS
# ============================================================================
BLACK = "black"
BLUE = "#2a6fdb"
YELLOW = "#ffd91a"
RED = "#ff6b73"

THIN = 2.0
GENOME_LINE_WIDTH = 3.2
INVERSION_BORDER_DASH_PATTERN = (0, (4, 6))

PRIMER_HEIGHT = 5
PRIMER_WIDTH = 14
PRIMER_NOTCH = 2
PRIMER_OFFSET = 7.2
PRIMER_EDGE_SHIFT_X = 8
GENOME_OVERHANG_EXTENSION = 3
GENOME_LEFT_OVERHANG_EXTRA = 2
GENOME_RIGHT_OVERHANG_SCALE = 0.8
GENOME_LABEL_OFFSET_Y = 0


# ============================================================================
# HELPER DRAWING FUNCTIONS
# ============================================================================
def draw_genome(ax, y, genome_start_x, genome_end_x):
    ax.plot([genome_start_x, genome_end_x], [y, y], color=BLACK, lw=GENOME_LINE_WIDTH, solid_capstyle="round")


def draw_vertical_line(ax, x, y1, y2, dashed=False):
    ax.plot(
        [x, x],
        [y1, y2],
        color=BLACK,
        lw=THIN,
        linestyle="--" if dashed else "-",
        dash_capstyle="round",
    )


def draw_inversion_border(ax, x, top_y, bottom_y):
    y_top = max(top_y, bottom_y)
    y_bottom = min(top_y, bottom_y)
    ax.plot(
        [x, x],
        [y_top, y_bottom],
        color=BLUE,
        lw=THIN,
        linestyle=INVERSION_BORDER_DASH_PATTERN,
        dash_capstyle="round",
    )


def draw_label(ax, x, y, text, ha="center", va="center", size=16, style="normal", rotation=0, color=BLACK, outline=False):
    text_artist = ax.text(x, y, text, ha=ha, va=va, fontsize=size, fontstyle=style, rotation=rotation, color=color)
    if outline:
        text_artist.set_path_effects([pe.Stroke(linewidth=3, foreground="white"), pe.Normal()])


def draw_primer_polygon(ax, x, y, direction="right", color=YELLOW, stem="up", width=None):
    primer_width = PRIMER_WIDTH if width is None else width
    if stem == "none":
        flag_y = y
    elif stem == "up":
        stem_end = y + PRIMER_OFFSET
        draw_vertical_line(ax, x, y, stem_end)
        flag_y = stem_end
    else:
        stem_end = y - PRIMER_OFFSET
        draw_vertical_line(ax, x, y, stem_end)
        flag_y = stem_end - PRIMER_HEIGHT

    if direction == "right":
        points = [
            (x, flag_y),
            (x + primer_width - PRIMER_NOTCH, flag_y),
            (x + primer_width, flag_y + PRIMER_HEIGHT / 2),
            (x + primer_width - PRIMER_NOTCH, flag_y + PRIMER_HEIGHT),
            (x, flag_y + PRIMER_HEIGHT),
        ]
        tip_x = x + primer_width
    else:
        points = [
            (x, flag_y),
            (x - primer_width + PRIMER_NOTCH, flag_y),
            (x - primer_width, flag_y + PRIMER_HEIGHT / 2),
            (x - primer_width + PRIMER_NOTCH, flag_y + PRIMER_HEIGHT),
            (x, flag_y + PRIMER_HEIGHT),
        ]
        tip_x = x - primer_width

    primer = Polygon(
        points,
        closed=True,
        facecolor=color,
        edgecolor=BLACK,
        lw=THIN,
        joinstyle="round",
    )
    ax.add_patch(primer)

    return {
        "center_y": flag_y + PRIMER_HEIGHT / 2,
        "tip_x": tip_x,
        "blunt_x": x,
        "direction": direction,
        "width": primer_width,
    }


def draw_primer_name(ax, primer, name, size=16):
    primer_width = primer.get("width", PRIMER_WIDTH)
    if primer["direction"] == "right":
        x = primer["blunt_x"] + primer_width * 0.42
    else:
        x = primer["blunt_x"] - primer_width * 0.42
    draw_label(ax, x, primer["center_y"], name, ha="center", va="center", size=size, outline=True)


def draw_curved_arrow(ax, start, end, rad, color=BLACK):
    arrow = FancyArrowPatch(
        start,
        end,
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>",
        mutation_scale=28,
        lw=THIN,
        color=color,
        linestyle="-",
    )
    ax.add_patch(arrow)


def draw_electrophoresis_placeholder(ax, y, gel_start_x, gel_width, gel_height):
    gel_rect = Rectangle(
        (gel_start_x, y - gel_height / 2),
        gel_width,
        gel_height,
        edgecolor=BLACK,
        facecolor="#f7f2e8",
        lw=1.2,
    )
    ax.add_patch(gel_rect)


def draw_gel_frame(ax, gel_start_x, gel_bottom, gel_width, gel_height):
    gel_fill = "#f3e2c5"
    gel_edge = "#9b8060"
    well_fill = "#ead7b8"

    gel = FancyBboxPatch(
        (gel_start_x, gel_bottom),
        gel_width,
        gel_height,
        boxstyle="round,pad=0.01,rounding_size=0.6",
        linewidth=1.2,
        edgecolor=gel_edge,
        facecolor=gel_fill,
        zorder=1,
    )
    ax.add_patch(gel)

    inner_margin = gel_width * 0.01
    inner_gel = FancyBboxPatch(
        (gel_start_x + inner_margin, gel_bottom + inner_margin),
        gel_width - 2 * inner_margin,
        gel_height - 2 * inner_margin,
        boxstyle="round,pad=0.005,rounding_size=0.4",
        linewidth=0.5,
        edgecolor=gel_edge,
        facecolor="none",
        zorder=2,
    )
    ax.add_patch(inner_gel)

    lane_count = 7
    lane_spacing = gel_width / (lane_count + 1)
    lane_x = [gel_start_x + lane_spacing * (i + 1) for i in range(lane_count)]

    well_y = gel_bottom + gel_height * 0.92
    well_w = gel_width * 0.07
    well_h = gel_height * 0.035
    scaled_well_h = well_h * 1.25
    well_top = well_y + well_h
    well_bottom = well_top - scaled_well_h
    inner_well_h = well_h * 0.64
    scaled_inner_well_h = inner_well_h * 1.25
    inner_well_top = well_y + well_h * 0.82
    inner_well_bottom = inner_well_top - scaled_inner_well_h
    for x in lane_x:
        ax.add_patch(
            FancyBboxPatch(
                (x - well_w / 2, well_bottom),
                well_w,
                scaled_well_h,
                boxstyle="round,pad=0.01,rounding_size=0.15",
                linewidth=0.8,
                edgecolor=gel_edge,
                facecolor=well_fill,
                zorder=3,
            )
        )
        ax.add_patch(
            Rectangle(
                (x - well_w / 2 + well_w * 0.08, inner_well_bottom),
                well_w * 0.84,
                scaled_inner_well_h,
                linewidth=0.4,
                edgecolor=gel_edge,
                facecolor="#f4e7ce",
                zorder=4,
            )
        )

    return lane_x, well_bottom, scaled_well_h


def draw_gel_band(ax, x, rel_y, gel_bottom, gel_width, gel_height, width_scale=1.0, height_scale=1.0, alpha=0.95):
    band_w = gel_width * 0.055 * width_scale
    band_h = gel_height * 0.015 * height_scale
    band_y = gel_bottom + gel_height * rel_y
    scaled_band_h = band_h * 1.15
    band_top = band_y + band_h / 2
    band_bottom = band_top - scaled_band_h
    center_band_h = band_h * 0.64
    scaled_center_band_h = center_band_h * 1.15
    center_band_top = band_y + band_h * 0.32
    center_band_bottom = center_band_top - scaled_center_band_h

    ax.add_patch(
        FancyBboxPatch(
            (x - band_w / 2, band_bottom),
            band_w,
            scaled_band_h,
            boxstyle="round,pad=0.01,rounding_size=0.12",
            linewidth=0,
            facecolor="#2b2924",
            alpha=alpha,
            zorder=5,
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (x - band_w / 2 + band_w * 0.03, center_band_bottom),
            band_w * 0.94,
            scaled_center_band_h,
            boxstyle="round,pad=0.003,rounding_size=0.08",
            linewidth=0,
            facecolor="black",
            alpha=0.25,
            zorder=6,
        )
    )


def draw_ladder_lane(ax, x, ladder_rel_y, gel_bottom, gel_width, gel_height):
    for bp, rel_y in ladder_rel_y.items():
        height_scale = 1.2 if bp in (500, 1000) else 0.9
        draw_gel_band(ax, x, rel_y, gel_bottom, gel_width, gel_height, height_scale=height_scale)


def draw_top_lane_annotations(ax, lane_x, label_y):
    for lane_idx, label in {0: "Ladder", 1: "+Ctrl", 2: "—Ctrl"}.items():
        draw_label(ax, lane_x[lane_idx], label_y, label, ha="center", va="bottom", size=14, color=BLACK)

    marker_width = 10.6 * 0.8
    marker_specs = {
        3: (("sta.R", "left", YELLOW), ("sta.F", "right", YELLOW)),
        4: (("end.R", "left", RED), ("end.F", "right", RED)),
        5: (("end.F", "left", RED), ("sta.F", "right", YELLOW)),
        6: (("end.R", "left", RED), ("sta.R", "right", YELLOW)),
    }

    for lane_idx, ((lower_name, lower_direction, lower_color), (upper_name, upper_direction, upper_color)) in marker_specs.items():
        center_x = lane_x[lane_idx]
        lower_x = center_x + marker_width / 2 if lower_direction == "left" else center_x - marker_width / 2
        upper_x = center_x + marker_width / 2 if upper_direction == "left" else center_x - marker_width / 2

        lower_marker = draw_primer_polygon(
            ax,
            lower_x,
            label_y,
            direction=lower_direction,
            color=lower_color,
            stem="none",
            width=marker_width,
        )
        draw_primer_name(ax, lower_marker, lower_name, size=14)

        upper_marker = draw_primer_polygon(
            ax,
            upper_x,
            label_y + PRIMER_HEIGHT + 0.5,
            direction=upper_direction,
            color=upper_color,
            stem="none",
            width=marker_width,
        )
        draw_primer_name(ax, upper_marker, upper_name, size=14)


def get_content_bbox(fig, margin_px=0):
    fig.canvas.draw()
    image = np.asarray(fig.canvas.buffer_rgba())
    nonwhite_mask = np.any(image[:, :, :3] < 250, axis=2)
    nonwhite_rows = np.where(np.any(nonwhite_mask, axis=1))[0]
    nonwhite_cols = np.where(np.any(nonwhite_mask, axis=0))[0]
    if len(nonwhite_rows) == 0 or len(nonwhite_cols) == 0:
        return None

    image_height = image.shape[0]
    image_width = image.shape[1]

    left_px = max(nonwhite_cols.min() - margin_px, 0)
    right_px = min(nonwhite_cols.max() + 1 + margin_px, image_width)
    top_px = max(nonwhite_rows.min() - margin_px, 0)
    bottom_px = min(nonwhite_rows.max() + 1 + margin_px, image_height)

    fig_width_in, fig_height_in = fig.get_size_inches()
    dpi = fig.dpi
    left_in = left_px / dpi
    right_in = right_px / dpi
    top_in = (image_height - top_px) / dpi
    bottom_in = (image_height - bottom_px) / dpi
    return Bbox.from_extents(left_in, bottom_in, right_in, top_in)


def electrophoresis_original_genome(ax, y, gel_start_x, gel_width, gel_height, annotation_y=None):
    """Draw gel electrophoresis visualization for original (ancestral) genome state."""
    gel_bottom = y - gel_height / 2
    lane_x, _, _ = draw_gel_frame(ax, gel_start_x, gel_bottom, gel_width, gel_height)
    if annotation_y is None:
        annotation_y = y
    label_y = annotation_y + gel_height * 0.53
    draw_top_lane_annotations(ax, lane_x, label_y)

    # NEB ladder positions
    ladder_rel_y = {
        1517: 0.78,
        1200: 0.71,
        1000: 0.64,
        900: 0.58,
        700: 0.52,
        600: 0.46,
        500: 0.39,
        300: 0.28,
        200: 0.18,
    }

    draw_ladder_lane(ax, lane_x[0], ladder_rel_y, gel_bottom, gel_width, gel_height)

    # ----------------------------------------
    # Sample lanes: 1, 2, 3 identical to lower gel; 4, 5 empty; 6, 7 have distinct bands
    # ----------------------------------------

    # Lane 2: 300 bp
    draw_gel_band(ax, lane_x[1], ladder_rel_y[300], gel_bottom, gel_width, gel_height, width_scale=0.95, height_scale=1.3)

    # Lane 3: empty

    # Lane 4: empty

    # Lane 5: empty

    # Lane 6: one band in 600-800 bp range (650 bp, smaller)
    draw_gel_band(ax, lane_x[5], ladder_rel_y[600], gel_bottom, gel_width, gel_height, width_scale=0.85, height_scale=1.2)

    # Lane 7: one band in 600-800 bp range (750 bp, larger)
    draw_gel_band(ax, lane_x[6], ladder_rel_y[700], gel_bottom, gel_width, gel_height, width_scale=1.05, height_scale=1.35)


def electrophoresis_lower_genome(ax, y, gel_start_x, gel_width, gel_height):
    """Draw gel electrophoresis visualization for inverted genome state."""
    gel_bottom = y - gel_height / 2
    lane_x, _, _ = draw_gel_frame(ax, gel_start_x, gel_bottom, gel_width, gel_height)

    # NEB ladder
    ladder_rel_y = {
        1517: 0.78,
        1200: 0.71,
        1000: 0.64,
        900: 0.58,
        700: 0.52,
        600: 0.46,
        500: 0.39,
        300: 0.28,
        200: 0.18,
    }

    draw_ladder_lane(ax, lane_x[0], ladder_rel_y, gel_bottom, gel_width, gel_height)
    draw_gel_band(ax, lane_x[1], ladder_rel_y[300], gel_bottom, gel_width, gel_height, width_scale=0.95, height_scale=1.3)
    draw_gel_band(ax, lane_x[3], ladder_rel_y[300], gel_bottom, gel_width, gel_height, width_scale=0.95, height_scale=1.3)
    draw_gel_band(ax, lane_x[4], ladder_rel_y[900], gel_bottom, gel_width, gel_height, width_scale=0.95, height_scale=1.3)


# ============================================================================
# SUBPLOT FUNCTIONS
# ============================================================================
def create_subplot_left(ax, y_normal, y_inversion):
    """Draw the genomic inversion diagram on the given axes."""
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 100)
    ax.axis("off")

    genome_start_x = 25 - GENOME_LEFT_OVERHANG_EXTRA
    sta_f_x = 34 - PRIMER_EDGE_SHIFT_X
    end_r_x = 100 + PRIMER_EDGE_SHIFT_X
    left_outer_primer_x = sta_f_x
    right_outer_primer_x = end_r_x
    left_overhang = (left_outer_primer_x - genome_start_x) + GENOME_OVERHANG_EXTENSION
    right_overhang = (left_overhang - 1) * GENOME_RIGHT_OVERHANG_SCALE
    genome_end_x = right_outer_primer_x + right_overhang

    # Mirror Inv.start.R pole distance across inversion borders:
    x_left = 45
    x_right = 90
    inv_start_r_base_distance = 53 - x_left
    inv_start_r_border_distance = inv_start_r_base_distance * 1.2 * 1.25 * 1.2 * 1.1
    inv_start_r_inversion_pole_x = x_left + inv_start_r_border_distance
    inv_start_r_normal_pole_x = x_right - inv_start_r_border_distance

    # Mirror Inv.end.F pole distance across genomes:
    inv_end_f_normal_pole_x = 55
    inv_end_f_base_border_distance = inv_end_f_normal_pole_x - x_left
    inv_end_f_border_distance = inv_end_f_base_border_distance * 1.4 * 1.2 * 1.1
    inv_end_f_normal_pole_x = x_left + inv_end_f_border_distance
    inv_end_f_inversion_pole_x = x_right - inv_end_f_border_distance

    genome_label_anchor_x = 3
    draw_label(ax, genome_label_anchor_x, y_normal + GENOME_LABEL_OFFSET_Y, "Ancestral\nGenome", ha="left", size=20)
    draw_label(ax, genome_label_anchor_x, y_inversion + GENOME_LABEL_OFFSET_Y, "Inversion\nPresent", ha="left", size=20)

    draw_genome(ax, y_normal, genome_start_x, genome_end_x)
    draw_genome(ax, y_inversion, genome_start_x, genome_end_x)

    draw_inversion_border(ax, x_left, y_normal, y_inversion)
    draw_inversion_border(ax, x_right, y_normal, y_inversion)
    inversion_border_label_y = (y_normal + y_inversion) / 2
    draw_label(ax, x_left - 1, inversion_border_label_y, "Inversion start", ha="right", size=12, rotation=90, color=BLUE)
    draw_label(ax, x_right + 1, inversion_border_label_y, "Inversion end", ha="left", size=12, rotation=90, color=BLUE)

    arrow_genome_offset_y = 2.0
    draw_curved_arrow(ax, (x_left + 0.8, y_normal - arrow_genome_offset_y), (x_right - 0.8, y_inversion + arrow_genome_offset_y), rad=0.2, color=BLUE)
    draw_curved_arrow(ax, (x_right - 0.8, y_normal - arrow_genome_offset_y), (x_left + 0.8, y_inversion + arrow_genome_offset_y), rad=-0.2, color=BLUE)

    primer = draw_primer_polygon(ax, sta_f_x, y_normal, direction="right", color=YELLOW, stem="up")
    draw_primer_name(ax, primer, "sta.F")
    primer = draw_primer_polygon(ax, inv_start_r_normal_pole_x, y_normal, direction="right", color=YELLOW, stem="up")
    draw_primer_name(ax, primer, "sta.R")
    primer = draw_primer_polygon(ax, inv_end_f_normal_pole_x, y_normal, direction="left", color=RED, stem="down")
    draw_primer_name(ax, primer, "end.F")
    primer = draw_primer_polygon(ax, end_r_x, y_normal, direction="left", color=RED, stem="down")
    draw_primer_name(ax, primer, "end.R")

    primer = draw_primer_polygon(ax, sta_f_x, y_inversion, direction="right", color=YELLOW, stem="up")
    draw_primer_name(ax, primer, "sta.F")
    primer = draw_primer_polygon(ax, inv_start_r_inversion_pole_x, y_inversion, direction="left", color=YELLOW, stem="down")
    draw_primer_name(ax, primer, "sta.R")
    primer = draw_primer_polygon(ax, inv_end_f_inversion_pole_x, y_inversion, direction="right", color=RED, stem="up")
    draw_primer_name(ax, primer, "end.F")
    primer = draw_primer_polygon(ax, end_r_x, y_inversion, direction="left", color=RED, stem="down")
    draw_primer_name(ax, primer, "end.R")


def create_subplot_right(ax, y_normal, y_inversion):
    """Draw gel electrophoresis on the given axes."""
    gel_width, gel_height = 87, 33.75
    gel_start_x = 2
    top_gel_offset_y = -2.0

    ax.set_xlim(0, gel_start_x + gel_width + 2)
    ax.set_ylim(0, 100)
    ax.axis("off")

    electrophoresis_original_genome(
        ax,
        y_normal + top_gel_offset_y,
        gel_start_x,
        gel_width,
        gel_height,
        annotation_y=y_normal,
    )
    electrophoresis_lower_genome(ax, y_inversion, gel_start_x, gel_width, gel_height)


def create_diagram(output_path="inversion_diagram"):
    """Create figure with both inversion diagram and gel electrophoresis side-by-side."""
    genome_center_y = 50
    distance = 42.0
    y_normal = genome_center_y + distance / 2
    y_inversion = genome_center_y - distance / 2

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(20, 7.5))
    ax_left.set_in_layout(False)
    ax_right.set_in_layout(False)
    fig.subplots_adjust(wspace=0.0)

    create_subplot_left(ax_left, y_normal, y_inversion)
    create_subplot_right(ax_right, y_normal, y_inversion)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bbox_inches = get_content_bbox(fig, margin_px=10)

    fig.savefig(output_path.with_suffix(".png"), dpi=300, bbox_inches=bbox_inches, pad_inches=0, facecolor="white")
    fig.savefig(output_path.with_suffix(".svg"), bbox_inches=bbox_inches, pad_inches=0, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    args = parse_args()
    create_diagram(args.output)
