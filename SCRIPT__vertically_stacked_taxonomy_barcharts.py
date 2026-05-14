#!/usr/bin/env python3
"""
Create stacked horizontal bar charts from multiple TSV taxonomy tables.

Features
--------
- Reads all .tsv files from a folder
- Ignores comment lines starting with '#'
- Ignores lines starting with 'Unassigned'
- Normalizes each file to percentages
- Automatically creates an "Other" category:
    all groups with less than X percent within a given bar are merged into "Other"
- Creates four figures automatically in this order:
    class, order, family, genus
- Uses a fixed global category order across all bars:
    class -> order -> family -> genus
    with Cyanobacteria forced to the leftmost position
- Uses class-correlated colors across ranks:
    each class gets a base color and lower ranks use shades of that class color
    Cyanobacteria is always blue
- Optional metadata CSV file:
    maps file names to sample names used as y-axis labels and sample order
"""

from __future__ import annotations

import argparse
import colorsys
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import pandas as pd


VALID_RANKS = ("d", "p", "c", "o", "f", "g")
PLOT_RANKS = ("c", "o", "f", "g")
RANK_LABELS = {
    "d": "Domain",
    "p": "Phylum",
    "c": "Class",
    "o": "Order",
    "f": "Family",
    "g": "Genus",
}

TaxonKey = Tuple[str, str, str, str, str]  # phylum, class, order, family, genus
CYANO_TOKEN = "cyanobacter"


def parse_taxonomy_field(taxonomy: str) -> Dict[str, str]:
    parsed: Dict[str, str] = {}

    for part in taxonomy.strip().split(";"):
        part = part.strip()
        if "__" not in part:
            continue

        rank, value = part.split("__", 1)
        rank = rank.strip()
        value = value.strip()

        if rank in VALID_RANKS:
            parsed[rank] = value

    return parsed


def normalize_label(label: str) -> str:
    if not label or label == "__":
        return "Unclassified"
    return label


def _sort_value(text: str) -> str:
    if not text or text == "Unclassified":
        return "zzzz_unclassified"
    return text.casefold()


def is_cyanobacteria_text(text: str) -> bool:
    return CYANO_TOKEN in _sort_value(text)


def is_cyanobacteria_category(category: str, category_keys: Dict[str, TaxonKey]) -> bool:
    p_name, c_name, o_name, f_name, g_name = category_keys.get(
        category,
        ("Unclassified", "Unclassified", "Unclassified", "Unclassified", "Unclassified"),
    )
    return any(
        is_cyanobacteria_text(value)
        for value in (category, p_name, c_name, o_name, f_name, g_name)
    )


def read_metadata(metadata_path: Path) -> Dict[str, str]:
    mapping: Dict[str, str] = {}

    with metadata_path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for line_number, parts in enumerate(reader, start=1):
            if not parts:
                continue
            if parts[0].strip().startswith("#"):
                continue

            if len(parts) < 2:
                raise ValueError(
                    f"{metadata_path}: line {line_number} malformed "
                    "(expected at least 2 comma-separated columns: file_name and sample_name)"
                )

            file_name = parts[0].strip()
            sample_name = parts[1].strip()

            if not file_name:
                raise ValueError(
                    f"{metadata_path}: line {line_number} has an empty file name."
                )
            if not sample_name:
                raise ValueError(
                    f"{metadata_path}: line {line_number} has an empty sample name."
                )

            mapping[file_name] = sample_name

            file_path = Path(file_name)
            mapping[file_path.stem] = sample_name
            if file_path.suffix != ".tsv":
                mapping[file_path.name + ".tsv"] = sample_name

    return mapping


def read_metadata_order(metadata_path: Path) -> list[str]:
    order: list[str] = []

    with metadata_path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for parts in reader:
            if not parts:
                continue
            if parts[0].strip().startswith("#"):
                continue

            if len(parts) < 2:
                continue

            sample_name = parts[1].strip()
            if sample_name:
                order.append(sample_name)

    return order


def read_and_aggregate_tsv(
    file_path: Path,
    rank: str,
) -> Tuple[Dict[str, float], Dict[str, TaxonKey]]:
    aggregated: Dict[str, float] = defaultdict(float)
    taxonomy_keys: Dict[str, TaxonKey] = {}

    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()

            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith("Unassigned"):
                continue

            parts = line.split("\t")
            if len(parts) < 2:
                raise ValueError(
                    f"{file_path}: line {line_number} malformed (expected at least 2 columns)"
                )

            taxonomy = parts[0].strip()
            value_str = parts[1].strip()

            try:
                value = float(value_str)
            except ValueError as exc:
                raise ValueError(
                    f"{file_path}: line {line_number} has invalid numeric value {value_str!r}"
                ) from exc

            taxonomy_map = parse_taxonomy_field(taxonomy)
            label = normalize_label(taxonomy_map.get(rank, "Unclassified"))

            aggregated[label] += value
            taxonomy_keys[label] = (
                normalize_label(taxonomy_map.get("p", "Unclassified")),
                normalize_label(taxonomy_map.get("c", "Unclassified")),
                normalize_label(taxonomy_map.get("o", "Unclassified")),
                normalize_label(taxonomy_map.get("f", "Unclassified")),
                normalize_label(taxonomy_map.get("g", "Unclassified")),
            )

    return dict(aggregated), taxonomy_keys


def taxonomy_category_sort_key(
    category: str,
    category_keys: Dict[str, TaxonKey],
) -> Tuple[int, str, str, str, str, str]:
    _, cls_name, ord_name, fam_name, gen_name = category_keys.get(
        category,
        ("Unclassified", "Unclassified", "Unclassified", "Unclassified", "Unclassified"),
    )

    is_cyanobacteria = is_cyanobacteria_category(category, category_keys)
    cyanobacteria_first = 0 if is_cyanobacteria else 1

    return (
        cyanobacteria_first,
        _sort_value(cls_name),
        _sort_value(ord_name),
        _sort_value(fam_name),
        _sort_value(gen_name),
        _sort_value(category),
    )


def collapse_small_categories(
    percentages: Dict[str, float],
    threshold: float,
) -> Dict[str, float]:
    if threshold <= 0:
        return dict(percentages)

    collapsed: Dict[str, float] = {}
    other_total = 0.0

    for category, pct in percentages.items():
        if pct < threshold:
            other_total += pct
        else:
            collapsed[category] = pct

    if other_total > 0:
        collapsed["Other"] = other_total

    return collapsed


def collect_tables(
    folder: Path,
    rank: str,
    threshold: float,
    metadata_map: Dict[str, str] | None = None,
    metadata_path: Path | None = None,
    metadata_order: list[str] | None = None,
) -> Tuple[pd.DataFrame, Dict[str, TaxonKey]]:
    tsv_files = sorted(folder.glob("*.tsv"))

    if metadata_path is not None:
        metadata_path = metadata_path.resolve()
        tsv_files = [fp for fp in tsv_files if fp.resolve() != metadata_path]

    if not tsv_files:
        raise FileNotFoundError(f"No .tsv taxonomy files found in {folder}")

    all_tables: Dict[str, Dict[str, float]] = {}
    category_keys: Dict[str, TaxonKey] = {}

    for file_path in tsv_files:
        counts, file_category_keys = read_and_aggregate_tsv(
            file_path=file_path,
            rank=rank,
        )
        for label, key_tuple in file_category_keys.items():
            category_keys.setdefault(label, key_tuple)

        total = sum(counts.values())
        if total == 0:
            percentages = {}
        else:
            percentages = {k: (v / total) * 100.0 for k, v in counts.items()}

        percentages = collapse_small_categories(percentages, threshold)

        sample_label = file_path.stem
        if metadata_map is not None:
            sample_label = (
                metadata_map.get(file_path.name)
                or metadata_map.get(file_path.stem)
                or sample_label
            )

        all_tables[sample_label] = percentages

    df = pd.DataFrame.from_dict(all_tables, orient="index").fillna(0.0)

    if df.empty:
        raise ValueError("No valid data found.")

    df = df.loc[df.sum(axis=1) > 0]

    if df.empty:
        raise ValueError("All samples have zero abundance after processing.")

    if metadata_order is not None:
        desired = [sample for sample in metadata_order if sample in df.index]
        remaining = [sample for sample in df.index if sample not in desired]
        df = df.loc[desired + remaining]

    order = sorted(
        [c for c in df.columns if c != "Other"],
        key=lambda category: taxonomy_category_sort_key(category, category_keys),
    )

    if "Other" in df.columns:
        order.append("Other")

    return df[order], category_keys


def _build_non_blue_palette() -> list[tuple[float, float, float, float]]:
    cmap = plt.get_cmap("tab20")
    non_blue_palette: list[tuple[float, float, float, float]] = []

    for i in range(cmap.N):
        color = cmap(i)
        r, g, b, a = color
        if b > r and b > g:
            continue
        non_blue_palette.append((r, g, b, a))

    if not non_blue_palette:
        raise ValueError("No non-blue colors available for taxa color assignment.")

    return non_blue_palette


def build_class_color_map(class_labels: list[str]) -> Dict[str, tuple[float, float, float, float]]:
    cyanobacteria_color = (0.0, 0.447, 0.741, 1.0)
    class_color_map: Dict[str, tuple[float, float, float, float]] = {}

    palette = _build_non_blue_palette()

    unique_classes = sorted(
        {_sort_value(label): label for label in class_labels if label != "Other"}.values(),
        key=_sort_value,
    )

    palette_index = 0
    for cls_name in unique_classes:
        if is_cyanobacteria_text(cls_name):
            class_color_map[cls_name] = cyanobacteria_color
        else:
            class_color_map[cls_name] = palette[palette_index % len(palette)]
            palette_index += 1

    return class_color_map


def _shade_of_class_color(
    base_color: tuple[float, float, float, float],
    index: int,
    total: int,
) -> tuple[float, float, float, float]:
    if total <= 1:
        return base_color

    r, g, b, a = base_color
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)

    min_lightness = max(0.22, lightness * 0.65)
    max_lightness = min(0.86, lightness + (1.0 - lightness) * 0.35)

    frac = index / (total - 1)
    new_lightness = min_lightness + (max_lightness - min_lightness) * frac

    nr, ng, nb = colorsys.hls_to_rgb(hue, new_lightness, saturation)
    return (nr, ng, nb, a)


def build_color_map(
    columns,
    rank: str,
    category_keys: Dict[str, TaxonKey],
    class_color_map: Dict[str, tuple[float, float, float, float]],
):
    color_map = {}

    non_other = [c for c in columns if c != "Other"]

    if rank == "c":
        for category in non_other:
            if is_cyanobacteria_category(category, category_keys):
                color_map[category] = (0.0, 0.447, 0.741, 1.0)
            else:
                color_map[category] = class_color_map.get(
                    category,
                    (0.6, 0.6, 0.6, 1.0),
                )
    else:
        grouped_by_class: Dict[str, list[str]] = defaultdict(list)

        for category in non_other:
            _, cls_name, _, _, _ = category_keys.get(
                category,
                ("Unclassified", "Unclassified", "Unclassified", "Unclassified", "Unclassified"),
            )
            group_key = "__cyanobacteria__" if is_cyanobacteria_category(category, category_keys) else cls_name
            grouped_by_class[group_key].append(category)

        palette = _build_non_blue_palette()
        used_non_cyan = {
            tuple(value)
            for key, value in class_color_map.items()
            if not is_cyanobacteria_text(key)
        }
        palette_index = 0

        for cls_name in sorted(grouped_by_class.keys(), key=_sort_value):
            if cls_name == "__cyanobacteria__":
                base_color = (0.0, 0.447, 0.741, 1.0)
            else:
                if cls_name not in class_color_map:
                    if is_cyanobacteria_text(cls_name):
                        class_color_map[cls_name] = (0.0, 0.447, 0.741, 1.0)
                    else:
                        candidate = palette[palette_index % len(palette)]
                        while tuple(candidate) in used_non_cyan and palette_index < len(palette) * 2:
                            palette_index += 1
                            candidate = palette[palette_index % len(palette)]
                        class_color_map[cls_name] = candidate
                        used_non_cyan.add(tuple(candidate))
                        palette_index += 1

                base_color = class_color_map[cls_name]

            members = grouped_by_class[cls_name]
            for idx, category in enumerate(members):
                color_map[category] = _shade_of_class_color(base_color, idx, len(members))

    if "Other" in columns:
        color_map["Other"] = (0.8, 0.8, 0.8, 1.0)

    return color_map


def draw_stacked_barh(
    ax,
    df: pd.DataFrame,
    rank: str,
    threshold: float,
    category_keys: Dict[str, TaxonKey],
    class_color_map: Dict[str, tuple[float, float, float, float]],
) -> None:
    color_map = build_color_map(df.columns, rank, category_keys, class_color_map)
    left = pd.Series(0.0, index=df.index)
    y_labels = list(df.index)
    y_step = 0.82
    y_positions = [i * y_step for i in range(len(y_labels))]
    bar_height = 0.64

    for category in df.columns:
        values = df[category]
        ax.barh(
            y_positions,
            values.values,
            left=left.values,
            label=category,
            color=color_map[category],
            edgecolor="white",
            linewidth=1.0,
            height=bar_height,
        )
        left += values

    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels)

    ax.set_xlabel("Relative abundance (%)")
    ax.set_xlim(0, 100)

    title = f"{RANK_LABELS[rank]} composition (threshold < {threshold:g}% -> Other)"
    ax.set_title(title)

    legend_fontsize = float(plt.rcParams.get("font.size", 10.0)) * (2.0 / 3.0)
    legend_labelspacing = 0.5 * (2.0 / 3.0)

    labels = [str(label) for label in df.columns]
    avg_len = sum(len(label) for label in labels) / len(labels) if labels else 0.0
    outlier_cutoff = max(12, int(round(avg_len * 1.4)))
    truncate_to = max(10, int(round(avg_len * 1.2)))

    abbreviated_labels = []
    for label in labels:
        if len(label) > outlier_cutoff:
            abbreviated_labels.append(label[:truncate_to].rstrip() + "...")
        else:
            abbreviated_labels.append(label)

    handles, _ = ax.get_legend_handles_labels()

    ax.legend(
        handles,
        abbreviated_labels,
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        frameon=False,
        fontsize=legend_fontsize,
        labelspacing=legend_labelspacing,
        ncol=2,
    )


def plot_stacked_rank_panels(
    rank_results: list[tuple[str, pd.DataFrame, Dict[str, TaxonKey]]],
    output_prefix: Path,
    threshold: float,
    class_color_map: Dict[str, tuple[float, float, float, float]],
) -> None:
    if not rank_results:
        raise ValueError("No rank results available for plotting.")

    sample_count = max(len(df) for _, df, _ in rank_results)
    panel_height = max(3.5, 0.5 * sample_count) * 0.64
    fig_height = panel_height * len(rank_results)

    fig, axes = plt.subplots(
        len(rank_results),
        1,
        figsize=(16, fig_height),
    )

    if len(rank_results) == 1:
        axes = [axes]

    for ax, (rank, df, category_keys) in zip(axes, rank_results):
        draw_stacked_barh(
            ax=ax,
            df=df,
            rank=rank,
            threshold=threshold,
            category_keys=category_keys,
            class_color_map=class_color_map,
        )

    plt.tight_layout()

    fig.savefig(output_prefix.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(output_prefix.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("-o", "--output-prefix", required=True, type=Path)
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=0.0,
        help='Merge categories < threshold (%) into "Other"',
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional CSV metadata file mapping file names to sample names.",
    )

    args = parser.parse_args()

    if not (0 <= args.threshold <= 100):
        raise ValueError("Threshold must be between 0 and 100.")

    metadata_map = None
    metadata_order = None
    if args.metadata is not None:
        metadata_map = read_metadata(args.metadata)
        metadata_order = read_metadata_order(args.metadata)

    class_color_map: Dict[str, tuple[float, float, float, float]] = {}
    rank_results: list[tuple[str, pd.DataFrame, Dict[str, TaxonKey]]] = []

    for rank in PLOT_RANKS:
        df, category_keys = collect_tables(
            folder=args.folder,
            rank=rank,
            threshold=args.threshold,
            metadata_map=metadata_map,
            metadata_path=args.metadata,
            metadata_order=metadata_order,
        )

        if rank == "c":
            class_color_map = build_class_color_map(list(df.columns))

        rank_results.append((rank, df, category_keys))

    plot_stacked_rank_panels(
        rank_results=rank_results,
        output_prefix=args.output_prefix,
        threshold=args.threshold,
        class_color_map=class_color_map,
    )


if __name__ == "__main__":
    main()
