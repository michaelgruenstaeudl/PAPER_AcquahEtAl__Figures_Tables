#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Polygon, FancyArrowPatch

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
PRIMER_NAME_GAP = 2
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


def draw_primer_polygon(ax, x, y, direction="right", color=YELLOW, stem="up"):
    if stem == "up":
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
            (x + PRIMER_WIDTH - PRIMER_NOTCH, flag_y),
            (x + PRIMER_WIDTH, flag_y + PRIMER_HEIGHT / 2),
            (x + PRIMER_WIDTH - PRIMER_NOTCH, flag_y + PRIMER_HEIGHT),
            (x, flag_y + PRIMER_HEIGHT),
        ]
        tip_x = x + PRIMER_WIDTH
    else:
        points = [
            (x, flag_y),
            (x - PRIMER_WIDTH + PRIMER_NOTCH, flag_y),
            (x - PRIMER_WIDTH, flag_y + PRIMER_HEIGHT / 2),
            (x - PRIMER_WIDTH + PRIMER_NOTCH, flag_y + PRIMER_HEIGHT),
            (x, flag_y + PRIMER_HEIGHT),
        ]
        tip_x = x - PRIMER_WIDTH

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
    }


def draw_primer_name(ax, primer, name, size=16):
    if primer["direction"] == "right":
        x = primer["blunt_x"] + PRIMER_WIDTH * 0.42
    else:
        x = primer["blunt_x"] - PRIMER_WIDTH * 0.42
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


def electrophoresis_original_genome(ax, y, gel_start_x, gel_width, gel_height):
    """Draw gel electrophoresis visualization for original genome state.
    
    Placeholder function to be filled with actual gel electrophoresis visualization.
    """
    from matplotlib.patches import Rectangle
    
    gel_rect = Rectangle((gel_start_x, y - gel_height / 2), gel_width, gel_height, 
                           edgecolor=BLACK, facecolor="#f7f2e8", lw=1.2)
    ax.add_patch(gel_rect)


def electrophoresis_lower_genome(ax, y, gel_start_x, gel_width, gel_height):
    """Draw gel electrophoresis visualization for inverted genome state.
    
    Placeholder function to be filled with actual gel electrophoresis visualization.
    """
    from matplotlib.patches import Rectangle
    
    gel_rect = Rectangle((gel_start_x, y - gel_height / 2), gel_width, gel_height,
                           edgecolor=BLACK, facecolor="#f7f2e8", lw=1.2)
    ax.add_patch(gel_rect)


# ============================================================================
# SUBPLOT FUNCTIONS
# ============================================================================
def create_subplot_left(ax, y_normal, y_inversion):
    """Draw the genomic inversion diagram on the given axes."""
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 100)
    ax.axis("off")

    genome_start_x = 25 - GENOME_LEFT_OVERHANG_EXTRA
    left_outer_primer_x = 34 - PRIMER_EDGE_SHIFT_X
    right_outer_primer_x = 100 + PRIMER_EDGE_SHIFT_X
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

    # Labels
    genome_label_anchor_x = 3
    draw_label(ax, genome_label_anchor_x, y_normal + GENOME_LABEL_OFFSET_Y, "Ancestral\nGenome", ha="left", size=20)
    draw_label(ax, genome_label_anchor_x, y_inversion + GENOME_LABEL_OFFSET_Y, "Inversion\nPresent", ha="left", size=20)

    # Genome lines
    draw_genome(ax, y_normal, genome_start_x, genome_end_x)
    draw_genome(ax, y_inversion, genome_start_x, genome_end_x)

    # Inversion borders (dashed lines)
    draw_inversion_border(ax, x_left, y_normal, y_inversion)
    draw_inversion_border(ax, x_right, y_normal, y_inversion)
    inversion_border_label_y = (y_normal + y_inversion) / 2
    draw_label(ax, x_left - 1, inversion_border_label_y, "Inversion start", ha="right", size=12, rotation=90, color=BLUE)
    draw_label(ax, x_right + 1, inversion_border_label_y, "Inversion end", ha="left", size=12, rotation=90, color=BLUE)

    # Curved inversion arrows
    arrow_genome_offset_y = 2.0
    draw_curved_arrow(ax, (x_left + 0.8, y_normal - arrow_genome_offset_y), (x_right - 0.8, y_inversion + arrow_genome_offset_y), rad=0.2, color=BLUE)
    draw_curved_arrow(ax, (x_right - 0.8, y_normal - arrow_genome_offset_y), (x_left + 0.8, y_inversion + arrow_genome_offset_y), rad=-0.2, color=BLUE)

    # Normal state primers and primer names
    primer = draw_primer_polygon(ax, 34 - PRIMER_EDGE_SHIFT_X, y_normal, direction="right", color=YELLOW, stem="up")
    draw_primer_name(ax, primer, "sta.F")

    primer = draw_primer_polygon(ax, inv_start_r_normal_pole_x, y_normal, direction="right", color=YELLOW, stem="up")
    draw_primer_name(ax, primer, "sta.R")

    primer = draw_primer_polygon(ax, inv_end_f_normal_pole_x, y_normal, direction="left", color=RED, stem="down")
    draw_primer_name(ax, primer, "end.F")

    primer = draw_primer_polygon(ax, 100 + PRIMER_EDGE_SHIFT_X, y_normal, direction="left", color=RED, stem="down")
    draw_primer_name(ax, primer, "end.R")

    # Inversion state primers and primer names
    primer = draw_primer_polygon(ax, 34 - PRIMER_EDGE_SHIFT_X, y_inversion, direction="right", color=YELLOW, stem="up")
    draw_primer_name(ax, primer, "sta.F")

    primer = draw_primer_polygon(ax, inv_start_r_inversion_pole_x, y_inversion, direction="left", color=YELLOW, stem="down")
    draw_primer_name(ax, primer, "sta.R")

    primer = draw_primer_polygon(ax, inv_end_f_inversion_pole_x, y_inversion, direction="right", color=RED, stem="up")
    draw_primer_name(ax, primer, "end.F")

    primer = draw_primer_polygon(ax, 100 + PRIMER_EDGE_SHIFT_X, y_inversion, direction="left", color=RED, stem="down")
    draw_primer_name(ax, primer, "end.R")


def create_subplot_right(ax, y_normal, y_inversion):
    """Draw gel electrophoresis rectangles on the given axes."""
    # Gel dimensions: single large rectangle per row, similar to genome line width
    gel_width = 87  # Matches genome line width (112 - 25)
    gel_height = 33.75  # Tall rectangles (expanded 50% both up and down)
    gel_start_x = 2  # Small left margin
    
    ax.set_xlim(0, gel_start_x + gel_width + 2)  # End right after rectangle
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Top row (y_normal) - original genome electrophoresis
    electrophoresis_original_genome(ax, y_normal, gel_start_x, gel_width, gel_height)

    # Bottom row (y_inversion) - inverted genome electrophoresis
    electrophoresis_lower_genome(ax, y_inversion, gel_start_x, gel_width, gel_height)


def create_diagram(output_path="inversion_diagram"):
    """Create figure with both inversion diagram and gel rectangles side-by-side."""
    # Calculate y positions (shared between both subplots)
    genome_center_y = 50
    genome_vertical_distance = 42.0
    y_normal = genome_center_y + genome_vertical_distance / 2
    y_inversion = genome_center_y - genome_vertical_distance / 2

    # Create figure with 1 row and 2 columns
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(20, 7.5))
    
    # Set layout to False for both axes so tight_layout doesn't interfere
    ax_left.set_in_layout(False)
    ax_right.set_in_layout(False)
    
    # Adjust spacing between subplots (decrease by 33%)
    fig.subplots_adjust(wspace=0.0)
    
    # Create both subplots
    create_subplot_left(ax_left, y_normal, y_inversion)
    create_subplot_right(ax_right, y_normal, y_inversion)

    # Save outputs
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path.with_suffix(".png"), dpi=300, bbox_inches="tight", pad_inches=0.12, facecolor="white")
    fig.savefig(output_path.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.12, facecolor="white")

    plt.close(fig)


if __name__ == "__main__":
    args = parse_args()
    create_diagram(args.output)
