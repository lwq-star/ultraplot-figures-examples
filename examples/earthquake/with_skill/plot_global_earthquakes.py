from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.is_dir():
    os.environ.setdefault("GDAL_DATA", str(gdal_data))

import cartopy.crs as ccrs
import matplotlib as mpl
import numpy as np
import ultraplot as uplt
from matplotlib import font_manager
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D


DEFAULT_INPUT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "usgs_earthquakes_2025_m5plus.geojson"
)
OUTPUT_BASENAME = "global_earthquakes_2025_m5plus"
EXPORT_DPI = 1000
DEPTH_EDGES = np.array([0.0, 70.0, 300.0, 700.0])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot the global distribution of 2025 M5+ earthquakes."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parent
    )
    return parser.parse_args()


def load_events(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if not path.is_file():
        raise FileNotFoundError(f"Input GeoJSON not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection" or not payload.get("features"):
        raise ValueError("Input must be a non-empty GeoJSON FeatureCollection.")
    if payload.get("crs") is not None:
        raise ValueError("This script expects RFC 7946 WGS 84 longitude/latitude.")

    records: list[tuple[float, float, float, float, int]] = []
    for index, feature in enumerate(payload["features"], start=1):
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        coordinates = geometry.get("coordinates") or []
        if geometry.get("type") != "Point" or len(coordinates) < 3:
            raise ValueError(f"Feature {index} is not a 3D Point.")
        try:
            records.append(
                (
                    float(coordinates[0]),
                    float(coordinates[1]),
                    float(coordinates[2]),
                    float(properties["mag"]),
                    int(properties["time"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Feature {index} has invalid coordinates or fields.") from exc

    values = np.asarray(records, dtype=float)
    longitude, latitude, depth_km, magnitude, time_ms = values.T
    if not np.isfinite(values).all():
        raise ValueError("All plotted coordinates, depths, magnitudes, and times must be finite.")
    if not ((-180 <= longitude).all() and (longitude <= 180).all()):
        raise ValueError("Longitude must be in [-180, 180] degrees.")
    if not ((-90 <= latitude).all() and (latitude <= 90).all()):
        raise ValueError("Latitude must be in [-90, 90] degrees.")
    if not ((0 <= depth_km).all() and (depth_km < DEPTH_EDGES[-1]).all()):
        raise ValueError("Depth must be in [0, 700) km for the displayed classes.")
    if not (magnitude >= 5).all():
        raise ValueError("The requested dataset must contain only M5+ events.")

    years = {
        datetime.fromtimestamp(timestamp / 1000, timezone.utc).year
        for timestamp in time_ms
    }
    if years != {2025}:
        raise ValueError(f"Expected only 2025 UTC timestamps, found years: {sorted(years)}")

    return longitude, latitude, depth_km, magnitude


def chinese_font_families() -> list[str]:
    font_path = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "msyh.ttc"
    if not font_path.is_file():
        raise FileNotFoundError("Microsoft YaHei font was not found.")
    font_manager.fontManager.addfont(font_path)
    families = list(mpl.rcParams["font.family"])
    if "Microsoft YaHei" not in families:
        families.append("Microsoft YaHei")
    return families


def marker_area(magnitude: np.ndarray | float) -> np.ndarray | float:
    return 6.0 + 8.0 * (np.asarray(magnitude) - 5.0) ** 2


def main() -> None:
    args = parse_args()
    longitude, latitude, depth_km, magnitude = load_events(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    depth_colors = mpl.colormaps["viridis"]([0.12, 0.52, 0.90])
    depth_cmap = ListedColormap(depth_colors, name="earthquake_depth")
    depth_norm = BoundaryNorm(DEPTH_EDGES, depth_cmap.N, clip=True)
    draw_order = np.argsort(magnitude)

    with uplt.rc.context({"font.family": chinese_font_families()}):
        fig, axs = uplt.subplots(
            [[1, 1], [2, 3]],
            proj={1: "pcarree"},
            journal="nat2",
            refnum=1,
            hratios=(2.35, 1.0),
            share=False,
            span=False,
            tight=True,
        )
        ax_map, ax_magnitude, ax_depth = axs

        points = ax_map.scatter(
            longitude[draw_order],
            latitude[draw_order],
            c=depth_km[draw_order],
            s=marker_area(magnitude[draw_order]),
            cmap=depth_cmap,
            norm=depth_norm,
            alpha=0.82,
            edgecolors="white",
            linewidths=0.15,
            transform=ccrs.PlateCarree(),
            zorder=3,
        )
        colorbar = ax_map.colorbar(
            points,
            loc="r",
            label="震源深度 (km)",
            ticks=DEPTH_EDGES,
        )
        colorbar.ax.set_yticklabels(["0", "70", "300", "700"])

        legend_magnitudes = (5, 6, 7, 8)
        legend_handles = [
            Line2D(
                [],
                [],
                linestyle="none",
                marker="o",
                markersize=float(np.sqrt(marker_area(value))),
                markerfacecolor="0.55",
                markeredgecolor="white",
                markeredgewidth=0.4,
                label=f"M {value}",
            )
            for value in legend_magnitudes
        ]
        ax_map.legend(handles=legend_handles, loc="ll", ncols=4, title="震级")
        ax_map.text(
            0.99,
            0.98,
            f"n = {magnitude.size:,}",
            transform=ax_map.transAxes,
            ha="right",
            va="top",
        )

        magnitude_bins = np.arange(5.0, 9.01, 0.2)
        ax_magnitude.hist(magnitude, bins=magnitude_bins)
        median_magnitude = float(np.median(magnitude))
        ax_magnitude.axvline(median_magnitude, color="0.25", linestyle="--", linewidth=1)
        ax_magnitude.text(
            0.97,
            0.91,
            f"中位数 {median_magnitude:.1f}",
            transform=ax_magnitude.transAxes,
            ha="right",
            va="top",
        )

        depth_bins = np.arange(0, 701, 25)
        ax_depth.hist(depth_km, bins=depth_bins)
        ax_depth.axvline(70, color="0.25", linestyle="--", linewidth=1)
        ax_depth.axvline(300, color="0.25", linestyle="--", linewidth=1)
        shallow = np.mean(depth_km < 70) * 100
        intermediate = np.mean((depth_km >= 70) & (depth_km < 300)) * 100
        deep = np.mean(depth_km >= 300) * 100
        ax_depth.text(
            0.97,
            0.91,
            f"浅源 {shallow:.1f}%  中源 {intermediate:.1f}%  深源 {deep:.1f}%",
            transform=ax_depth.transAxes,
            ha="right",
            va="top",
        )

        axs.format(abc="a.", abcloc="ul")
        ax_map.format(
            lonlim=(-180, 180),
            latlim=(-90, 90),
            lonlocator=60,
            latlocator=30,
            lonlabels="b",
            latlabels="l",
            coast=True,
            grid=True,
        )
        ax_magnitude.format(
            xlabel="震级",
            ylabel="地震数",
            xlim=(5, 9),
            ylim=(0, 1200),
            xlocator=1,
            grid=False,
        )
        ax_depth.format(
            xlabel="震源深度 (km)",
            ylabel="地震数（对数刻度）",
            xlim=(0, 700),
            ylim=(0.7, 3000),
            xlocator=100,
            yscale="log",
            grid=False,
        )

        for suffix in ("pdf", "png"):
            fig.save(
                args.output_dir / f"{OUTPUT_BASENAME}.{suffix}",
                dpi=EXPORT_DPI,
            )


if __name__ == "__main__":
    main()
