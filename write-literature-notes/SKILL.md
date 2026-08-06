---
name: write-literature-notes
description: "Read research papers, reviews, theses, PDFs, DOI/arXiv records, or publication links and create evidence-grounded Chinese literature notes in the bundled fixed Word table. Use when asked to 阅读、精读、总结或改写文献并交付 DOCX，或需要填写题目、作者、来源、真实论文结构、研究问题、方法、结果、创新、不足和感悟。Always copy the bundled template, fill only allowed cells, preserve its 13-row layout, and leave the remarks row blank."
---

# 写文献阅读笔记 SOP

把论文证据转换为一份固定模板的中文阅读笔记。只在模板副本的允许槽位写内容，不重建表格，不修改模板资产，不把通用 Word 格式规范套到该固定模板。

## 权威与边界

按以下优先级处理冲突：论文原文与补充材料 → `references/writing-style.md` → `references/template-spec.md` → 风格参考资产。通用 `word-writer` 的白底表格等规则与本模板冲突时，以本技能模板为准；不要对最终阅读笔记运行 `normalize_word.py`。

默认只交付一份最终 DOCX。内部证据记录、JSON、PDF 和页面图片只用于生成与核验，交付后移除，除非用户明确要求保留。

## SOP

### 0. 确认输入与运行条件

1. 确认论文全文或可访问的稳定来源、输出目录和文件名。只有摘要时，不得假装完成全文精读；改为“摘要级笔记”并在交付时明确范围。
2. 读取 `references/source-and-failures.md`，判断本地 PDF、网页、DOI、扫描件、付费墙或资料冲突的处理路径。
3. 运行环境预检：

```powershell
python -X utf8 scripts/check_environment.py
```

`status=ready` 才能直接生成并渲染；`degraded` 时按报告中的 fallback 继续；`blocked` 时先修复缺失的核心 Python 包。不要盲信某个固定 Python 路径，应使用能够导入 `python-docx` 的解释器。

### 1. 建立字段级证据

1. 阅读首页、目录、摘要、引言、方法、实验或分析、结果、结论和必要附录。
2. 为每个输出字段记录证据位置：章节、页码、表号、图号或出版页。数字、排名、维度、样本量、运行次数和统计结论必须能回到来源。
3. 区分事实、作者解释和自己的概括。无法核验的元数据用 `—` 或空值，不推测。

### 2. 按文献类型起草

1. 始终完整读取 `references/writing-style.md`。
2. 先判定实验论文、综述、系统综述/元分析或学位论文，再选对应写法。综述没有原创实验时，写统计、分类、比较、归纳与开放问题，不把被引研究写成本文实验。
3. 论文结构按真实目录重排为连续阿拉伯数字。一级写 `1. 标题：总结`；真实小节写 `3.1 标题：总结`，不要手动加连字符。
4. 研究问题、方法和结果：一个要点不编号；两个及以上要点由脚本自动添加 `1. `、`2. `。
5. 创新与不足分别形成数组：每组只有一个要点时不编号；同组两个及以上时由脚本独立编号。不足证据不足时省略 `limitations`，不得主观补写。

### 3. 准备并校验 JSON

1. 完整读取 `references/content-schema.md` 与 `references/template-spec.md`。
2. 使用首选字段 `innovations` 和可选字段 `limitations`；JSON 条目只写正文，不写“创新：”“不足：”或手工编号。
3. 只有在写作尺度仍不明确时，才查看 `assets/teacher-reference.docx` 和 `assets/recent-style-reference.docx`。参考稿只控制组织密度，不覆盖论文事实。

### 4. 生成 DOCX

```powershell
python -X utf8 scripts/fill_reading_note.py `
  --content "C:\absolute\note-content.json" `
  --out "C:\absolute\文献阅读笔记.docx"
```

脚本必须返回 JSON 且 `status` 为 `pass`。它会核对模板哈希、拒绝覆盖模板、复制模板、验证结构、自动处理分组编号、清空备注并审计最终文件。输出已存在时换用新路径；只有用户明确要求覆盖时使用 `--force`。

### 5. 渲染与逐页核验

优先使用可用的文档渲染工作流。也可运行：

```powershell
python -X utf8 scripts/render_docx.py `
  "C:\absolute\文献阅读笔记.docx" `
  --pdf "C:\temporary\文献阅读笔记.pdf"
```

逐页检查裁切、重叠、断表、异常空白、字体替换、编号和末尾空白页。每次内容或布局修改后重新生成、重新渲染、重新检查。没有可用渲染器时只能报告“结构审计通过、视觉验收未完成”，不得宣称最终交付通过。

### 6. 安全审查

在交付、发布或复制本 skill 前运行：

```powershell
python -X utf8 scripts/audit_skill_security.py
```

必须得到 `status=pass`，且 `findings`、`warnings` 均为空。扫描器会检查文本以及 DOCX 内部 XML，但不会回显命中的秘密值。对任务专用工作/输出目录再使用 `--root` 扫描，防止把 API 密钥、访问令牌、账号密码、真实用户路径、`.env`、OCR 临时文本或含凭据 JSON 一并交付。发现真实凭据时先移除；若它可能已经被提交或分享，提醒用户立即轮换/吊销，然后重跑扫描。不得把“加入允许列表”当作默认修复。

### 7. 交付

确认最终 DOCX 对应最新一次 `status=pass` 和逐页检查结果；核对第 13 行备注为空。只交付最终 DOCX，并说明论文来源范围、未能核验的字段和任何视觉 QA 限制。

## 停止条件

- 全文不可获取且用户要求全文级结论：停止并请求全文；可另行提供明确标注的摘要级版本。
- 扫描件 OCR 质量不足以核对公式、表格或数字：停止相关字段，不能凭模糊识别补写。
- 模板哈希或 13 行结构不匹配：停止生成，确认模板版本，禁止绕过校验重建相似表格。
- 新旧 JSON 同时提供 `innovation` 与 `innovations`/`limitations`：视为歧义并修正输入，不猜测优先级。
- 论文证据只支持创新、不支持不足：使用“创新”行标签并省略不足，不把缺项视为失败。
- 安全扫描发现凭据、私有路径、可疑凭据文件或未检查二进制：停止交付；移除意外材料或完成人工来源审查后重跑。

## 完成合同

只有同时满足以下条件才报告完成：论文结构与真实目录一致；关键结论可追溯；实验/综述写法正确；创新与不足的单项/多项编号正确；输出仍为 1 节、1 张 13 行表；备注为空；生成审计通过；每页已经视觉检查；最终 skill 与任务目录的安全扫描通过；最终交付不含内部临时文件。

## 资源

- `references/source-and-failures.md`：来源获取、降级和异常处理。
- `references/writing-style.md`：各字段的证据与写作合同。
- `references/content-schema.md`：JSON 契约和兼容规则。
- `references/template-spec.md`：模板布局与保真门槛。
- `assets/reading-note-template.docx`：唯一生成模板。
- `scripts/check_environment.py`：新电脑预检。
- `scripts/fill_reading_note.py`：确定性填表与审计。
- `scripts/render_docx.py`：LibreOffice/Word PDF 渲染入口。
- `scripts/audit_skill_security.py`：不回显秘密值的凭据、私有路径与 OOXML 内容扫描。
