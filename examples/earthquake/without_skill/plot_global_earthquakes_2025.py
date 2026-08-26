"""Plot the spatial, magnitude, and depth patterns of 2025 M5+ earthquakes."""

from __future__ import annotations

import json
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker
from matplotlib.colorbar import Colorbar
import numpy as np
import ultraplot as uplt


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "usgs_earthquakes_2025_m5plus.geojson"
)
OUTPUT_DIR = Path(__file__).resolve().parent
PNG_PATH = OUTPUT_DIR / "global_earthquakes_2025_m5plus.png"
PDF_PATH = OUTPUT_DIR / "global_earthquakes_2025_m5plus.pdf"


def load_earthquakes(path: Path) -> tuple[np.ndarray, ...]:
    """Return longitude, latitude, depth, magnitude, and time arrays."""
    with path.open("r", encoding="utf-8") as stream:
        collection = json.load(stream)

    features = collection.get("features", [])
    if not features:
        raise ValueError(f"No earthquake features found in {path}")

    records: list[tuple[float, float, float, float, int]] = []
    for feature in features:
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        coordinates = geometry.get("coordinates") or []
        if geometry.get("type") != "Point" or len(coordinates) < 3:
            continue
        values = (coordinates[0], coordinates[1], coordinates[2], properties.get("mag"))
        if any(value is None for value in values):
            continue
        records.append((*map(float, values), int(properties.get("time", 0))))

    data = np.asarray(records, dtype=float)
    if data.size == 0:
        raise ValueError("No valid point records with magnitude and depth were found")

    longitude, latitude, depth, magnitude, time_ms = data.T
    valid = (
        np.isfinite(data).all(axis=1)
        & (longitude >= -180)
        & (longitude <= 180)
        & (latitude >= -90)
        & (latitude <= 90)
        & (depth >= 0)
        & (magnitude >= 5)
    )
    if not valid.all():
        longitude, latitude, depth, magnitude, time_ms = (
            array[valid] for array in (longitude, latitude, depth, magnitude, time_ms)
        )
    return longitude, latitude, depth, magnitude, time_ms


def marker_area(magnitude: np.ndarray | float) -> np.ndarray | float:
    """Map magnitude to marker area while keeping rare large events legible."""
    return 7.0 + 13.0 * (np.asarray(magnitude) - 5.0) ** 2


def style_cartesian_axis(axis) -> None:
    axis.set_facecolor("#fbfcfc")
    axis.grid(axis="y", color="#d8dee1", linewidth=0.55, alpha=0.8, zorder=0)
    axis.tick_params(axis="both", which="major", labelsize=8, length=3, width=0.7)
    axis.tick_params(axis="both", which="minor", length=2, width=0.5)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#68747a")
    axis.spines["bottom"].set_color("#68747a")


def main() -> None:
    longitude, latitude, depth, magnitude, _ = load_earthquakes(DATA_PATH)
    event_count = magnitude.size

    uplt.rc.update(
        {
            "font.family": "DejaVu Sans",
            "axes.labelcolor": "#26343a",
            "axes.titlecolor": "#17262c",
            "text.color": "#26343a",
            "xtick.color": "#536269",
            "ytick.color": "#536269",
            "figure.facecolor": "#f7f9f9",
            "savefig.facecolor": "#f7f9f9",
        }
    )

    figure, axes = uplt.subplots(
        [[1, 1], [2, 3]],
        proj={1: ccrs.Robinson(central_longitude=180)},
        figsize=(12.0, 8.7),
        hratios=(1.92, 1.0),
        wspace=0.34,
        hspace=0.78,
        share=False,
    )
    map_axis, magnitude_axis, depth_axis = axes

    # Geographic context uses a Pacific-centered view so the Ring of Fire is continuous.
    map_axis.set_global()
    map_axis.add_feature(
        cfeature.OCEAN.with_scale("110m"), facecolor="#dce9ed", edgecolor="none", zorder=0
    )
    map_axis.add_feature(
        cfeature.LAND.with_scale("110m"), facecolor="#edf0eb", edgecolor="none", zorder=1
    )
    map_axis.coastlines(resolution="110m", color="#718087", linewidth=0.45, zorder=2)
    map_axis.spines["geo"].set_color("#4e5f66")
    map_axis.spines["geo"].set_linewidth(0.7)
    gridlines = map_axis.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=False,
        linewidth=0.38,
        color="#78909a",
        alpha=0.48,
        linestyle=(0, (2, 3)),
        zorder=2,
    )
    gridlines.xlocator = mticker.FixedLocator(np.arange(-180, 181, 60))
    gridlines.ylocator = mticker.FixedLocator(np.arange(-60, 61, 30))

    color_limit = max(650.0, float(np.ceil(depth.max() / 50.0) * 50.0))
    depth_norm = mcolors.PowerNorm(gamma=0.5, vmin=0, vmax=color_limit)
    depth_cmap = uplt.Colormap("cividis")
    draw_order = np.lexsort((depth, magnitude))
    points = map_axis.scatter(
        longitude[draw_order],
        latitude[draw_order],
        c=depth[draw_order],
        s=marker_area(magnitude[draw_order]),
        cmap=depth_cmap,
        norm=depth_norm,
        alpha=0.78,
        edgecolors="#ffffff",
        linewidths=0.25,
        transform=ccrs.PlateCarree(),
        rasterized=True,
        zorder=3,
    )

    major = magnitude >= 7.0
    map_axis.scatter(
        longitude[major],
        latitude[major],
        s=marker_area(magnitude[major]) + 12,
        facecolors="none",
        edgecolors="#a82127",
        linewidths=0.9,
        transform=ccrs.PlateCarree(),
        zorder=4,
    )

    largest = int(np.argmax(magnitude))
    map_axis.annotate(
        f"Largest: M {magnitude[largest]:.1f}\n29 Jul, Kamchatka",
        xy=(longitude[largest], latitude[largest]),
        xycoords=ccrs.PlateCarree()._as_mpl_transform(map_axis),
        xytext=(18, -36),
        textcoords="offset points",
        fontsize=7.5,
        fontweight="bold",
        ha="left",
        va="top",
        color="#7f161c",
        bbox={
            "boxstyle": "round,pad=0.28",
            "facecolor": "#fffdf9",
            "edgecolor": "#c79591",
            "linewidth": 0.6,
            "alpha": 0.96,
        },
        arrowprops={"arrowstyle": "-", "color": "#8b2a2e", "linewidth": 0.75},
        zorder=6,
    )

    size_values = (5.0, 6.0, 7.0, 8.0)
    size_handles = [
        map_axis.scatter(
            [],
            [],
            s=marker_area(value),
            facecolor="#66777e",
            edgecolor="#ffffff",
            linewidth=0.4,
        )
        for value in size_values
    ]
    size_legend = map_axis.legend(
        size_handles,
        [f"M {value:.0f}" for value in size_values],
        title="Magnitude (marker area)",
        loc="lower left",
        bbox_to_anchor=(0.018, 0.018),
        ncol=4,
        frameon=True,
        fancybox=False,
        facecolor="#fffdf9",
        edgecolor="#a9b3b7",
        framealpha=0.96,
        fontsize=7.2,
        title_fontsize=7.5,
        handletextpad=0.35,
        columnspacing=0.9,
        borderpad=0.55,
    )
    size_legend.set_zorder(7)

    colorbar_axis = figure.add_axes([0.690, 0.389, 0.200, 0.013], label="depth_colorbar")
    colorbar = Colorbar(
        colorbar_axis,
        points,
        orientation="horizontal",
        ticks=[0, 70, 300, 600],
    )
    colorbar.ax.tick_params(labelsize=6.8, length=2, pad=1)
    colorbar.ax.minorticks_off()
    colorbar.ax.tick_params(which="minor", bottom=False, top=False)
    colorbar.ax.set_title("Depth (km; square-root color scale)", fontsize=7.2, pad=4)
    colorbar.outline.set_linewidth(0.5)
    colorbar.outline.set_edgecolor("#65737a")

    map_axis.text(
        0.015,
        0.92,
        "A",
        transform=map_axis.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        fontweight="bold",
        bbox={"facecolor": "#f7f9f9", "edgecolor": "none", "pad": 2.2, "alpha": 0.9},
        zorder=8,
    )
    map_axis.set_title(
        f"{event_count:,} USGS events | Pacific-centered Robinson projection | "
        "marker area encodes magnitude; color encodes depth",
        loc="left",
        fontsize=9.5,
        color="#53656c",
        pad=7,
    )

    # Magnitude distribution. A log count axis keeps the rare M7+ tail visible.
    magnitude_bins = np.arange(4.95, 9.16, 0.2)
    magnitude_axis.hist(
        magnitude,
        bins=magnitude_bins,
        color="#c64f42",
        edgecolor="#fffdf9",
        linewidth=0.45,
        zorder=2,
    )
    magnitude_axis.axvline(6.0, color="#8a2d29", linewidth=0.8, linestyle="--", zorder=3)
    magnitude_axis.axvline(7.0, color="#8a2d29", linewidth=0.8, linestyle="--", zorder=3)
    magnitude_axis.set_yscale("log")
    magnitude_axis.set_xlim(4.9, 9.05)
    magnitude_axis.set_ylim(0.8, 800)
    magnitude_axis.set_xticks([5, 6, 7, 8, 9])
    magnitude_axis.set_xlabel("Reported magnitude", fontsize=9)
    magnitude_axis.set_ylabel("Number of events (log scale)", fontsize=9)
    magnitude_axis.text(
        0.0,
        0.985,
        "B  Magnitude distribution",
        transform=magnitude_axis.transAxes,
        ha="left",
        va="top",
        fontsize=10.5,
        fontweight="bold",
        bbox={"facecolor": "#fbfcfc", "edgecolor": "none", "pad": 1.8, "alpha": 0.94},
        zorder=6,
    )
    magnitude_axis.text(
        0.97,
        0.95,
        f"M >= 6: {(magnitude >= 6).sum():,} ({(magnitude >= 6).mean():.1%})\n"
        f"M >= 7: {(magnitude >= 7).sum():,} ({(magnitude >= 7).mean():.1%})",
        transform=magnitude_axis.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        linespacing=1.35,
        bbox={"facecolor": "#fffdf9", "edgecolor": "#d8c1bd", "pad": 3, "alpha": 0.95},
        zorder=5,
    )
    style_cartesian_axis(magnitude_axis)

    # Depth distribution with conventional shallow/intermediate/deep boundaries.
    depth_bins = np.arange(0, 676, 25)
    depth_counts, depth_edges = np.histogram(depth, bins=depth_bins)
    depth_centers = (depth_edges[:-1] + depth_edges[1:]) / 2
    depth_axis.bar(
        depth_centers,
        depth_counts,
        width=np.diff(depth_edges) * 0.92,
        color=depth_cmap(depth_norm(depth_centers)),
        edgecolor="#f7f9f9",
        linewidth=0.35,
        zorder=2,
    )
    for boundary in (70, 300):
        depth_axis.axvline(boundary, color="#48565c", linewidth=0.75, linestyle="--", zorder=3)
    depth_axis.set_yscale("log")
    depth_axis.set_xlim(0, 675)
    depth_axis.set_ylim(0.8, 1500)
    depth_axis.set_xticks([0, 70, 150, 300, 450, 600])
    depth_axis.set_xlabel("Hypocentral depth (km)", fontsize=9)
    depth_axis.set_ylabel("Number of events (log scale)", fontsize=9)
    depth_axis.text(
        0.0,
        0.985,
        "C  Depth distribution",
        transform=depth_axis.transAxes,
        ha="left",
        va="top",
        fontsize=10.5,
        fontweight="bold",
        bbox={"facecolor": "#fbfcfc", "edgecolor": "none", "pad": 1.8, "alpha": 0.94},
        zorder=6,
    )

    zones = (
        (35, depth < 70, "<70 km"),
        (185, (depth >= 70) & (depth < 300), "70-300 km"),
        (480, depth >= 300, ">=300 km"),
    )
    for x_position, mask, label in zones:
        depth_axis.text(
            x_position,
            0.82,
            f"{label}\n{mask.sum():,} ({mask.mean():.1%})",
            transform=depth_axis.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=7.6,
            fontweight="bold",
            linespacing=1.25,
            bbox={"facecolor": "#fffdf9", "edgecolor": "#ccd4d6", "pad": 2.2, "alpha": 0.93},
            zorder=5,
        )
    style_cartesian_axis(depth_axis)

    figure.suptitle(
        "2025 Global Earthquakes of Magnitude 5.0+",
        x=0.075,
        y=0.985,
        ha="left",
        va="top",
        fontsize=18,
        fontweight="bold",
        color="#14272e",
    )
    figure.text(
        0.075,
        0.004,
        "Source: USGS Earthquake Catalog, 1 Jan-31 Dec 2025 UTC. "
        "Red outlines identify M7.0+ events. Histogram counts use logarithmic y-axes.",
        ha="left",
        va="bottom",
        fontsize=7.4,
        color="#5a696f",
    )

    figure.savefig(PNG_PATH, dpi=300, bbox_inches="tight", pad_inches=0.12)
    figure.savefig(PDF_PATH, dpi=300, bbox_inches="tight", pad_inches=0.12)
    print(f"Saved {PNG_PATH}")
    print(f"Saved {PDF_PATH}")
    print(
        f"Plotted {event_count} events; magnitude {magnitude.min():.1f}-{magnitude.max():.1f}; "
        f"depth {depth.min():.1f}-{depth.max():.1f} km"
    )


if __name__ == "__main__":
    main()
