**English** | [Simplified Chinese](README_zh.md)

# UltraPlot Skill A/B Test: Global M5+ Earthquakes in 2025

## Input data

- GeoJSON: [usgs_earthquakes_2025_m5plus.geojson](data/usgs_earthquakes_2025_m5plus.geojson)
- Source features: 2,129
- Plotted valid Point features: 2,129 in each condition
- Feature types: 2,128 records have `properties.type == "earthquake"`; one has
  `properties.type == "landslide"`
- The frozen rerun retained that landslide record because both new tests plotted
  all valid Point features; it was not filtered during repository integration
- Magnitude range: M5.0-M8.8; depth range: 0-648.298 km

## Prompt control

The input path below is repository-relative so the prompt can be published
without machine-specific information. The full effective prompt for each
condition consists of its condition-specific instruction plus the common task.
The local skill link used during the rerun is represented here by the equivalent
v1.2.1 repository permalink; its visible prompt wording is unchanged.

The common task was:

> Plotting data file: `data/usgs_earthquakes_2025_m5plus.geojson`
>
> Show the spatial distribution, magnitude, and depth characteristics of global
> M5+ earthquakes in 2025, so readers can understand their global pattern and
> major characteristics directly.
>
> Provide directly runnable Python code and export PDF and PNG.

Only the plotting instruction changed:

| Condition | Plotting instruction |
|---|---|
| With skill | `Use [$ultraplot-figures](https://github.com/lwq-star/ultraplot-figures/blob/v1.2.1/SKILL.md) for plotting.` |
| Without skill | `Use UltraPlot for plotting.` |

The rerun used UltraPlot 2.6.0, Matplotlib 3.10.6, and Cartopy 0.25.0.
The skill-enabled condition used `ultraplot-figures` v1.2.1.

## Isolation and provenance

- The generation agents used `fork_turns="none"`, so they did not inherit prior
  conversation history. Prompts and generation outputs were isolated at the
  content and workflow level.
- The agents were instructed not to read existing test scripts or outputs, the
  other condition's files, or prior skill-example results. There is no evidence
  that cross-reading occurred. The skill-disabled condition did not open the
  skill instructions or supporting files, although the system skill catalog and
  its short description remained visible. The skill-enabled condition used
  v1.2.1 and did not use old skill example results.
- Both results were frozen before any central comparison. Repository integration
  subsequently changed only portable input paths and existing output basenames
  and locations, then reran the scripts.
- The agents shared a host and filesystem, without OS-level access isolation or
  a filesystem access audit. This is therefore a content-level isolation test,
  not an OS-hermetic or completely blind experiment.

## Figure comparison

### With `ultraplot-figures`

![Skill-enabled earthquake figure](with_skill/global_earthquakes_2025_m5plus.png)

### Without skill

![Skill-disabled earthquake figure](without_skill/global_earthquakes_2025_m5plus.png)

## Retained files

| Type | With skill | Without skill |
|---|---|---|
| Analysis and plotting | [plot_global_earthquakes.py](with_skill/plot_global_earthquakes.py) | [plot_global_earthquakes_2025.py](without_skill/plot_global_earthquakes_2025.py) |
| PDF | [global_earthquakes_2025_m5plus.pdf](with_skill/global_earthquakes_2025_m5plus.pdf) | [global_earthquakes_2025_m5plus.pdf](without_skill/global_earthquakes_2025_m5plus.pdf) |
| PNG | [global_earthquakes_2025_m5plus.png](with_skill/global_earthquakes_2025_m5plus.png) | [global_earthquakes_2025_m5plus.png](without_skill/global_earthquakes_2025_m5plus.png) |

## Objective output information

| Item | With skill | Without skill |
|---|---:|---:|
| Plotted valid Point features | 2,129 | 2,129 |
| PDF pages | 1 | 1 |
| PDF page size | 182.9996 x 121.6549 mm | 282.3731 x 224.6046 mm |
| PNG dimensions | 7,204 x 4,789 px | 3,335 x 2,652 px |
| PNG resolution metadata | 999.998 dpi | 299.999 dpi |
| Display projection | Plate Carree, central longitude 0 | Robinson, central longitude 180 |
