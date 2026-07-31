---
name: write-literature-notes
description: Read research papers or reviews and create source-grounded Chinese literature notes in the user's fixed Word table. Use when asked to 阅读、精读、总结或改写论文、综述、PDF、DOI、arXiv 或论文链接，并生成文献阅读笔记 DOCX，填写题目、作者、来源、真实论文结构、研究问题、研究方法、研究结果或综述发现、创新与不足和感悟心得。Always copy assets/reading-note-template.docx, fill only its existing cells, preserve the table format, and leave the remarks row blank.
---

# 写文献阅读笔记

根据论文证据生成中文阅读笔记。把 Skill 内置模板复制为新的输出文件，只在副本的既有表格槽位中填入内容；不要重建表格、修改表格格式或覆盖模板资产。

## 加载顺序

1. 始终阅读 `references/writing-style.md`，按文献类型选择论文或综述写法。
2. 生成 DOCX 时阅读 `references/template-spec.md` 和 `references/content-schema.md`，使用 `scripts/fill_reading_note.py`。
3. 写作尺度不明确时，再查看 `assets/teacher-reference.docx` 和 `assets/recent-style-reference.docx`。

## 工作流

1. 从论文首页、目录、引言、方法、实验、结果、结论和附录建立字段级证据记录；关键事实保留章节、表、图或页码位置。
2. 判定文献类型并按 `references/writing-style.md` 起草。实验论文按真实实验写结果；无原创实验的综述按统计、分类、比较、归纳和开放问题写发现，不虚构实验。
3. 将论文原有的罗马数字或其他章节编号统一重排为阿拉伯数字：一级结构使用 `1. 标题：总结`；算法小节在 Word 中显示为 `- 3.1 标题：总结`，并采用统一的悬挂缩进与一级结构区分；标题后必须使用中文冒号。
4. 核对元数据、实验数字、统计结论和局限来源。无法核验的内容留空或填写 —，不做推测。
5. 按 `references/content-schema.md` 准备 UTF-8 JSON，运行脚本生成 DOCX。备注不属于生成内容，保留模板第 13 行并留空。
6. 使用 `scripts/render_with_word.ps1` 导出 PDF，或使用文档渲染工具逐页检查；每次实质修改后重新生成并复核。默认只交付最终 DOCX。

## 生成命令

使用 Codex 工作区依赖返回的 Python：

```powershell
& $PYTHON_BIN "$SKILL_DIR\scripts\fill_reading_note.py" `
  --content "C:\absolute\note-content.json" `
  --out "C:\absolute\文献阅读笔记.docx"
```

脚本核对内置模板哈希，复制 `assets/reading-note-template.docx`，再写入允许的文本槽位。输出路径必须与模板路径不同。

## 交付门槛

- 论文结构与真实目录一致，问题、方法和实验均来自论文原文。
- 论文结构一级序号为连续的 `1. `、`2. `；小节显示为 `- 3.1`、`- 3.2`，左缩进 0.74 cm、首行悬挂 0.37 cm，换行与小节正文起始位置对齐；每条均为“标题：总结”，不保留论文原有罗马数字或字母编号。
- 数字、排名、维度、样本数和统计结论能够回到论文证据。
- 综述没有原创实验时，结果栏使用具体统计、分类、比较或归纳结果表述，不把被引研究的实验写成综述自身实验。
- 创新写清机制、实现和作用；不足有原文或实验现象支撑。
- 表格仍为原 13 行结构，尺寸、边距、列宽、合并关系、灰底和边框不变。
- 第 13 行备注内容保持空白，交由用户手工填写。
- 表格后只保留 1 pt 空段落，最终文件不得因表后空段落产生尾部空白页。
- 默认只交付一份 DOCX，不交付内部 JSON、PDF、PNG 或证据表。

## 资源

- `assets/reading-note-template.docx`：唯一模板；复制后原位填表。
- `assets/teacher-reference.docx`：控制基本深度与组织方式。
- `assets/recent-style-reference.docx`：控制实验细节与定量表达密度。
