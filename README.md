**English** | [Simplified Chinese](README_zh.md)

# UltraPlot Figures Examples

This repository contains the complete, reproducible examples for the
[`ultraplot-figures`](https://github.com/lwq-star/ultraplot-figures) Codex
skill. Starting with skill v1.1.0, the examples are maintained separately so
installing the skill does not download example data or rendered outputs.

## Examples

- [2025 global M5+ earthquake skill comparison](examples/earthquake/README.md)
- [Observed-versus-predicted model comparison](examples/correlation-scatter-plot/README.md)

Each comparison retains the input data, editable scripts, and final PDF and PNG
outputs for both the skill-enabled and skill-disabled conditions. The current
comparisons were retested with
[`ultraplot-figures` v1.3.0](https://github.com/lwq-star/ultraplot-figures/blob/v1.3.0/SKILL.md).

## Reproduction environment

The examples were last verified with Python 3.13.7, UltraPlot 2.7.0,
Matplotlib 3.10.6, and NumPy 2.4.5. The earthquake example also requires
Cartopy 0.25.0. The correlation example also requires pandas 2.3.3 and
openpyxl 3.1.5. Each script resolves its input and output paths relative to its
own example directory. The comparison runs were generated on Windows by
mutually independent Codex agents, each starting from a blank context.

## Data and license

The repository [license](LICENSE) applies to the original code and
documentation. Third-party data remains subject to its source terms. The
earthquake GeoJSON records its USGS query URL in its metadata.
