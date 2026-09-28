"""Map 2025 global M5+ earthquakes with magnitude and depth encodings.

The default paths reproduce the deliverables for this task. A different
USGS-style GeoJSON file or output directory can be supplied on the command
line without editing the script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
os.environ.setdefault("GDAL_DATA", str(Path(sys.prefix) / "Library" / "share" / "gdal"))

import cartopy.crs as ccrs
import matplotlib as mpl
import numpy as np
import ultraplot as uplt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D


DEFAULT_INPUT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "usgs_earthquakes_2025_m5plus.geojson"
)
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent
DEFAULT_BASENAME = "global_earthquakes_2025_m5plus"

DEPTH_EDGES = np.array([0.0, 35.0, 70.0, 150.0, 300.0, 700.0])
DEPTH_LABELS = ["0-34", "35-69", "70-149", "150-299", "300+"]
DEPTH_COLORS = ["#f4c95d", "#e99549", "#ce5d58", "#8d4d78", "#3f416f"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a global UltraPlot map of USGS earthquakes."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="USGS-style earthquake GeoJSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the PDF and PNG outputs.",
    )
    parser.add_argument(
        "--basename",
        default=DEFAULT_BASENAME,
        help="Output filename stem.",
    )
    return parser.parse_args()


def load_earthquakes(path: Path) -> dict[str, Any]:
    """Load and validate the fields needed from a USGS GeoJSON catalog."""
    with path.open("r", encoding="utf-8") as stream:
        catalog = json.load(stream)

    if catalog.get("type") != "FeatureCollection":
        raise ValueError(f"Expected a GeoJSON FeatureCollection: {path}")

    records: list[tuple[float, float, float, float, int, str]] = []
    for feature in catalog.get("features", []):
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        coordinates = geometry.get("coordinates") or []
        if geometry.get("type") != "Point" or len(coordinates) < 3:
            continue
        try:
            lon, lat, depth = map(float, coordinates[:3])
            magnitude = float(properties["mag"])
            epoch_ms = int(properties["time"])
        except (KeyError, TypeError, ValueError):
            continue
        if not np.all(np.isfinite([lon, lat, depth, magnitude])):
            continue
        records.append(
            (lon, lat, max(depth, 0.0), magnitude, epoch_ms, str(properties.get("place", "")))
        )

    if not records:
        raise ValueError(f"No valid point earthquakes found in {path}")

    return {
        "longitude": np.array([row[0] for row in records]),
        "latitude": np.array([row[1] for row in records]),
        "depth": np.array([row[2] for row in records]),
        "magnitude": np.array([row[3] for row in records]),
        "time": np.array([row[4] for row in records], dtype=np.int64),
        "place": np.array([row[5] for row in records], dtype=object),
        "metadata": catalog.get("metadata") or {},
    }


def marker_area(magnitude: np.ndarray | float) -> np.ndarray:
    """Convert magnitude to marker area in points squared."""
    values = np.asarray(magnitude, dtype=float)
    return 9.0 * np.power(2.25, values - 5.0)


def angular_distance_deg(
    lon1: float, lat1: float, lon2: float, lat2: float
) -> float:
    """Great-circle angular distance used to separate map annotations."""
    lon1r, lat1r, lon2r, lat2r = np.deg2rad([lon1, lat1, lon2, lat2])
    cosine = (
        np.sin(lat1r) * np.sin(lat2r)
        + np.cos(lat1r) * np.cos(lat2r) * np.cos(lon1r - lon2r)
    )
    return float(np.rad2deg(np.arccos(np.clip(cosine, -1.0, 1.0))))


def select_major_events(data: dict[str, Any], number: int = 3) -> list[int]:
    """Select large events while avoiding labels in the same cluster."""
    order = np.argsort(-data["magnitude"], kind="stable")
    selected: list[int] = []
    for index in order:
        if all(
            angular_distance_deg(
                data["longitude"][index],
                data["latitude"][index],
                data["longitude"][other],
                data["latitude"][other],
            )
            >= 25.0
            for other in selected
        ):
            selected.append(int(index))
        if len(selected) == number:
            break
    return selected


def shorten_place(place: str, limit: int = 34) -> str:
    text = place.removeprefix("2025 ").removesuffix(" Earthquake").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def event_year_and_range(epoch_ms: np.ndarray) -> tuple[str, str]:
    dates = [datetime.fromtimestamp(value / 1000, timezone.utc) for value in epoch_ms]
    years = sorted({date.year for date in dates})
    year_text = str(years[0]) if len(years) == 1 else f"{years[0]}-{years[-1]}"
    date_range = f"{min(dates):%b %d}-{max(dates):%b %d, %Y} UTC"
    return year_text, date_range


def draw_figure(data: dict[str, Any]) -> mpl.figure.Figure:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.0,
            "axes.titleweight": "bold",
            "axes.titlesize": 11.0,
            "axes.labelsize": 9.0,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "savefig.facecolor": "#fbfcfc",
        }
    )

    longitude = data["longitude"]
    latitude = data["latitude"]
    depth = data["depth"]
    magnitude = data["magnitude"]
    count = len(magnitude)
    year_text, date_range = event_year_and_range(data["time"])

    projection = uplt.Proj("robin", lon0=150)
    layout = [[1, 1], [1, 1], [1, 1], [2, 3]]
    fig, axes = uplt.subplots(
        layout,
        proj={1: projection},
        figwidth=13.0,
        figheight=8.4,
        hratios=(1.0, 1.0, 1.0, 0.88),
        wratios=(1.05, 1.0),
        hspace="0.30in",
        wspace="0.28in",
        bottom="0.80in",
        share=False,
    )
    ax_map, ax_magnitude, ax_depth = axes
    fig.patch.set_facecolor("#fbfcfc")

    ax_map.format(
        coast=True,
        land=True,
        ocean=True,
        landcolor="#f3f1eb",
        oceancolor="#dcecf2",
        coastcolor="#707d82",
        coastlinewidth=0.55,
        longrid=True,
        latgrid=True,
        gridcolor="#91a3a9",
        gridalpha=0.42,
        gridlinewidth=0.38,
        lonlocator=60,
        latlocator=30,
        labels=False,
        lefttitle=f"{count:,} events | {date_range}",
        righttitle="Circle area: magnitude | color: focal depth",
        title_kw={"fontsize": 9.2, "fontweight": "normal", "color": "#3b474b"},
    )

    cmap = ListedColormap(DEPTH_COLORS, name="earthquake_depth")
    norm = BoundaryNorm(DEPTH_EDGES, cmap.N, clip=True)
    plate_carree = ccrs.PlateCarree()
    plot_order = np.argsort(magnitude, kind="stable")

    points = ax_map.scatter(
        longitude[plot_order],
        latitude[plot_order],
        c=depth[plot_order],
        s=marker_area(magnitude[plot_order]),
        cmap=cmap,
        norm=norm,
        transform=plate_carree,
        alpha=0.82,
        edgecolors="#fbfcfc",
        linewidths=0.28,
        rasterized=True,
        zorder=3,
    )

    major = magnitude >= 7.0
    ax_map.scatter(
        longitude[major],
        latitude[major],
        s=marker_area(magnitude[major]) * 1.16,
        facecolors="none",
        edgecolors="#24272b",
        linewidths=0.9,
        transform=plate_carree,
        zorder=4,
    )

    depth_midpoints = (DEPTH_EDGES[:-1] + DEPTH_EDGES[1:]) / 2
    colorbar = ax_map.colorbar(
        points,
        loc="r",
        ticks=depth_midpoints,
        label="Focal depth (km)",
        length=0.68,
        width=0.15,
        ticklabelsize=7.8,
        labelsize=8.7,
    )
    colorbar.ax.set_yticklabels(DEPTH_LABELS)
    colorbar.outline.set_linewidth(0.6)

    magnitude_examples = [5.0, 6.0, 7.0, 8.0]
    magnitude_handles = [
        Line2D(
            [],
            [],
            linestyle="",
            marker="o",
            markersize=float(np.sqrt(marker_area(value))),
            markerfacecolor="#7c667e",
            markeredgecolor="#ffffff",
            markeredgewidth=0.6,
        )
        for value in magnitude_examples
    ]
    legend = ax_map.legend(
        magnitude_handles,
        [f"M{value:.0f}" for value in magnitude_examples],
        title="Magnitude",
        loc="lower left",
        bbox_to_anchor=(0.018, 0.025),
        ncols=4,
        frame=True,
        framealpha=0.94,
        facecolor="#ffffff",
        edgecolor="#8d989c",
        fontsize=7.8,
        title_fontsize=8.2,
        borderpad=0.55,
        handletextpad=0.35,
        columnspacing=0.75,
    )
    legend.get_frame().set_linewidth(0.55)

    for index in select_major_events(data):
        lon = float(longitude[index])
        lat = float(latitude[index])
        mag = float(magnitude[index])
        dx = -10 if lon > 105 or lon < -30 else 10
        dy = -16 if lat > 45 else (13 if lat >= 0 else -15)
        ax_map.annotate(
            f"M{mag:.1f}  {shorten_place(str(data['place'][index]))}",
            xy=(lon, lat),
            xycoords=plate_carree._as_mpl_transform(ax_map),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="right" if dx < 0 else "left",
            va="center",
            fontsize=7.2,
            color="#202326",
            bbox={
                "boxstyle": "round,pad=0.28,rounding_size=0.12",
                "facecolor": "#ffffff",
                "edgecolor": "#778489",
                "linewidth": 0.55,
                "alpha": 0.95,
            },
            arrowprops={
                "arrowstyle": "-",
                "color": "#59656a",
                "linewidth": 0.7,
                "shrinkA": 2,
                "shrinkB": 4,
            },
            annotation_clip=True,
            zorder=6,
        )

    magnitude_edges = np.array([5.0, 5.5, 6.0, 6.5, 7.0, np.inf])
    magnitude_labels = ["5.0-5.4", "5.5-5.9", "6.0-6.4", "6.5-6.9", "7.0+"]
    magnitude_counts = np.array(
        [
            np.count_nonzero((magnitude >= low) & (magnitude < high))
            for low, high in zip(magnitude_edges[:-1], magnitude_edges[1:])
        ]
    )
    magnitude_bar_colors = ["#a9b9bd", "#88a2a9", "#d7ab58", "#cf704e", "#9e3446"]
    y_positions = np.arange(len(magnitude_labels))
    ax_magnitude.barh(
        y_positions,
        np.maximum(magnitude_counts - 1, 0),
        left=1,
        width=0.62,
        color=magnitude_bar_colors,
        edgecolor="none",
        zorder=3,
    )
    ax_magnitude.set_xscale("log")
    ax_magnitude.set_xlim(1, max(3000, int(magnitude_counts.max() * 1.8)))
    ax_magnitude.set_yticks(y_positions, labels=magnitude_labels)
    ax_magnitude.set_ylim(len(magnitude_labels) - 0.35, -0.65)
    for y_value, value in zip(y_positions, magnitude_counts):
        is_largest = value > magnitude_counts.max() * 0.5
        ax_magnitude.text(
            value / 1.12 if is_largest else max(value * 1.10, 1.5),
            y_value,
            f"{value:,}  ({value / count:.1%})",
            va="center",
            ha="right" if is_largest else "left",
            fontsize=7.7,
            color="#263034" if is_largest else "#31383b",
        )
    ax_magnitude.format(
        title="Magnitude frequency",
        xlabel="Event count (log scale)",
        ylabel="Magnitude",
        xgrid=True,
        ygrid=False,
        gridcolor="#d2dadd",
        gridlinewidth=0.5,
        facecolor="#fbfcfc",
    )

    depth_counts, _ = np.histogram(depth, bins=DEPTH_EDGES)
    ax_depth.barh(
        y_positions,
        depth_counts,
        width=0.62,
        color=DEPTH_COLORS,
        edgecolor="none",
        zorder=3,
    )
    ax_depth.set_xlim(0, depth_counts.max() * 1.34)
    ax_depth.set_yticks(y_positions, labels=DEPTH_LABELS)
    ax_depth.set_ylim(len(DEPTH_LABELS) - 0.35, -0.65)
    for y_value, value in zip(y_positions, depth_counts):
        ax_depth.text(
            value + depth_counts.max() * 0.025,
            y_value,
            f"{value:,}  ({value / count:.1%})",
            va="center",
            ha="left",
            fontsize=7.7,
            color="#31383b",
        )
    ax_depth.format(
        title="Depth composition",
        xlabel="Event count",
        ylabel="Depth (km)",
        xgrid=True,
        ygrid=False,
        gridcolor="#d2dadd",
        gridlinewidth=0.5,
        facecolor="#fbfcfc",
    )

    for axis in (ax_magnitude, ax_depth):
        axis.set_axisbelow(True)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_visible(False)
        axis.tick_params(axis="y", length=0, pad=5)
        axis.tick_params(axis="x", colors="#566267")

    fig.format(
        suptitle=f"Global M5.0+ Earthquakes | {year_text}",
        suptitle_kw={
            "fontsize": 18.5,
            "fontweight": "bold",
            "color": "#172126",
        },
    )
    fig.text(
        0.055,
        0.018,
        "Source: USGS Earthquake Hazards Program GeoJSON catalog  |  "
        "Map: Robinson projection centered on 150E  |  "
        "Symbol area increases exponentially with magnitude; depth colors are classed.",
        ha="left",
        va="bottom",
        fontsize=7.5,
        color="#5b676c",
    )
    return fig


def main() -> None:
    args = parse_args()
    data = load_earthquakes(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig = draw_figure(data)

    pdf_path = args.output_dir / f"{args.basename}.pdf"
    png_path = args.output_dir / f"{args.basename}.png"
    fig.savefig(
        pdf_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        metadata={
            "Title": "Global M5.0+ Earthquakes in 2025",
            "Author": "UltraPlot",
            "Subject": "USGS earthquake magnitude, depth, and spatial distribution",
        },
    )
    fig.savefig(
        png_path,
        dpi=300,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    print(f"Loaded {len(data['magnitude']):,} earthquakes from {args.input}")
    print(
        f"Magnitude range: {data['magnitude'].min():.1f}-{data['magnitude'].max():.1f}; "
        f"depth range: {data['depth'].min():.1f}-{data['depth'].max():.1f} km"
    )
    print(f"Saved {pdf_path}")
    print(f"Saved {png_path}")


if __name__ == "__main__":
    main()
