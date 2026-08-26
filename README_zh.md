[English](README.md) | **简体中文**

# UltraPlot Figures 示例

本仓库集中保存 Codex skill
[`ultraplot-figures`](https://github.com/lwq-star/ultraplot-figures) 的完整可复现
示例。自 skill v1.1.0 起，示例与 skill 分开维护，因此安装 skill 时不会下载示例
数据或渲染结果。

## 示例

- [2025 年全球 M5+ 地震 skill 对照案例](examples/earthquake/README_zh.md)
- [预测值与真实值模型对照案例](examples/correlation-scatter-plot/README_zh.md)

每个对照案例均保留输入数据、可编辑脚本，以及启用和禁用 skill 两种条件下的最终
PDF 和 PNG。当前案例使用
[`ultraplot-figures` v1.2.1](https://github.com/lwq-star/ultraplot-figures/blob/v1.2.1/SKILL.md)
重新测试。

## 复现环境

这些示例最近使用 Python 3.13.7、UltraPlot 2.6.0、Matplotlib 3.10.6 和
NumPy 2.4.5 核验。地震案例还需要 Cartopy 0.25.0；相关性案例还需要
pandas 2.3.3 和 openpyxl 3.1.5。各脚本均相对于自身案例目录解析输入和输出路径。
本次对照测试在 Windows 电脑上使用 GPT-5.6 Sol 模型和 `ultra` 推理强度完成。

## 数据与许可证

本仓库的 [LICENSE](LICENSE) 适用于原创代码和文档，第三方数据仍遵循其来源条款。
地震 GeoJSON 的 metadata 中记录了 USGS 查询 URL。
