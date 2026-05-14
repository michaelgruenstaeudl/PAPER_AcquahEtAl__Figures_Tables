#!/usr/bin/env python3
"""
Create horizontally stacked diversity-index bar charts from summary text files.

Expected per-file content example:
Raw reads: 91377
ASV method: DADA2
Number of ASVs: 272
Number of genera: 67
Number of families: 46
Shannon diversity: 6.341
Pielou evenness: 0.784
Simpson diversity: 0.972

Behavior
--------
- Reads all regular files in an input folder
- Selects only files that contain "Number of ASVs:"
- Parses key:value lines
- Uses all numeric metrics starting at and including "Number of ASVs"
- Creates one bar chart per selected metric across all samples
- Arranges subplots horizontally in a single row
- Adds figure supertitle "(b) Diversity indices"
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


START_METRIC = "Number of ASVs"
SUPERTITLE = "(b) Diversity indices"


def parse_metadata(metadata_path: Path) -> tuple[Dict[str, str], List[str]]:
    mapping: Dict[str, str] = {}
    order: List[str] = []

    with metadata_path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for line_number, row in enumerate(reader, start=1):
            if not row:
                continue
            if row[0].strip().startswith("#"):
                continue
            if len(row) < 2:
                raise ValueError(
                    f"{metadata_path}: line {line_number} malformed "
                    "(expected at least 2 comma-separated columns: file_name,sample_name)"
                )

            file_name = row[0].strip()
            sample_name = row[1].strip()

            if not file_name or not sample_name:
                raise ValueError(
                    f"{metadata_path}: line {line_number} must include file_name and sample_name."
                )

            file_path = Path(file_name)
            mapping[file_path.name] = sample_name
            mapping[file_path.stem] = sample_name
            order.append(sample_name)

    return mapping, order


def parse_summary_file(file_path: Path) -> Dict[str, float]:
    fields: Dict[str, float] = {}

    with file_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            try:
                numeric_value = float(value)
            except ValueError:
                continue

            fields[key] = numeric_value

    return fields


def detect_metric_order(file_path: Path) -> List[str]:
    metrics: List[str] = []
    started = False

    with file_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if key == START_METRIC:
                started = True

            if not started:
                continue

            try:
                float(value)
            except ValueError:
                continue

            metrics.append(key)

    return metrics


def collect_sample_metrics(
    folder: Path,
    metadata_map: Dict[str, str] | None = None,
    metadata_order: List[str] | None = None,
) -> tuple[List[str], List[str], Dict[str, Dict[str, float]]]:
    if metadata_map is None or metadata_order is None:
        raise ValueError("A metadata CSV is required for sample labels and sample ordering.")

    files = sorted([p for p in folder.iterdir() if p.is_file()])

    if not files:
        raise FileNotFoundError(f"No input files found in {folder}")

    selected_files: List[Path] = []
    for file_path in files:
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if f"{START_METRIC}:" in text:
            selected_files.append(file_path)

    if not selected_files:
        raise FileNotFoundError(
            f"No files containing '{START_METRIC}:' found in {folder}"
        )

    metric_order = detect_metric_order(selected_files[0])
    if not metric_order:
        raise ValueError(
            f"Could not detect numeric metrics from '{START_METRIC}' onward in {selected_files[0]}"
        )

    sample_values: Dict[str, Dict[str, float]] = {}

    for file_path in selected_files:
        parsed = parse_summary_file(file_path)

        missing = [metric for metric in metric_order if metric not in parsed]
        if missing:
            missing_str = ", ".join(missing)
            raise ValueError(f"{file_path} missing required metrics: {missing_str}")

        sample_name = file_path.stem
        mapped_name = metadata_map.get(file_path.name) or metadata_map.get(file_path.stem)
        if mapped_name is None:
            raise ValueError(
                f"{file_path} is missing in metadata mapping (file_name -> sample_name)."
            )
        sample_name = mapped_name

        sample_values[sample_name] = {metric: parsed[metric] for metric in metric_order}

    sample_names = [name for name in metadata_order if name in sample_values]

    if not sample_names:
        raise ValueError("No samples from metadata were found in input files.")

    return sample_names, metric_order, sample_values


def plot_horizontal_metric_panels(
    sample_names: List[str],
    metric_order: List[str],
    sample_values: Dict[str, Dict[str, float]],
    output_prefix: Path,
) -> None:
    panel_count = len(metric_order)
    bar_height = 0.512
    y_step = 0.712
    y_positions = [i * y_step for i in range(len(sample_names))]

    base_fig_height = max(4, 0.44 * len(sample_names))
    fig, axes = plt.subplots(
        1,
        panel_count,
        figsize=(max(4.2 * panel_count, 12), base_fig_height * 0.8),
        squeeze=False,
    )
    axes_row = axes[0]

    for idx, metric in enumerate(metric_order):
        ax = axes_row[idx]
        values = [sample_values[sample][metric] for sample in sample_names]
        metric_min = min(values)
        metric_max = max(values)
        metric_span = metric_max - metric_min

        if metric_span == 0:
            padding = max(0.05 * abs(metric_min), 0.1)
        else:
            padding = 0.12 * metric_span

        ax.barh(
            y_positions,
            values,
            height=bar_height,
            color="0.65",
            edgecolor="white",
            linewidth=0.8,
        )
        ax.set_yticks(y_positions)
        ax.set_yticklabels(sample_names)
        if idx < 3:
            ax.set_xlim(0, metric_max + padding)
        else:
            ax.set_xlim(metric_min - padding, metric_max + padding)
        ax.set_title(metric, fontsize=13)
        ax.grid(axis="x", linestyle=":", linewidth=0.7, alpha=0.5)

        if metric.strip().casefold() == "simpson diversity":
            ax.xaxis.set_major_locator(MaxNLocator(nbins=4))

        if idx == 0:
            ax.tick_params(axis="y", labelsize=13)
        else:
            ax.tick_params(axis="y", left=False, labelleft=False)

    plt.tight_layout()

    fig.savefig(output_prefix.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(output_prefix.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path, help="Folder with per-sample summary files")
    parser.add_argument("-o", "--output-prefix", required=True, type=Path)
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional CSV metadata file mapping file_name,sample_name for labels/order.",
    )

    args = parser.parse_args()

    metadata_map = None
    metadata_order = None
    if args.metadata is not None:
        metadata_map, metadata_order = parse_metadata(args.metadata)

    sample_names, metric_order, sample_values = collect_sample_metrics(
        folder=args.folder,
        metadata_map=metadata_map,
        metadata_order=metadata_order,
    )

    plot_horizontal_metric_panels(
        sample_names=sample_names,
        metric_order=metric_order,
        sample_values=sample_values,
        output_prefix=args.output_prefix,
    )


if __name__ == "__main__":
    main()
