# Phase 5-7 详细指引：核心抽象、功能链路深读、项目地图汇总

> 本文件在 Phase 5 开始时读取，覆盖 Phase 5（核心抽象）、Phase 6（功能链路深读）、Phase 7（汇总交付）的完整操作细节。

## Phase 5：核心抽象与架构

### 5.1 找出核心名词（按项目类型速查）

| 项目类型 | 典型核心抽象 |
| --- | --- |
| Web 框架 | Application、Router、Request、Response、Middleware、Dependency、Handler |
| 数据库 | Connection、Transaction、Query、Storage、Index、WAL、Replication |
| 机器学习框架 | Tensor、Module、Model、Optimizer、Dataset、Trainer、Loss |
| 消息系统 | Producer、Consumer、Broker、Topic、Partition、Offset |
| 前端框架 | Component、State、Props、Hook、Store、Virtual DOM |
| CLI 工具 | Command、Option、Parser、Runner、Config |
| 微服务/云原生 | Service、Deployment、Config、Discovery、Gateway、Sidecar |

**方法**：先让学习者猜（"你觉得这个项目里最重要的几个名词是什么？"），AI 再补充修正。不要一次性列出全部类名，只提炼 3-6 个"核心名词"。

### 5.2 厘清关系（一句话架构）

目标：能用一句话说清"**A 创建 B，B 调用 C，C 管理 D**"。示例：

- Web 框架：`Application 创建 Router，Router 把请求分发给 Handler，Handler 调用 Service，Service 操作 Database`
- 数据库：`Client 创建 Connection，Connection 执行 Query，Query 经由 Storage 读写，Storage 依赖 Index 与 WAL`

### 5.3 画架构图（允许不完美）

用 ASCII 图即可，不追求精确，之后每个 Phase 都可修正：

```text
User
 │
 ▼
API Gateway
 │
 ▼
Web 服务 ──→ Cache (Redis)
 │
 ▼
Database
```

**指导**：学习者必须参与画图（至少口头描述每一层），AI 负责把描述变成图。画完问一句："你觉得这张图哪里最可能画错了？"——这个问题本身就在训练架构思维。

### 5.4 验证理解

- "用一句话讲这个项目的架构。"（标准：出现核心名词 + 关系动词）
- "如果我要给用户加一个'收藏'功能，按你的理解，这条链路会经过哪些部分？"（不要求正确，要求有推理过程）

### 5.5 产出：追加到 `notes/working.md`

```markdown
# 核心抽象与架构

## 核心名词
- <名词1>：<职责>
- <名词2>：<职责>

## 一句话架构
<A 创建 B，B 调用 C，C 管理 D……>

## 架构图
<ASCII 图>

## 存疑点
- <哪里还没想明白>
```

## Phase 6：功能链路深读

### 6.1 选择链路

由学习者从 Phase 4 记录的流程中选择 1 条（AI 提供建议但最终学习者决定）。**优先选学习者最想改的功能**——这样 Phase 8 修改实践可以直接复用。

### 6.2 追踪调用链（核心方法）

以 Web 项目"登录"为例的追踪模板：

```text
点击登录按钮（前端）
  → HTTP POST /login（网络层）
  → Router 匹配路由（路由层）
  → Controller/Handler：login()（入口函数）
  → Service：authenticate_user()（业务逻辑）
  → Repository：UserRepository.find()（数据访问）
  → database.query()（存储层）
  → 返回结果 → 前端更新状态
```

操作步骤：
1. **找入口**：路由定义（`@app.post("/login")`、`@PostMapping`、routes 文件）或 CLI 命令定义、`main()`/入口文件。
2. **逐层下钻**：每找到一个函数，看它调用了什么，把调用关系记录成缩进树；用 IDE/编辑器的“查找引用”或全局搜索（优先 `rg`，不可用时再用其他工具）定位被调函数。
3. **每层记录**：文件路径 + 函数名 + 职责一句话。
4. **遇到不认识的函数先跳过**：标记为"待理解"，先走完主链路，再回来补。

### 6.3 用测试验证理解（tests 是最好的文档）

遇到不理解的行为，先搜索测试：

```bash
rg -n "authenticate_user|/login" tests/  # 或按函数名/API 名搜索
```

测试明确表达了：输入是什么、调用什么接口、期望结果是什么、异常情况是什么。**测试比实现代码更容易告诉你"作者希望这个模块怎么被使用"。**

### 6.4 用 git 历史理解"奇怪代码"

- `git blame <file>`：某行是谁改的、哪个 commit。
- `git log --oneline -- <file>`：该文件的历史。
- `git show <commit>`：看那次改动的 diff 与 commit message。
- 再到 GitHub 找到对应 PR，看讨论（为什么不用方案 A？会不会破坏兼容性？）。
- 常见结论：看似莫名其妙的代码 = 历史 bug 修复 / 兼容性处理 / 性能优化。

### 6.5 验证理解（重点验证）

- 让学习者**不看代码**，凭记忆画出这条链路的每一层（可口头）。
- 让学习者回答一个"如果"问题："如果登录时密码错误，链路在哪一层返回错误？"（要求指向具体函数）
- 卡住时先给提示（如"想想 Service 层和 Controller 层谁该校验密码"），两次提示无效再展示答案。

### 6.6 产出：更新工作底稿 `notes/working.md`

```markdown
## 调用链记录
### 链路一：<功能名>
入口：<文件:行号 函数名>
<缩进调用树，每层：文件路径 / 函数名 / 行号 / 一句话职责>

## 关键发现
- <测试揭示了什么设计意图>
- <git 历史解释了哪段奇怪代码>
- <有趣的设计模式 / 待深挖点>
```

> 调用链记录将直接成为 `guide.md` 第 6 节"核心代码路径"的素材，务必精确到行号。

## Phase 7：学习检查点与深度带读交付

### 7.1 全面验收

用 `references/checklist.md` 的“最终 8 问”逐题评分。未达到阈值时标记薄弱 Phase，补一个针对性小练习；学习者拒绝补练时记录为 `unverified`，不得宣称通过。

### 7.2 深度带读模式：生成 `notes/guide.md`

1. 读取 `notes/working.md` 的目标、证据账本、目录、运行、流程、抽象和调用链。
2. 按 `references/guide-spec.md` 生成 `guide.md`。
3. 不可省略：功能地图、功能→文件→代码导航表、架构图、数据流图和源码基线。
4. 学习者用 `guide.md` 完成 3 个随机导航任务；每个任务要找到对应文件与函数。
5. 预览并修正内容后结束深度带读模式，不生成 `course.html`。

学习者持续回答“继续”或拒绝验收时，用自答自讲完成讲解，生成标题下明确标注“学习验收未完成”的暂定 guide，运行静态校验后停止。此时 Phase 7 和整体模式均记录为 `unverified`，不得声称导航练习或深度带读已经通过。

### 7.3 完整实战模式：冻结证据，延迟交付

1. 不在本阶段生成最终文件，避免 Phase 8 修改源码后行号和内容失效。
2. 把已验证导航项、待修改链路和任务候选写入 `working.md`。
3. 选择一个与目标一致的实质任务，并在进入 Phase 8 前确认修改权限。
4. `guide.md` 与 `course.html` 统一在 Phase 9 基于最终源码快照生成。
