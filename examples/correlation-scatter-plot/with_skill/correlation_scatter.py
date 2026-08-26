from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import ultraplot as uplt


LAND_COVERS = ("cropland", "forest", "grassland", "savanna")
LAND_LABELS = ("Cropland", "Forest", "Grassland", "Savanna")
MODELS = ("DNN", "GBRT", "LR", "SVR")
DEFAULT_INPUT = (
    Path(__file__).resolve().parent.parent / "data" / "multiple_data.xlsx"
)
EXPORT_DPI = 1000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot paired _0 and _1 values by land cover and model."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parent
    )
    return parser.parse_args()


def load_pairs(path: Path) -> tuple[dict[tuple[str, str], pd.DataFrame], tuple[float, float]]:
    if not path.is_file():
        raise FileNotFoundError(f"Input workbook not found: {path}")

    data = pd.read_excel(path)
    required = [
        f"{land}{model}_{suffix}"
        for land in LAND_COVERS
        for model in MODELS
        for suffix in (0, 1)
    ]
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    pairs: dict[tuple[str, str], pd.DataFrame] = {}
    plotted_values: list[np.ndarray] = []
    for land in LAND_COVERS:
        for model in MODELS:
            columns = [f"{land}{model}_0", f"{land}{model}_1"]
            pair = data.loc[:, columns]
            if not pair[columns[0]].isna().equals(pair[columns[1]].isna()):
                raise ValueError(f"Unpaired missing value(s) in {land} / {model}")
            pair = pair.dropna()
            if pair.empty:
                raise ValueError(f"No paired observations for {land} / {model}")
            values = pair.to_numpy(dtype=float)
            if not np.isfinite(values).all():
                raise ValueError(f"Non-finite paired value(s) in {land} / {model}")
            pairs[(land, model)] = pair
            plotted_values.append(values.ravel())

    all_values = np.concatenate(plotted_values)
    data_min, data_max = float(all_values.min()), float(all_values.max())
    pad = 0.03 * (data_max - data_min)
    return pairs, (data_min - pad, data_max + pad)


def main() -> None:
    args = parse_args()
    pairs, limits = load_pairs(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fig, axs = uplt.subplots(
        nrows=len(LAND_COVERS),
        ncols=len(MODELS),
        journal="nat2",
        share=True,
        tight=True,
    )

    for ax, land, model in zip(
        axs,
        np.repeat(LAND_COVERS, len(MODELS)),
        np.tile(MODELS, len(LAND_COVERS)),
    ):
        pair = pairs[(land, model)]
        x = pair.iloc[:, 0].to_numpy()
        y = pair.iloc[:, 1].to_numpy()
        correlation = np.corrcoef(x, y)[0, 1]

        ax.plot(
            limits,
            limits,
            color="black",
            linewidth=0.7,
            linestyle="--",
            alpha=0.65,
            zorder=1,
        )
        ax.scatter(
            x,
            y,
            s=2.2,
            alpha=0.24,
            edgecolors="none",
            rasterized=True,
            zorder=2,
        )
        ax.text(
            0.96,
            0.05,
            rf"$r$ = {correlation:.2f}" + "\n" + rf"$n$ = {len(pair):,}",
            transform="axes",
            ha="right",
            va="bottom",
            fontsize=6.5,
        )

    axs.format(
        xlim=limits,
        ylim=limits,
        aspect=1,
        xlabel="_0",
        ylabel="_1",
        toplabels=MODELS,
        leftlabels=LAND_LABELS,
        abc="a.",
        abcloc="ul",
    )

    output_base = args.output_dir / "correlation_scatter"
    fig.save(output_base.with_suffix(".pdf"), dpi=EXPORT_DPI)
    fig.save(output_base.with_suffix(".png"), dpi=EXPORT_DPI)
    uplt.close(fig)


if __name__ == "__main__":
    main()
