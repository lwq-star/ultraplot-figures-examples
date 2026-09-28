"""Create a publication-ready 4 x 4 correlation-scatter matrix with UltraPlot."""

from __future__ import annotations

import argparse
import string
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.figure import Figure as MatplotlibFigure
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import ultraplot as uplt


DEFAULT_INPUT = (
    Path(__file__).resolve().parent.parent / "data" / "multiple_data.xlsx"
)

LAND_COVERS = (
    ("cropland", "Cropland"),
    ("forest", "Forest"),
    ("grassland", "Grassland"),
    ("savanna", "Savanna"),
)
MODELS = ("DNN", "GBRT", "LR", "SVR")
MODEL_COLORS = {
    "DNN": "#0072B2",
    "GBRT": "#D55E00",
    "LR": "#009E73",
    "SVR": "#CC79A7",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot _0 versus _1 for four land covers and four models."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Input Excel workbook (default: %(default)s).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory for PDF and PNG outputs (default: script directory).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
        help="PNG resolution in dots per inch (default: %(default)s).",
    )
    return parser.parse_args()


def required_columns() -> list[str]:
    return [
        f"{land}{model}_{suffix}"
        for land, _ in LAND_COVERS
        for model in MODELS
        for suffix in (0, 1)
    ]


def load_data(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Input workbook not found: {path}")

    data = pd.read_excel(path, sheet_name=0)
    missing = [column for column in required_columns() if column not in data.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    return data


def finite_pair(data: pd.DataFrame, land: str, model: str) -> tuple[np.ndarray, np.ndarray]:
    columns = [f"{land}{model}_0", f"{land}{model}_1"]
    pair = data[columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    pair = pair[np.isfinite(pair).all(axis=1)]
    if len(pair) < 2:
        raise ValueError(f"Fewer than two finite pairs for {land} / {model}.")
    return pair[:, 0], pair[:, 1]


def common_limits(data: pd.DataFrame) -> tuple[float, float]:
    values = (
        data[required_columns()]
        .apply(pd.to_numeric, errors="coerce")
        .to_numpy(dtype=float)
    )
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        raise ValueError("The required columns contain no finite numeric values.")

    lower = float(np.floor(finite.min() / 5.0) * 5.0)
    upper = float(np.ceil(finite.max() / 5.0) * 5.0)
    if lower == upper:
        lower -= 1.0
        upper += 1.0
    return lower, upper


def draw_figure(data: pd.DataFrame) -> mpl.figure.Figure:
    limits = common_limits(data)
    tick_start = np.ceil(limits[0] / 20.0) * 20.0
    ticks = np.arange(tick_start, limits[1] + 0.01, 20.0)

    style = {
        "font.family": "DejaVu Sans",
        "font.size": 7.5,
        "axes.linewidth": 0.65,
        "axes.edgecolor": "#6A6A6A",
        "axes.labelcolor": "#202020",
        "xtick.color": "#303030",
        "ytick.color": "#303030",
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 2.8,
        "ytick.major.size": 2.8,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }

    with mpl.rc_context(style):
        fig, axes = uplt.subplots(
            nrows=4,
            ncols=4,
            figsize=(7.35, 7.55),
            share=True,
            span=False,
            left="0.66in",
            right="0.55in",
            bottom="0.82in",
            top="0.62in",
            wspace="0.07in",
            hspace="0.07in",
        )

        panel_labels = iter(string.ascii_lowercase)
        for row, (land_key, land_label) in enumerate(LAND_COVERS):
            for col, model in enumerate(MODELS):
                ax = axes[row, col]
                color = MODEL_COLORS[model]
                x, y = finite_pair(data, land_key, model)

                correlation = float(np.corrcoef(x, y)[0, 1])
                rmse = float(np.sqrt(np.mean(np.square(y - x))))
                slope, intercept = np.polyfit(x, y, 1)
                fit_x = np.array([x.min(), x.max()])

                ax.scatter(
                    x,
                    y,
                    s=5.2,
                    color=color,
                    alpha=0.22,
                    edgecolors="none",
                    rasterized=True,
                    zorder=2,
                )
                ax.plot(
                    limits,
                    limits,
                    color="#5D6368",
                    linewidth=0.85,
                    linestyle=(0, (3.0, 2.2)),
                    zorder=1,
                )
                ax.plot(
                    fit_x,
                    slope * fit_x + intercept,
                    color=color,
                    linewidth=1.35,
                    solid_capstyle="round",
                    zorder=3,
                )

                ax.set_xlim(limits)
                ax.set_ylim(limits)
                ax.set_xticks(ticks)
                ax.set_yticks(ticks)
                ax.set_aspect("equal", adjustable="box")
                ax.set_axisbelow(True)
                ax.grid(
                    True,
                    color="#D8DADD",
                    linewidth=0.45,
                    linestyle=(0, (1.2, 2.4)),
                    alpha=0.9,
                )
                ax.tick_params(
                    labelsize=6.8,
                    labelbottom=row == len(LAND_COVERS) - 1,
                    labelleft=col == 0,
                    pad=2.0,
                )

                panel = next(panel_labels)
                ax.text(
                    0.045,
                    0.955,
                    f"({panel})",
                    transform=ax.transAxes,
                    ha="left",
                    va="top",
                    fontsize=7.5,
                    fontweight="bold",
                    color="#202020",
                    zorder=5,
                )
                ax.text(
                    0.955,
                    0.055,
                    f"$r$ = {correlation:.3f}\nRMSE = {rmse:.2f}\n$n$ = {len(x):,}",
                    transform=ax.transAxes,
                    ha="right",
                    va="bottom",
                    fontsize=6.3,
                    linespacing=1.18,
                    color="#202020",
                    bbox={
                        "facecolor": "white",
                        "edgecolor": "none",
                        "alpha": 0.84,
                        "pad": 1.25,
                    },
                    zorder=5,
                )

                if row == 0:
                    ax.set_title(
                        model,
                        fontsize=9.2,
                        fontweight="bold",
                        color=color,
                        pad=5.5,
                    )
                if col == len(MODELS) - 1:
                    ax.text(
                        1.065,
                        0.5,
                        land_label,
                        transform=ax.transAxes,
                        rotation=270,
                        ha="left",
                        va="center",
                        fontsize=8.3,
                        fontweight="semibold",
                        color="#303030",
                        clip_on=False,
                    )

        fig.suptitle(
            "Paired-variable relationships by land cover and model",
            x=0.505,
            y=0.975,
            fontsize=11.2,
            fontweight="semibold",
            color="#202020",
        )
        fig.text(
            0.505,
            0.066,
            "Value (_0)",
            ha="center",
            va="center",
            fontsize=9.2,
            fontweight="medium",
            color="#202020",
        )
        fig.text(
            0.028,
            0.512,
            "Value (_1)",
            ha="center",
            va="center",
            rotation=90,
            fontsize=9.2,
            fontweight="medium",
            color="#202020",
        )

        legend_handles = [
            Line2D(
                [0],
                [0],
                color="#5D6368",
                linewidth=0.9,
                linestyle=(0, (3.0, 2.2)),
            ),
            Line2D([0], [0], color="#303030", linewidth=1.35),
        ]
        MatplotlibFigure.legend(
            fig,
            legend_handles,
            ["1:1 reference", "OLS fit (model color)"],
            loc="lower center",
            bbox_to_anchor=(0.505, 0.010),
            ncol=2,
            frameon=False,
            fontsize=7.2,
            handlelength=2.8,
            columnspacing=2.0,
        )

    return fig


def main() -> None:
    args = parse_args()
    if args.dpi <= 0:
        raise ValueError("--dpi must be a positive integer.")

    input_path = args.input.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_data(input_path)
    figure = draw_figure(data)
    pdf_path = output_dir / "correlation_scatter_ultraplot.pdf"
    png_path = output_dir / "correlation_scatter_ultraplot.png"

    figure.savefig(
        pdf_path,
        dpi=args.dpi,
        facecolor="white",
        metadata={
            "Title": "Correlation scatter plots by land cover and model",
            "Creator": "UltraPlot",
        },
    )
    figure.savefig(
        png_path,
        dpi=args.dpi,
        facecolor="white",
        metadata={"Software": "UltraPlot"},
    )
    plt.close(figure)

    print(f"Read {len(data):,} rows from {input_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {png_path} at {args.dpi} dpi")


if __name__ == "__main__":
    main()
