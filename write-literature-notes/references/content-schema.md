# 内容 JSON 契约

`scripts/fill_reading_note.py` 接受 UTF-8 JSON 对象。字符串数组表示“一项一个段落”；点数由论文证据决定，不设固定数量。

## 首选结构

```json
{
  "title": "论文首页原始题目",
  "authors": ["Author A", "Author B"],
  "document_type": "期刊论文",
  "impact_factor": "—",
  "source": "Journal or Conference",
  "original_link": "https://doi.org/...",
  "keywords": ["关键词1", "关键词2"],
  "structure": [
    "1. Introduction：概括本节内容。",
    "2. Related Work：概括本节内容。",
    "3. Proposed Method：概括整体算法。",
    "3.1 Adaptive Search Mechanism：概括机制与作用。",
    "3.2 Perturbation Mechanism：概括机制与作用。"
  ],
  "research_question": [
    "依据论文原始问题或研究缺口提炼完整问题。"
  ],
  "methods": [
    "写区别于已有工作的核心机制、实现方式及其解决的问题。",
    "只在必要时补充与结果解释直接相关的实验设计。"
  ],
  "results": [
    "具体实验或分析名称结果表明，写明对象、结果和支持的结论。"
  ],
  "innovations": [
    "写清新机制或新对象、实现方式以及解决的问题。"
  ],
  "limitations": [
    "只写有作者声明、实验现象、开销或未覆盖场景支持的不足。"
  ],
  "reflection": "我认为最值得借鉴的是……，可迁移到……。"
}
```

必填字段：`title`、`authors`、`document_type`、`source`、`structure`、`research_question`、`methods`、`results`、`innovations`、`reflection`。`limitations`、`impact_factor`、`original_link` 和 `keywords` 可选。影响因子无法核验时使用 `—`，其他可选值无法核验时使用空字符串或空数组。

## 编号合同

- `research_question`、`methods` 和 `results`：数组长度为 1 时不编号；长度大于 1 时由脚本添加 `1. `、`2. `。
- `innovations`：长度为 1 时不编号；长度大于 1 时由脚本编号。
- `limitations`：独立计数；长度为 1 时不编号，长度大于 1 时从 `1. ` 重新编号。
- 所有数组都只写正文。不要在 JSON 中写 `1. `、`创新：`、`不足：` 或其他短标签。
- `limitations` 为空时，脚本把第 11 行标签设为“创新”；存在不足时自动设为“创新与不足”。不要手工提供标签。

## 论文结构合同

`structure` 的一级条目必须连续使用 `1. 标题：总结`、`2. 标题：总结`。真实小节在 JSON 中使用 `3.1 标题：总结`、`3.2 标题：总结`，不要手动添加连字符或空格缩进。脚本会把子级渲染为 `- 3.1 标题：总结`，并设置左缩进 0.74 cm、首行悬挂 0.37 cm。

标题取自真实目录；标题与总结之间只用中文冒号 `：`。不要复制论文原有的 `I.`、`II.`、`A.`、`B.` 编号。脚本会拒绝不连续编号、孤立小节、英文冒号和缺失总结。

## 文献类型合同

`document_type` 决定结果写法。实验型论文的 `results` 使用具体实验名称加“实验结果表明”；没有原创实验的综述使用具体统计、分类、比较、归纳或开放问题名称加“结果表明”，不得把被引研究的实验写成综述自身实验。

## 旧版兼容

旧 JSON 可继续使用 `innovation` 数组：

```json
"innovation": [
  "创新：",
  "创新正文一。",
  "创新正文二。",
  "不足：",
  "不足正文。"
]
```

脚本会按“创新：”和“不足：”拆分、移除旧手工编号，再应用新编号规则。不要同时提供 `innovation` 与 `innovations`/`limitations`。旧数据若写了“创新与不足”标签却没有“不足：”分隔，脚本会拒绝猜测，应先迁移为首选结构。

JSON 不提供 `notes` 字段。旧版 JSON 即使包含 `notes`，脚本也会忽略并把模板第 13 行备注留空。
