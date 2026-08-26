"""Create a publication-ready 4 x 4 correlation scatter figure with UltraPlot."""

import os
from pathlib import Path
import sys


GDAL_DATA_DIR = Path(sys.prefix) / "Library" / "share" / "gdal"
if GDAL_DATA_DIR.is_dir():
    os.environ.setdefault("GDAL_DATA", str(GDAL_DATA_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from scipy.stats import linregress
import ultraplot as uplt


OUTPUT_DIR = Path(__file__).resolve().parent
INPUT_FILE = OUTPUT_DIR.parent / "data" / "multiple_data.xlsx"
PNG_FILE = OUTPUT_DIR / "correlation_scatter_ultraplot.png"
PDF_FILE = OUTPUT_DIR / "correlation_scatter_ultraplot.pdf"

LAND_COVERS = ("cropland", "forest", "grassland", "savanna")
MODELS = ("DNN", "GBRT", "LR", "SVR")
MODEL_COLORS = {
    "DNN": "#0072B2",
    "GBRT": "#009E73",
    "LR": "#D55E00",
    "SVR": "#CC79A7",
}


def load_pairs():
    """Load and validate all land-cover/model pairs from the workbook."""
    data = pd.read_excel(INPUT_FILE, sheet_name=0, engine="openpyxl")
    expected = [
        f"{land}{model}_{suffix}"
        for land in LAND_COVERS
        for model in MODELS
        for suffix in (0, 1)
    ]
    missing = sorted(set(expected).difference(data.columns))
    if missing:
        raise ValueError(f"Workbook is missing required columns: {missing}")

    pairs = {}
    for land in LAND_COVERS:
        for model in MODELS:
            columns = [f"{land}{model}_0", f"{land}{model}_1"]
            pair = data.loc[:, columns].apply(pd.to_numeric, errors="coerce").dropna()
            if len(pair) < 3:
                raise ValueError(f"Insufficient paired observations for {land} / {model}")
            pairs[(land, model)] = (
                pair.iloc[:, 0].to_numpy(dtype=float),
                pair.iloc[:, 1].to_numpy(dtype=float),
            )
    return pairs


def common_limits(pairs):
    """Return common, rounded limits so every panel is directly comparable."""
    values = np.concatenate([array for pair in pairs.values() for array in pair])
    lower = 10.0 * np.floor(values.min() / 10.0)
    upper = 10.0 * np.ceil(values.max() / 10.0)
    if lower == upper:
        lower -= 10.0
        upper += 10.0
    return float(lower), float(upper)


def configure_style():
    """Set reproducible export and typography defaults."""
    matplotlib.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.0,
            "axes.linewidth": 0.65,
            "axes.unicode_minus": True,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
            "savefig.edgecolor": "white",
        }
    )


def make_figure(pairs):
    """Build the multi-panel figure and return it with panel statistics."""
    configure_style()
    lower, upper = common_limits(pairs)
    major_ticks = np.arange(
        20.0 * np.ceil(lower / 20.0), upper + 0.1, 20.0
    )
    major_ticks = major_ticks[(major_ticks > lower) & (major_ticks < upper)]
    minor_ticks = np.arange(lower, upper + 0.1, 10.0)

    fig, axes = uplt.subplots(
        nrows=len(LAND_COVERS),
        ncols=len(MODELS),
        refwidth=1.42,
        refheight=1.42,
        share=False,
        hspace=0.12,
        wspace=0.12,
    )
    fig.patch.set_facecolor("white")
    statistics = []

    for row, land in enumerate(LAND_COVERS):
        for col, model in enumerate(MODELS):
            ax = axes[row, col]
            x, y = pairs[(land, model)]
            fit = linregress(x, y)
            rmse = float(np.sqrt(np.mean(np.square(y - x))))
            statistics.append((land, model, len(x), fit.rvalue, rmse))

            ax.plot(
                [lower, upper],
                [lower, upper],
                color="#6F6F6F",
                linewidth=0.8,
                linestyle=(0, (4, 2.5)),
                zorder=1,
            )
            ax.scatter(
                x,
                y,
                s=5.0,
                color=MODEL_COLORS[model],
                alpha=0.23,
                edgecolors="none",
                rasterized=True,
                zorder=2,
            )
            fit_x = np.linspace(x.min(), x.max(), 200)
            ax.plot(
                fit_x,
                fit.intercept + fit.slope * fit_x,
                color=MODEL_COLORS[model],
                linewidth=1.35,
                zorder=3,
            )

            ax.set_xlim(lower, upper)
            ax.set_ylim(lower, upper)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xticks(major_ticks)
            ax.set_yticks(major_ticks)
            ax.set_xticks(minor_ticks, minor=True)
            ax.set_yticks(minor_ticks, minor=True)
            ax.set_axisbelow(True)
            ax.grid(which="major", color="#D9D9D9", linewidth=0.48, alpha=0.72)
            ax.grid(which="minor", visible=False)
            ax.tick_params(
                which="major",
                direction="out",
                length=2.8,
                width=0.6,
                pad=1.6,
                labelsize=6.8,
                labelbottom=(row == len(LAND_COVERS) - 1),
                labelleft=(col == 0),
                top=False,
                right=False,
            )
            ax.tick_params(which="minor", direction="out", length=1.5, width=0.45)
            for spine in ax.spines.values():
                spine.set_color("#4D4D4D")
                spine.set_linewidth(0.65)

            ax.text(
                0.045,
                0.955,
                f"$r$ = {fit.rvalue:.2f}\nRMSE = {rmse:.2f}\n$n$ = {len(x):,}",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=6.8,
                linespacing=1.18,
                color="#222222",
                bbox={
                    "boxstyle": "square,pad=0.18",
                    "facecolor": "white",
                    "edgecolor": "none",
                    "alpha": 0.80,
                },
                zorder=5,
            )
            panel_letter = chr(ord("a") + row * len(MODELS) + col)
            ax.text(
                0.955,
                0.045,
                f"({panel_letter})",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=7.2,
                fontweight="bold",
                color="#222222",
                zorder=5,
            )

            if row == 0:
                ax.set_title(model, fontsize=9.2, fontweight="bold", pad=4.0)
            if col == 0:
                ax.text(
                    -0.22,
                    0.5,
                    land.capitalize(),
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    rotation=90,
                    fontsize=8.2,
                    fontweight="bold",
                    color="#222222",
                    clip_on=False,
                )

    fig.suptitle(
        "Relationships between _0 and _1 across land-cover classes",
        fontsize=10.5,
        fontweight="bold",
        y=0.995,
    )
    fig.supxlabel("Value (_0)", fontsize=9.0, y=0.049)
    fig.supylabel("Value (_1)", fontsize=9.0, x=0.006)

    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markersize=4.0,
            markerfacecolor="#707070",
            markeredgecolor="none",
            alpha=0.65,
            label="Paired observations",
        ),
        Line2D([0], [0], color="#303030", linewidth=1.35, label="OLS fit"),
        Line2D(
            [0],
            [0],
            color="#6F6F6F",
            linewidth=0.8,
            linestyle=(0, (4, 2.5)),
            label="1:1 reference",
        ),
    ]
    fig.legend(
        handles=legend_handles,
        loc="bottom",
        ncols=3,
        frameon=False,
        fontsize=7.4,
        handlelength=2.2,
        columnspacing=1.8,
    )
    return fig, statistics


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pairs = load_pairs()
    fig, statistics = make_figure(pairs)
    fig.savefig(PDF_FILE, dpi=600, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(PNG_FILE, dpi=600, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)

    for land, model, count, correlation, rmse in statistics:
        print(
            f"{land:10s} {model:4s}  n={count:4d}  "
            f"r={correlation:.3f}  RMSE={rmse:.3f}"
        )
    print(f"Saved: {PDF_FILE}")
    print(f"Saved: {PNG_FILE}")


if __name__ == "__main__":
    main()
