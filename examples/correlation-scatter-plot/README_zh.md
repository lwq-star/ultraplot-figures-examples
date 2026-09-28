[English](README.md) | **简体中文**

# UltraPlot Skill A/B 测试：相关性散点图

## 实验来源与隔离

- 本次覆盖测试的四个绘图条件由使用 `fork_turns="none"` 启动的独立代理生成，
  未继承此前的对话轮次；这属于内容层面的隔离。
- 所有条件仍运行在同一主机并共享同一文件系统，未实施操作系统级访问隔离，
  也没有底层文件访问审计，因此本次测试并非操作系统级密封或完全盲法实验。
- skill 禁用组没有打开 skill 指令或 skill 支持文件；但系统提供的 skill 目录
  及其简短说明仍然可见，因此不能声称该组不可能知道 skill 的存在。
- skill 启用组使用 `ultraplot-figures` v1.3.0，且没有读取已有示例结果或此前的
  skill 测试结果。
- skill 启用组使用了正常运行的 UltraPlot MCP。MCP 的 `ultraplot.subplots` 源文件
  与所选 `spyder_env` 中的 UltraPlot 2.7.0 运行时一致，并通过任务相关查询检查了
  `PlotAxes.scatter` 和 `Figure.supxlabel`；skill 禁用组没有使用 UltraPlot MCP。
- 没有证据表明任一条件读取了已有测试结果或其他条件的产物；四个条件的结果
  全部冻结后才开始跨组比较。
- 集成到仓库时仅调整了输入路径、输出目录和仓库既有输出基名，随后使用同一
  工作簿原样重新运行两套相关性图设计。

上述控制支持“内容隔离”的比较，但不足以宣称实验完全密封或可证明为完全盲法。

## 输入数据

- 工作簿：[multiple_data.xlsx](data/multiple_data.xlsx)
- 工作表与规模：`Sheet1`，4,305 行 × 32 个数值列
- 结构：4 种地类 × 4 种模型 × `_0`/`_1` 配对字段
- 地类：`cropland`、`forest`、`grassland`、`savanna`
- 模型：`DNN`、`GBRT`、`LR`、`SVR`
- 四种地类的完整配对数依次为 3,499、3,965、4,221、4,305；16 个地类/模型
  组合合计 63,960 个有限值配对

## 提示词控制

以下内容记录本次覆盖测试的提示词。为避免写入本机专用信息，输入路径和 skill
路径以仓库链接表示；这种路径规范化没有改变可见提示词措辞或条件差异。

共同任务为：

> 绘图数据文件：`data/multiple_data.xlsx`
>
> 比较 cropland、forest、grassland 和 savanna 四种地类中，DNN、GBRT、LR、
> SVR 四种模型下 `_0` 与 `_1` 的关系。
>
> 请提供可直接运行的 Python 代码，导出 PDF 和 PNG。

只有绘图指令发生变化：

| 条件 | 绘图指令 |
|---|---|
| 启用 skill | `请用 [$ultraplot-figures](https://github.com/lwq-star/ultraplot-figures/blob/v1.3.0/SKILL.md) 制作一张适合论文使用的相关性散点图。` |
| 禁用 skill | `请用 UltraPlot 制作一张适合论文使用的相关性散点图。` |

图件使用 UltraPlot 2.7.0 和 Matplotlib 3.10.6 重新生成。

## 图件对比

### 启用 skill

![skill 启用组相关性图](with_skill/correlation_scatter.png)

### 禁用 skill

![skill 禁用组相关性图](without_skill/correlation_scatter_ultraplot.png)

## 输出文件

| 产物 | 启用 skill | 禁用 skill |
|---|---|---|
| 分析与绘图 | [correlation_scatter.py](with_skill/correlation_scatter.py) | [correlation_scatter_ultraplot.py](without_skill/correlation_scatter_ultraplot.py) |
| PDF | [correlation_scatter.pdf](with_skill/correlation_scatter.pdf) | [correlation_scatter_ultraplot.pdf](without_skill/correlation_scatter_ultraplot.pdf) |
| PNG | [correlation_scatter.png](with_skill/correlation_scatter.png) | [correlation_scatter_ultraplot.png](without_skill/correlation_scatter_ultraplot.png) |

## 客观输出信息

| 项目 | 启用 skill | 禁用 skill |
|---|---:|---:|
| PDF 页数 | 1 | 1 |
| PDF 页面尺寸 | 182.9996 × 179.8458 mm | 186.6900 × 191.7700 mm |
| PNG 像素尺寸 | 7,204 × 7,080 px | 4,410 × 4,530 px |
| PNG 分辨率元数据 | 999.998 dpi | 599.999 dpi |
