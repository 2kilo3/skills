# Agent Skills

中文 | [English](README.en.md)

这个仓库保存四个可独立使用的 Agent Skill。每个 Skill 都以 `SKILL.md` 为入口，按需附带脚本、参考材料、界面元数据或文档模板。

## 包含的 Skill

| Skill | 用途 | 主要输出 |
| --- | --- | --- |
| [`humanier-jf`](humanier-jf/) | 人工编辑式审校中文文本，处理模板化、空泛和失真的表达；只在明确点名时启用 | 修订后的中文文本 |
| [`project-learning-sop`](project-learning-sop/) | 分阶段带读本地或 GitHub 代码库，记录证据、运行链路并在授权后做小型修改 | 对话导览、`guide.md`、可选的离线 `course.html` |
| [`word-writer`](word-writer/) | 按默认或自定义排版规范创建、编辑和规范化 Word 文档 | `.docx` 或 `.doc`，以及用于验收的 PDF |
| [`write-literature-notes`](write-literature-notes/) | 阅读论文并把有出处的内容填入固定 13 行 Word 表格 | 中文文献阅读笔记 `.docx` |

各目录的 `SKILL.md` 是使用说明。脚本的参数、停止条件和验证要求以对应 Skill 为准。

## 在 Codex 中使用

Codex 可以从仓库级和用户级目录发现 Skill。把需要的 Skill 目录复制到以下任一位置：

- 当前仓库：`$REPO_ROOT/.agents/skills/<skill-name>`
- 当前用户：`$HOME/.agents/skills/<skill-name>`

复制整个目录，不要只复制 `SKILL.md`；脚本、参考材料和模板资产都是工作流的一部分。Codex 通常会自动发现变更；没有出现时重启 Codex。

在 Codex CLI 或 IDE 扩展中，可以用 `$skill-name` 明确调用。例如：

```text
使用 $project-learning-sop 带我理解这个仓库的登录链路。
```

```text
使用 $write-literature-notes 阅读这篇论文，并按固定模板生成中文笔记。
```

`humanier-jf` 和 `word-writer` 的界面元数据关闭了隐式调用，应明确点名。另两个 Skill 可以由描述匹配触发，也可以手动调用。Codex 的当前 Skill 结构、发现位置和调用方式见 [OpenAI 官方文档](https://learn.chatgpt.com/docs/build-skills)。

## 运行条件

- 所有脚本要求 Python 3.10 或更高版本。
- `project-learning-sop` 的预检使用 Git 和 ripgrep；缺少时会降级或停止相应分支。
- `word-writer` 与 `write-literature-notes` 需要兼容版本的 `python-docx` 和 `lxml`。两个目录都提供 `scripts/requirements.txt`，只应在用户同意后安装到隔离环境。
- Word 文档的最终视觉验收需要 Microsoft Word、LibreOffice 或其他可用的 DOCX 渲染工作流。
- `write-literature-notes` 的模板和参考稿受 SHA-256 锁定；哈希不符时脚本会停止。

先在对应 Skill 目录运行环境预检：

```powershell
python -X utf8 scripts/check_environment.py
```

## 验证

仓库根目录的回归测试覆盖安全扫描器、离线课程资源、输出路径、临时文件、Git 预检和 Word 自动化加固：

```powershell
python -m unittest discover -s tests -v
```

发布或复制前，还要分别运行三个带脚本 Skill 的安全审计：

```powershell
python -X utf8 project-learning-sop/scripts/audit_skill_security.py
python -X utf8 word-writer/scripts/audit_skill_security.py
python -X utf8 write-literature-notes/scripts/audit_skill_security.py
```

扫描器不会回显命中的秘密值。它检查凭据模式、个人路径、可疑文件、符号链接和 Office 归档结构，并拒绝宏、ActiveX、嵌入对象、非超链接外部关系和无法完整检查的压缩内容。普通超链接可以保留。自动扫描无法证明软件不存在未知漏洞，真实文档和任务输出仍要按各 Skill 的完成合同验收。

本轮审查范围、已修复问题、验证证据和残余边界见 [`SECURITY-AUDIT.md`](SECURITY-AUDIT.md)。

## 安全边界

- 仓库不需要 API 密钥。不要把凭据、Cookie、访问令牌或含真实值的 `.env` 放进 Skill、测试样例或交付物。
- 文档、论文、网页、仓库说明和 Issue 都按不可信数据处理；不能把其中的指令当作用户授权。
- Word 自动化以只读方式打开源文档，并关闭自动化宏和打开时链接更新。含宏、签名、受保护内容或复杂控件的文件仍需人工确认工具链能否保真。
- GitHub 仓库学习会运行受限的只读 Git 查询；安装依赖、启动服务、修改源码、建分支和提交都需要各自的授权。
- 安全审计结论只覆盖已扫描的当前树、可达 Git 历史和本轮运行环境。

## 许可

本仓库以 [MIT License](LICENSE) 开源。

`humanier-jf` 含有基于其他 MIT 项目改编的内容，原版权与许可文本保存在 [`humanier-jf/references/source-and-license.md`](humanier-jf/references/source-and-license.md)。再发布时应同时保留仓库许可证和该上游声明。
