from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.is_dir():
    os.environ.setdefault("GDAL_DATA", str(gdal_data))

import cartopy.crs as ccrs
import numpy as np
import ultraplot as uplt


DEFAULT_INPUT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "usgs_earthquakes_2025_m5plus.geojson"
)
OUTPUT_BASENAME = "global_earthquakes_2025_m5plus"
EXPORT_DPI = 1000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot the global distribution of 2025 USGS M5+ earthquakes."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="USGS GeoJSON input (default: bundled 2025 M5+ catalog).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help=f"Directory for {OUTPUT_BASENAME}.pdf and .png.",
    )
    return parser.parse_args()


def load_events(path: Path) -> tuple[np.ndarray, ...]:
    if not path.is_file():
        raise FileNotFoundError(f"Input GeoJSON not found: {path}")

    with path.open(encoding="utf-8") as stream:
        collection = json.load(stream)

    if collection.get("type") != "FeatureCollection":
        raise ValueError("Input must be a GeoJSON FeatureCollection.")

    rows: list[tuple[float, float, float, float, int]] = []
    for index, feature in enumerate(collection.get("features", [])):
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        coordinates = geometry.get("coordinates") or []
        if geometry.get("type") != "Point" or len(coordinates) < 3:
            raise ValueError(f"Feature {index} is not a 3D Point geometry.")
        try:
            rows.append(
                (
                    float(coordinates[0]),
                    float(coordinates[1]),
                    float(coordinates[2]),
                    float(properties["mag"]),
                    int(properties["time"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Feature {index} lacks finite longitude, latitude, depth, "
                "magnitude, or time values."
            ) from exc

    if not rows:
        raise ValueError("Input contains no earthquake features.")

    values = np.asarray(rows, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Earthquake coordinates and attributes must be finite.")

    longitudes, latitudes, depths, magnitudes = values[:, :4].T
    times = values[:, 4].astype(np.int64)
    if np.any((longitudes < -180) | (longitudes > 180)):
        raise ValueError("Longitudes must be in EPSG:4326 degrees.")
    if np.any((latitudes < -90) | (latitudes > 90)):
        raise ValueError("Latitudes must be in EPSG:4326 degrees.")
    if np.any(depths < 0):
        raise ValueError("Depth values must be non-negative kilometers.")
    if np.any(magnitudes < 5):
        raise ValueError("This figure requires a catalog restricted to M >= 5.")

    years = {
        datetime.fromtimestamp(timestamp / 1000, UTC).year for timestamp in times
    }
    if years != {2025}:
        raise ValueError("This figure requires earthquake origin times from 2025.")

    return longitudes, latitudes, depths, magnitudes


def main() -> None:
    args = parse_args()
    longitudes, latitudes, depths, magnitudes = load_events(args.input)

    # Draw smaller events first so the less frequent large events remain visible.
    order = np.argsort(magnitudes, kind="stable")
    longitudes = longitudes[order]
    latitudes = latitudes[order]
    depths = depths[order]
    magnitudes = magnitudes[order]

    fig, ax = uplt.subplots(proj="pcarree", journal="nat2", tight=True)
    points = ax.scatter(
        longitudes,
        latitudes,
        c=depths,
        s=magnitudes,
        smin=9,
        smax=180,
        absolute_size=False,
        cmap="batlow",
        vmin=0,
        vmax=700,
        alpha=0.78,
        edgecolors="white",
        linewidths=0.25,
        transform=ccrs.PlateCarree(),
        zorder=3,
    )
    ax.format(
        extent="globe",
        coast=True,
        land=True,
        landcolor="#E8E8E8",
        ocean=True,
        grid=True,
        lonlabels="b",
        latlabels="l",
        lonlocator=60,
        latlocator=30,
    )
    ax.colorbar(
        points,
        loc="r",
        label="Depth (km)",
        ticks=np.arange(0, 701, 100),
    )
    ax.sizelegend(
        [5, 6, 7, 8],
        labels=["5", "6", "7", "8"],
        title="Magnitude",
        color="gray5",
        loc="b",
        ncols=4,
        frame=False,
    )
    ax.text(
        0.01,
        0.98,
        f"USGS catalog | 2025 | M >= 5 | n = {magnitudes.size:,}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize="small",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1.5},
        zorder=5,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig.save(args.output_dir / f"{OUTPUT_BASENAME}.pdf", dpi=EXPORT_DPI)
    fig.save(args.output_dir / f"{OUTPUT_BASENAME}.png", dpi=EXPORT_DPI)


if __name__ == "__main__":
    main()
