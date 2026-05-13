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


def create_diagram(output_path="inversion_diagram"):
    # Colors: only black, yellow, red
    BLACK = "black"
    BLUE = "#2a6fdb"
    YELLOW = "#ffd91a"
    RED = "#ff6b73"

    # Line widths: only thin and thick
    THIN = 2.0
    GENOME_LINE_WIDTH = 3.2
    INVERSION_BORDER_DASH_PATTERN = (0, (4, 6))

    # Primer geometry: all primers share exactly the same size and form
    PRIMER_HEIGHT = 5
    PRIMER_WIDTH = 8
    PRIMER_NOTCH = 2
    PRIMER_OFFSET = 9 * 0.8
    PRIMER_NAME_GAP = 2
    GENOME_LABEL_OFFSET_Y = -0.5

    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_in_layout(False)

    genome_start_x = 25
    genome_end_x = 112

    def draw_genome(y):
        genome, = ax.plot([genome_start_x, genome_end_x], [y, y], color=BLACK, lw=GENOME_LINE_WIDTH, solid_capstyle="round")
        return genome

    def draw_vertical_line(x, y1, y2, dashed=False):
        ax.plot(
            [x, x],
            [y1, y2],
            color=BLACK,
            lw=THIN,
            linestyle="--" if dashed else "-",
            dash_capstyle="round",
        )

    def draw_inversion_border(x, top_y, bottom_y):
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

    def draw_label(
        x,
        y,
        text,
        ha="center",
        va="center",
        size=16,
        style="normal",
        rotation=0,
        color=BLACK,
        outline=False,
        outline_color="white",
        outline_width=3,
    ):
        text_artist = ax.text(x, y, text, ha=ha, va=va, fontsize=size, fontstyle=style, rotation=rotation, color=color)
        if outline:
            text_artist.set_path_effects([pe.Stroke(linewidth=outline_width, foreground=outline_color), pe.Normal()])

    def draw_primer(x, y, direction="right", color=YELLOW, stem="up"):
        if stem == "up":
            stem_end = y + PRIMER_OFFSET
            draw_vertical_line(x, y, stem_end)
            flag_y = stem_end
        else:
            stem_end = y - PRIMER_OFFSET
            draw_vertical_line(x, y, stem_end)
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

    def draw_primer_name(primer, name, size=16):
        if primer["direction"] == "right":
            x = primer["blunt_x"] - PRIMER_NAME_GAP
            ha = "right"
        else:
            x = primer["blunt_x"] + PRIMER_NAME_GAP
            ha = "left"

        # Align text centerline with the primer horizontal centerline.
        draw_label(x, primer["center_y"], name, ha=ha, va="center", size=size, outline=True)

    def draw_curved_arrow(start, end, rad, color=BLACK):
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

    # Main y positions
    genome_center_y = 50
    genome_vertical_distance = 50 * 1.2 * 0.8
    y_normal = genome_center_y + genome_vertical_distance / 2
    y_inversion = genome_center_y - genome_vertical_distance / 2
    arrow_genome_offset_y = 2.5 * 0.8

    # Breakpoint positions
    x_left = 45
    x_right = 90

    # Inversion borders
    inversion_border_start_x = x_left
    inversion_border_end_x = x_right
    inversion_border_top_y = y_normal
    inversion_border_bottom_y = y_inversion

    # Mirror Inv.start.R pole distance across inversion borders:
    # left border -> inversion Inv.start.R equals
    # normal Inv.start.R -> right border
    inv_start_r_inversion_pole_x = 53
    inv_start_r_border_distance = inv_start_r_inversion_pole_x - inversion_border_start_x
    inv_start_r_normal_pole_x = inversion_border_end_x - inv_start_r_border_distance

    # Mirror Inv.end.F pole distance across genomes:
    # inversion Inv.end.F -> right border equals
    # left border -> normal Inv.end.F
    inv_end_f_normal_pole_x = 55
    inv_end_f_base_border_distance = inv_end_f_normal_pole_x - inversion_border_start_x
    inv_end_f_border_distance = inv_end_f_base_border_distance * 1.4
    inv_end_f_normal_pole_x = inversion_border_start_x + inv_end_f_border_distance
    inv_end_f_inversion_pole_x = inversion_border_end_x - inv_end_f_border_distance

    # Labels
    genome_label_anchor_x = 3
    draw_label(genome_label_anchor_x, y_normal + GENOME_LABEL_OFFSET_Y, "ORIGINAL\nGENOME", ha="left", size=20)
    draw_label(genome_label_anchor_x, y_inversion + GENOME_LABEL_OFFSET_Y, "INVERSION\nPRESENT", ha="left", size=20)

    # Genome lines
    draw_genome(y_normal)
    draw_genome(y_inversion)

    # Inversion borders (dashed lines)
    draw_inversion_border(inversion_border_start_x, inversion_border_top_y, inversion_border_bottom_y)
    draw_inversion_border(inversion_border_end_x, inversion_border_top_y, inversion_border_bottom_y)
    inversion_border_label_y = (inversion_border_top_y + inversion_border_bottom_y) / 2
    draw_label(inversion_border_start_x - 1, inversion_border_label_y, "Inversion start", ha="right", size=12, rotation=90, color=BLUE)
    draw_label(inversion_border_end_x + 1, inversion_border_label_y, "Inversion end", ha="left", size=12, rotation=90, color=BLUE)

    # Curved inversion arrows
    draw_curved_arrow((inversion_border_start_x + 0.8, y_normal - arrow_genome_offset_y), (inversion_border_end_x - 0.8, y_inversion + arrow_genome_offset_y), rad=0.2, color=BLUE)
    draw_curved_arrow((inversion_border_end_x - 0.8, y_normal - arrow_genome_offset_y), (inversion_border_start_x + 0.8, y_inversion + arrow_genome_offset_y), rad=-0.2, color=BLUE)

    # Normal state primers and primer names
    primer = draw_primer(34, y_normal, direction="right", color=YELLOW, stem="up")
    draw_primer_name(primer, "Inv.start.F")

    primer = draw_primer(inv_start_r_normal_pole_x, y_normal, direction="right", color=YELLOW, stem="up")
    draw_primer_name(primer, "Inv.start.R")

    primer = draw_primer(inv_end_f_normal_pole_x, y_normal, direction="left", color=RED, stem="down")
    draw_primer_name(primer, "Inv.end.F")

    primer = draw_primer(100, y_normal, direction="left", color=RED, stem="down")
    draw_primer_name(primer, "Inv.end.R")

    # Inversion state primers and primer names
    primer = draw_primer(34, y_inversion, direction="right", color=YELLOW, stem="up")
    draw_primer_name(primer, "Inv.start.F")

    primer = draw_primer(inv_start_r_inversion_pole_x, y_inversion, direction="left", color=YELLOW, stem="down")
    draw_primer_name(primer, "Inv.start.R")

    primer = draw_primer(inv_end_f_inversion_pole_x, y_inversion, direction="right", color=RED, stem="up")
    draw_primer_name(primer, "Inv.end.F")

    primer = draw_primer(100, y_inversion, direction="left", color=RED, stem="down")
    draw_primer_name(primer, "Inv.end.R")

    # ----------------------------------------
    # Save outputs
    # ----------------------------------------

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path.with_suffix(".png"), dpi=300, bbox_inches="tight", pad_inches=0.12, facecolor="white")
    fig.savefig(output_path.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.12, facecolor="white")

    plt.close(fig)


if __name__ == "__main__":
    args = parse_args()
    create_diagram(args.output)
