from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import ultraplot as uplt


DEFAULT_INPUT = (
    Path(__file__).resolve().parent.parent / "data" / "multiple_data.xlsx"
)
LAND_COVERS = ("cropland", "forest", "grassland", "savanna")
MODELS = ("DNN", "GBRT", "LR", "SVR")
EXPORT_DPI = 1000
OUTPUT_STEM = "correlation_scatter"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot _0 versus _1 for four land covers and four models."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Input Excel workbook (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory for PDF and PNG outputs (default: script directory)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    required = [
        f"{land_cover}{model}_{suffix}"
        for land_cover, model, suffix in product(LAND_COVERS, MODELS, (0, 1))
    ]

    data = pd.read_excel(args.input, sheet_name=0)
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    values = data[required].apply(pd.to_numeric, errors="raise")
    observed = values.to_numpy(dtype=float)
    observed = observed[~np.isnan(observed)]
    if observed.size == 0:
        raise ValueError("The required columns contain no observed values.")
    if not np.isfinite(observed).all():
        raise ValueError("The required columns contain infinite values.")

    data_span = float(np.ptp(observed))
    if data_span == 0:
        raise ValueError("A scatter plot requires a non-zero data range.")
    padding = 0.04 * data_span
    limits = (float(observed.min() - padding), float(observed.max() + padding))

    fig, axs = uplt.subplots(
        nrows=len(LAND_COVERS),
        ncols=len(MODELS),
        order="C",
        share=3,
        span=False,
        refaspect=1,
        journal="nat2",
        tight=True,
    )

    for ax, (land_cover, model) in zip(axs, product(LAND_COVERS, MODELS)):
        x_column = f"{land_cover}{model}_0"
        y_column = f"{land_cover}{model}_1"
        pair = values[[x_column, y_column]].dropna()
        if len(pair) < 2:
            raise ValueError(f"{land_cover} {model} has fewer than two paired values.")

        x = pair[x_column].to_numpy()
        y = pair[y_column].to_numpy()
        if np.ptp(x) == 0 or np.ptp(y) == 0:
            raise ValueError(f"{land_cover} {model} contains a constant variable.")
        correlation = float(np.corrcoef(x, y)[0, 1])

        ax.plot(
            limits,
            limits,
            color="black",
            linestyle="--",
            linewidth=0.7,
            alpha=0.5,
            zorder=1,
        )
        ax.scatter(
            x,
            y,
            s=2,
            alpha=0.28,
            edgecolors="none",
            rasterized=True,
            zorder=2,
        )
        ax.text(
            0.96,
            0.05,
            f"$r$ = {correlation:.3f}\n$n$ = {len(pair):,}",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize="small",
        )

    axs.format(
        abc="a.",
        abcloc="ul",
        xlabel="_0",
        ylabel="_1",
        xlim=limits,
        ylim=limits,
        aspect="equal",
        toplabels=MODELS,
        leftlabels=tuple(name.capitalize() for name in LAND_COVERS),
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig.save(args.output_dir / f"{OUTPUT_STEM}.pdf", dpi=EXPORT_DPI)
    fig.save(args.output_dir / f"{OUTPUT_STEM}.png", dpi=EXPORT_DPI)


if __name__ == "__main__":
    main()
