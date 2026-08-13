# 04 · GPT Image 2 → Editable PowerPoint

## 适用范围

该分支适合图形摘要、系统概念图和非数值型科研示意图。数据曲线、混淆矩阵、坐标轴、公式和关键拓扑必须由真实数据或可控矢量对象生成，不能由图像模型决定。

## 工作流

```text
Figure Specification
  → GPT Image 2 concept draft
  → structure and copyright review
  → PowerPoint layer reconstruction
  → render to PNG
  → pixel/structure comparison
  → single-variable iteration
```

## 交付契约

一次完整案例应包含：

- `figure_spec.md`：图件主张、来源、尺寸和不可改变项；
- `prompt.txt`：最终生成提示词和模型记录；
- `reference.png`：AI概念草案；
- `reconstruction.pptx`：文本、形状、连接线和图标均可编辑；
- `render.png`：PPT渲染结果；
- `diff.png`、`overlay.png`、`compare.json`：差异产物；
- `assumptions.md`：人工判断、字体替换和版权说明。

## 验收顺序

1. 科学关系、模块连接和阅读顺序正确；
2. 文本、公式、图例和关键对象可编辑；
3. 无裁切、遮挡、字体替换或低分辨率问题；
4. 再使用 `compare_figure_renders.py` 量化渲染差异。

“像素级对比”是迭代手段，不代表允许逐像素复制无授权论文图，也不能优先于科学正确性。
