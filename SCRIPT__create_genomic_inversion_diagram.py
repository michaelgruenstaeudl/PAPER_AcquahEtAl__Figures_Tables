#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib.pyplot as plt

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


def create_diagram(output_path):
    # ----------------------------------------
    # Create figure and axis
    # ----------------------------------------
    fig, ax = plt.subplots(figsize=(10, 3.8))

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # ----------------------------------------
    # Helper functions
    # ----------------------------------------
    def draw_arrow(x1, y1, x2, y2, label, label_offset=3):
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="->",
                lw=1.0,
                shrinkA=0,
                shrinkB=0,
            ),
        )

        ax.text(
            (x1 + x2) / 2,
            y1 + label_offset,
            label,
            ha="center",
            va="bottom",
            fontsize=9,
        )

    def draw_break(x, y, height=8):
        ax.plot(
            [x - 0.4, x + 0.4],
            [y - height / 2, y + height / 2],
            color="black",
            lw=1.0,
        )

    def draw_genome(y):
        ax.plot(
            [3, 97],
            [y, y],
            color="black",
            lw=1.0,
        )

    # ----------------------------------------
    # Coordinates
    # ----------------------------------------
    xA = 13
    xB = 82

    # ----------------------------------------
    # Top genome
    # ----------------------------------------
    draw_genome(78)

    draw_break(xA, 78)
    draw_break(xB, 78)

    draw_arrow(4, 92, 21, 92, "Forward A")
    draw_arrow(20, 87, 4, 87, "Reverse A")

    draw_arrow(73, 92, 92, 92, "Forward B")
    draw_arrow(91, 87, 73, 87, "Reverse B")

    ax.text(
        13,
        64,
        "Inversion Start (A)",
        fontsize=9,
        ha="center",
        va="center",
    )

    ax.text(
        82,
        64,
        "Inversion End (B)",
        fontsize=9,
        ha="center",
        va="center",
    )

    # ----------------------------------------
    # Middle genome
    # ----------------------------------------
    draw_genome(48)

    draw_break(xA, 48)
    draw_break(xB, 48)

    # ----------------------------------------
    # Bottom genome
    # ----------------------------------------
    draw_genome(25)

    draw_break(xA, 25)
    draw_break(xB, 25)

    draw_arrow(3, 15, 22, 15, "Forward A")
    draw_arrow(20, 10, 4, 10, "Reverse B")

    draw_arrow(73, 15, 92, 15, "Forward B")
    draw_arrow(91, 10, 73, 10, "Reverse A")

    # ----------------------------------------
    # Save outputs
    # ----------------------------------------
    plt.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        output_path.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        output_path.with_suffix(".svg"),
        bbox_inches="tight",
    )

    plt.close(fig)


if __name__ == "__main__":
    args = parse_args()
    create_diagram(args.output)
