# 内容 JSON

`scripts/fill_reading_note.py` 接受 UTF-8 JSON。所有字段值可为字符串或字符串数组；数组按一个条目一个段落写入。数组长度由论文实际内容决定，不要求固定点数。`research_question`、`methods` 和 `results` 含两个及以上条目时，脚本自动添加 `1. `、`2. ` 编号；JSON 条目只写完整正文，编号是唯一层级标记。`structure` 必须由写作者先完成章节层级判断并按下述格式编号，脚本会拒绝罗马数字、字母编号、缺失中文冒号或不连续的编号。

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
    "1. Introduction：用 1 句话概括本节内容。",
    "2. Related Work：用 1 句话概括本节内容。",
    "3. Proposed Method：概括整体算法。",
    "3.1 Adaptive Search Mechanism：用 1 句话概括机制与作用。",
    "3.2 Perturbation Mechanism：用 1 句话概括机制与作用。"
  ],
  "research_question": [
    "依据论文原始问题或研究缺口提炼；点数随原文决定。"
  ],
  "methods": [
    "写区别于已有工作的核心机制、实现方式及其解决的问题。",
    "必要时补充与结果解释直接相关的实验设计。"
  ],
  "results": [
    "CEC 2017 30 维测试函数实验结果表明，……",
    "去除自适应步长机制的消融实验结果表明，……",
    "MK01–MK10 柔性作业车间调度实例实验结果表明，……"
  ],
  "innovation_label": "创新与不足",
  "innovation": [
    "创新：",
    "写新机制、实现方式和解决的问题。",
    "不足：",
    "仅写有原文、消融或退化结果支持的内容。"
  ],
  "reflection": "我认为最值得借鉴的是……，可迁移到……。"
}
```

必填字段：`title`、`authors`、`document_type`、`source`、`structure`、`research_question`、`methods`、`results`、`innovation`、`reflection`。影响因子或链接无法核验时分别使用 — 或空字符串，不得猜测。

`document_type` 决定结果写法。实验型论文的 `results` 使用具体实验名称加 `实验结果表明`；没有原创实验的综述使用具体统计、分类、比较、归纳或开放问题名称加 `结果表明`，不得把被引研究的实验写成综述自身实验。

`structure` 的一级条目必须连续使用 `1. 标题：总结`、`2. 标题：总结`；算法或方法小节在 JSON 中仍使用 `3.1 标题：总结`、`3.2 标题：总结`，不要手动添加连字符或空格缩进。生成脚本会把子级统一渲染为 `- 3.1 标题：总结`，并设置左缩进 0.74 cm、首行悬挂 0.37 cm。标题取自论文真实标题，标题与总结之间只用中文冒号 `：`。不要把论文中的 `I.`、`II.`、`A.`、`B.` 直接复制到 JSON。

JSON 不提供 `notes` 字段。模板第 13 行备注内容由用户手工填写；即使旧版 JSON 仍包含 `notes`，生成脚本也会忽略并留空。

`results` 中的三条仅演示如何把实验名称写具体，不是固定实验类别。正式内容必须依据论文真实实验标题、对象和顺序增减条目；论文没有对应实验时不得沿用示例。

综述结果示例：

```json
"results": [
  "文献规模统计结果表明，……",
  "算法分类结果表明，……",
  "应用与开放问题综合结果表明，……"
]
```
