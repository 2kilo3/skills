# course.html 交互式课程规范

> 本文件只在完整实战模式的 Phase 9 生成 `course.html` 时读取。产物是**单文件交互式 HTML 课程**：零依赖、无构建、离线可开。设计哲学参考 codebase-to-course：**从用户行为出发的教学弧线、Show don't tell、测验测做事不测记忆、原始代码不改写**。它与 guide.md（导航指南）同源，但视角不同：guide 负责“查”，course 负责“学”。

## 1. 文件与总体结构

- 文件名：`course.html`，与 `guide.md` 同目录（`notes/`）。
- 单文件包含 `<style>` 与 `<script>`，不引用外部资源；图标用 Unicode/emoji，字体只用系统字体栈，保证断网可用。
- 页面上方固定导航条（模块按钮 + 当前进度），主体为滚动模块（`scroll-snap-type: y proximity`，`min-height: 100dvh` 带 `100vh` 回退）。

## 2. 教学弧线（模块设计：4-6 个模块）

课程永远**从学习者已经知道的东西出发**（用户可见行为），再逐步深入代码。模块定位菜单（按需选用，不是全要）：

| 模块位置 | 定位 | 对学习者的意义 |
| --- | --- | --- |
| 1 | "这个项目是什么 + 用一次它" | 从产品出发，先给一个具体用户动作，再进入代码 |
| 2 | 认识主角（核心组件/类） | 知道有哪些零件，才能"把逻辑放在 X 而不是 Y" |
| 3 | 零件怎么说话（数据流/调用关系） | 理解数据流动，才能调试"它为什么不显示" |
| 4 | 外部世界（API/数据库/存储） | 知道什么在外面，才能评估成本与失败模式 |
| 5 | 聪明技巧（缓存/延迟加载/错误处理） | 学会向 AI 提"要这类模式" |
| 6 | 动手改代码（修改实践） | 建立调试直觉，真正改一次 |

**模块内容要求（每模块）**：
- 3-6 屏（子节，模块内滚动）
- ≥1 处 代码↔白话对照
- ≥1 个交互元素（测验/动画/可视化，见第 3 节）
- 1-2 个"aha!"提示框（通用 CS 洞察）
- 1 个贴合该概念的比喻（**禁止跨模块复用比喻；禁止默认"餐厅"比喻**）

## 3. 强制交互元素（每份课程必须全部包含）

1. **数据流动画**（至少 1 处）：组件间逐步传递的动画（步骤逐步高亮即可，用 IntersectionObserver 触发）。
2. **组件对话**（至少 1 处）：iMessage/微信风格的组件间对话气泡，生动展示调用顺序。
3. **代码 ↔ 白话对照**（每模块至少 1 处）：左真实代码（标注文件路径），右 ≤2 句白话解释。
4. **交互测验**（每模块至少 1 处）：测"做事"不测记忆——"用户报数据是旧的，你先查哪层？"而不是"API 是什么意思？"
5. **术语提示**（每个术语模块内首次出现）：hover/聚焦显示大白话定义。

## 4. 内容哲学（Show, don't tell）

- 每屏**至少 50% 视觉**（图/代码/动画/卡片）；文字块最多 2-3 句话。
- 能做成图/动画/交互的，**绝不用段落**。
- 每屏回答"**why should I care?**"（这对学习者有什么用：更会指挥 AI / 更会调试 / 更会做决策），再讲"how"。
- **原始代码原则**：所有代码摘录从真实代码库**原样复制**，标注文件路径；禁止改写、简化、编造。学习者应能在源码中找到同一段。
- 每个真实代码块使用 `<pre data-source="仓库相对路径" data-lines="起始行-结束行"><code>...</code></pre>`；`code` 内不加语法高亮标签，保证校验器能逐字匹配源码。
- 语言大白话，默认零背景；术语必解释。

## 5. 设计系统（视觉规范）

- **暖色基调**：米白背景（`#faf8f5` 类），暖灰，禁用冷白/冷蓝。
- **一个大胆强调色**：朱红/珊瑚/青绿（如 `#c2410c`），**禁用紫色渐变**。
- **个性字体**：标题用有性格的展示字体（如 Bricolage Grotesque、Georgia 类衬线加粗；**禁用 Inter/Roboto/Arial**），正文用清爽无衬线（系统字体栈），代码用等宽（`ui-monospace, Consolas, monospace`）。
- **留白**：模块呼吸感，每屏最多 3-4 个短段落。
- **模块交替背景**：奇偶模块两种相近暖色交替（`#ffffff` / `#f4efe9`）。
- **深色代码块**：IDE 风格（背景 `#1e1e2e`，文字 `#cdd6f4`），可选 Catppuccin 系配色。
- **阴影柔和**：暖色阴影，禁用纯黑投影。

## 6. 交互元素实现要点

- 导航：模块按钮 `data-target` + `scrollIntoView({behavior:'smooth'})`，滚动时高亮当前模块。
- 数据流动画/流程步骤：`ol.flow li` + IntersectionObserver 加 `.hit` 类逐个高亮；需要"包在组件间传递"效果时用 `.chat` 气泡容器。
- 测验：`<details class="quiz">`（`<summary>` 问题 + `.answer` 答案），答案 2-4 句且指向具体文件。
- 术语提示：`.term` span 内嵌 `.tip`，CSS `position:absolute` hover/聚焦显示。
- 图片：非必要不使用；确需图片时嵌入 data URI，不创建额外图片文件，也不引用网络或相对路径资源。

## 7. 完整骨架示例（可直接复用并填充）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>《<项目名>》学习课程</title>
<style>
  :root { --bg:#faf8f5; --card:#ffffff; --ink:#1c1917; --accent:#c2410c;
          --code-bg:#1e1e2e; --code-ink:#cdd6f4; --alt:#f4efe9; --plain:#fef3c7; }
  * { margin:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--ink); font:16px/1.7 system-ui,"PingFang SC","Microsoft YaHei",sans-serif; }
  nav { position:sticky; top:0; background:var(--bg); border-bottom:1px solid #e7e5e4;
        padding:10px 24px; display:flex; gap:8px; flex-wrap:wrap; z-index:10; }
  nav button { border:1px solid #d6d3d1; background:var(--card); border-radius:999px;
               padding:6px 14px; cursor:pointer; }
  nav button.active { background:var(--accent); color:#fff; border-color:var(--accent); }
  main { max-width:880px; margin:0 auto; padding:40px 24px 80px; }
  section.module { background:var(--card); border-radius:16px; padding:40px;
                   margin-bottom:32px; scroll-margin-top:70px; }
  section.module:nth-child(even) { background:var(--alt); }
  h1 { font-size:38px; letter-spacing:-.5px; margin-bottom:8px; }
  h2 { font-size:25px; margin-bottom:14px; } h3 { font-size:18px; margin:18px 0 8px; }
  p { margin-bottom:12px; max-width:64ch; }
  table { border-collapse:collapse; width:100%; margin:12px 0; font-size:14px; }
  th,td { border:1px solid #e7e5e4; padding:8px 10px; text-align:left; }
  th { background:var(--alt); }
  pre { background:var(--code-bg); color:var(--code-ink); border-radius:10px; padding:16px;
        overflow-x:auto; font:13px/1.6 ui-monospace,Consolas,monospace; margin:12px 0; }
  code { font-family:ui-monospace,Consolas,monospace; background:#f0edea; padding:2px 5px;
         border-radius:4px; font-size:.92em; }
  pre code { background:none; padding:0; }
  .code-pair { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:16px 0; }
  .code-pair > div { border-radius:10px; overflow:hidden; }
  .code-side { background:var(--code-bg); color:var(--code-ink); }
  .plain-side { background:var(--plain); padding:16px; }
  .code-head,.plain-head { font-size:12px; opacity:.75; padding:8px 12px; }
  .code-side .code-head { color:#a5b4fc; } .plain-side .plain-head { color:#92400e; }
  .plain-side p { margin:0; }
  .quiz { border:1px dashed #d6d3d1; border-radius:10px; padding:14px; margin:16px 0; cursor:pointer; }
  .quiz summary { font-weight:600; }
  .quiz .answer { margin-top:10px; padding-top:10px; border-top:1px solid #e7e5e4; }
  .term { position:relative; border-bottom:1px dotted var(--accent); cursor:help; }
  .term .tip { display:none; position:absolute; bottom:130%; left:0; width:230px;
               background:#1c1917; color:#f5f5f4; padding:8px 10px; border-radius:8px;
               font-size:13px; z-index:20; }
  .term:hover .tip, .term:focus .tip { display:block; }
  ol.flow { list-style:none; counter-reset:f; }
  ol.flow li { counter-increment:f; padding:12px 16px; border-left:3px solid #d6d3d1; margin-bottom:8px; }
  ol.flow li::before { content:"0" counter(f); color:var(--accent); font-weight:700; margin-right:10px; }
  ol.flow li.hit { border-color:var(--accent); background:#fff7ed; }
  .chat { max-width:520px; margin:16px 0; }
  .chat .bubble { border-radius:14px; padding:10px 14px; margin:6px 0; max-width:80%; font-size:14px; }
  .chat .from-a { background:#fff; border:1px solid #e7e5e4; align-self:flex-start; }
  .chat .from-b { background:var(--plain); margin-left:auto; }
  .foot { text-align:center; color:#78716c; font-size:13px; padding:24px; }
  @media (max-width:720px) { .code-pair { grid-template-columns:1fr; } section.module { padding:24px; } }
</style>
</head>
<body>
<nav><!-- 每个模块一个按钮：<button data-target="m1">项目是什么</button> … --></nav>
<main>
  <section class="module" id="m1"><!-- 模块 1-5 按教学弧线填充 --></section>
  <section class="module" id="m6"><!-- 模块 6：动手改代码 --></section>
</main>
<div class="foot">由 Project Learning SOP 生成 · 离线可查看</div>
<script>
  const btns=[...document.querySelectorAll('nav button')];
  btns.forEach(b=>b.addEventListener('click',()=>{
    btns.forEach(x=>x.classList.remove('active')); b.classList.add('active');
    document.getElementById(b.dataset.target).scrollIntoView({behavior:'smooth'});
  }));
  const io=new IntersectionObserver(es=>es.forEach(e=>{
    if(e.isIntersecting) e.target.classList.add('hit');
  }),{threshold:.5});
  document.querySelectorAll('ol.flow li').forEach(s=>io.observe(s));
</script>
</body>
</html>
```

## 8. 内容纪律

- 代码摘录**原样复制**真实源码，标注文件路径；禁止改写/简化/编造。
- 白话解释 ≤2 句话；一屏最多 3-4 个短段落。
- 测验只考"做事"（去哪查、改哪里、为什么），不考背定义。
- 比喻不重复、不落俗套（默认禁"餐厅"）。
- 内容必须来自已产出的 `guide.md` / 工作底稿，不引入未学过的内容。
- 生成后打开 `course.html` 预览，请学习者确认内容准确、交互可用，再交付。
- 断网预览时外部网络请求为 0，浏览器控制台错误为 0；桌面与 360px 宽度均不得出现页面级水平溢出。

## 9. 自动验证

生成并预览后运行：

```bash
python <skill-root>/scripts/validate_artifacts.py course <learning-root>/notes/course.html <repo-root>
```

脚本检查模块、导航目标、必需交互、外部资源和真实代码逐字匹配，返回 0 后才可交付。浏览器控制台与响应式布局仍需通过实际预览确认。校验后若修改 HTML，必须重新预览并重跑；不得用旧结果证明新文件通过。
