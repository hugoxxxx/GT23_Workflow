# Copilot / AI Agent Instructions — 项目快速上手指南

此文件为 AI 编码代理的操作指引，简洁列出本仓库的架构要点、关键路径、约定与可执行命令（中英双语）。

## 1. Big picture / 大局观
- Project: 胶片索引页生成器 (contact sheet renderer)。核心库放在 `core/`，工具脚本在 `apps/`，配置在 `config/`，入口为 `main.py`。
- `core/metadata.py` 负责 EXIF 与影像元数据解析；`core/renderer.py` 提供渲染骨架；具体画幅渲染在 `core/renderers/` 下（比如 `renderer_66.py`, `renderer_645.py`）。

## 2. Key files to inspect / 关键文件
- `AI_CONTEXT.md` — 项目设计约定、审美与必遵规范（务必阅读）。
- `main.py` — 程序入口，运行流程调度点。
- `core/metadata.py`, `core/renderer.py`, `core/film_simulator.py` — 渲染与元数据核心逻辑。
- `apps/border_tool.py` — 边框/留白逻辑被抽成独立工具，修改边框逻辑请从此处入手。
- `config/*.json` (`films.json`, `contact_layouts.json`, `layouts.json`) — 所有物理和版式参数由 JSON 配置驱动，改变样式/画幅优先修改这些文件。

## 3. Project-specific conventions / 项目约定（必须遵守）
- 双语注释：所有新代码/修改**必须**包含中英双语注释（见 `AI_CONTEXT.md`）。
- 视觉优先：当像素对齐与“视觉平衡”冲突时，优先遵守审美准则（模拟真实底片感）。
- 单位与字体：焦距使用 `mm`（小写）；参数显示偏好 `Seven Segment` 字体（色彩与位置按 `AI_CONTEXT.md`）。
- 配置优先：渲染参数（步进、间距、喷码位移）由 `config/*.json` 控制，代码应读取并尊重这些值而非硬编码。

## 4. Common code patterns / 常见代码模式
- 渲染子类：新增画幅时，在 `core/renderers/` 添加 `renderer_<format>.py` 并遵循 `base_renderer.py` 的接口。示例文件：`core/renderers/renderer_66.py`。
- 数据流：`main.py` -> 读取 `config/*.json` -> `core/metadata` 解析图片 -> 传入 `core/renderer` -> 输出到 `photos_out/`。
- 工具分离：可将交互或可视化工具放入 `apps/`，工具应尽量只依赖核心库接口，不直接修改底层状态。

## 5. Run & debug / 运行与调试
- 快速运行（假设使用当前 Python 环境）：

```powershell
python main.py
```

- 手动验证配置：编辑 `config/contact_layouts.json` 后，运行 `python main.py` 来观察渲染变化（没有测试套件，手动运行为主）。

## 6. How to add a renderer / 添加新画幅的步骤
1. 在 `core/renderers/` 添加 `renderer_<name>.py`，继承 `base_renderer.BaseRenderer`。
2. 在 `config/contact_layouts.json` 和 `config/layouts.json` 添加对应布局条目（物理步进、间距、喷码规则）。
3. 在 `core/renderer.py` 或渲染注册点添加识别逻辑（通常按画幅名称选择子类）。
4. 保证新代码包含中英双语注释，更新 `AI_CONTEXT.md` 中的进度/路线图如有必要。

## 7. Configuration and tuning / 配置与调优要点
- `films.json` 控制不同胶片的色彩倾向与喷码样式；`contact_layouts.json` 控制物理格子与步进；`layouts.json` 控制边框渲染。
- 首先通过 JSON 调整参数，只有在无法用数据驱动时才改动渲染算法本身。

## 8. Things not present / 仓库中未发现但要注意
- 没有测试目录或 CI 配置（在修改核心渲染逻辑时请手动验证输出）。
- 未发现现成的 CONTRIBUTING/AGENT 文件；本文件目标是填补该空白并供 AI 代理使用。

## 9. Quick PR guidance for AI agents / AI 代理提交 PR 要点
- 每次改动附带中英说明与短截图或输出示例（若为渲染变更）。
- 修改行为应优先修改 `config/*.json` 并提供对比截图，而非直接改算法，除非确有必要。

---
请审阅本文件并指出需补充的细节（例如：具体运行参数、虚拟环境命令或 CI 流程）。
