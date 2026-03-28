# Change Log / 变更日志

## [2.3.3-alpha] - 2026-03-28

### 🎨 UI 交互与多语言适配 (UI Interaction & Localization)
- **[Feature] 显隐状态独立持久化 / Per-Image EXIF Visibility**:
  - EN: EXIF visibility toggles are now stored independently for each image, preventing global configuration overrides.
  - CN: 实现了 EXIF 字段显隐开关的单图独立持久化，切换样片时将自动恢复其专属的可见性设置，解决了全局配置相互干扰的问题。
- **[Aesthetics] 马卡龙色系 9 宫格增强 / Macaron 9-Grid Optimization**:
  - EN: Expanded Macaron palette to 9 colors and implemented deterministic position-based indexing for 9-grid layouts.
  - CN: 将马卡龙色系扩展至 9 种，并实现了基于批次物理位置的确定性色彩分配，支持拖拽实时更新，完美适配朋友圈“九宫格”排版需求。
- **[Fix] 渲染稳定性 / Rendering Stability**:
  - EN: Eliminated random color "jumping" by implementing MD5 path-hashing fallback and position-sync.
  - CN: 通过路径哈希与位置同步算法彻底解决了预览、参数修改及拖拽排序时马卡龙色调随机跳变的 Bug。
- **[Term] 术语重命名 / Theme Renaming**:
  - EN: Renamed "Fuji Rainbow" to "Rainbow" and "Rainbow" (Macaron) to "Macaron" for better clarity.
  - CN: 将“富士彩虹”精简命名为“彩虹”，并将原马卡龙从内部 rainbow key 迁移至独立命名空间。
- **[Feature] 纯净模式 / Pure Mode**:
  - EN: Introduced "Pure Mode" to suppress all text and logo overlays while preserving the border background.
  - CN: 新增“纯净模式”，可完全隐藏所有文字参数与相机 Logo，仅保留边框底色，满足极致简约需求。
- **[Feature] CJK 字库降级 / CJK Font Fallback**:
  - EN: Implemented automatic CJK character detection and system-default font fallback (Microsoft YaHei) for EXIF strings.
  - CN: 实现了 CJK 字符自动检测与系统字库自动降级逻辑，支持在手动覆盖字段中输入中文字符并正常渲染。
- **[Interactive] 回车即时刷新 / Enter-to-Refresh**:
  - EN: Added `<Return>` key bindings to all parameter entries for instant preview rendering update.
  - CN: 为设置面板中所有参数输入框绑定了回车事件，按下回车即刻触发现场预览重绘。
- **[Aesthetics] 边框主题 UI 降噪 / Theme Selector Refinement**:
  - EN: Simplified theme labels to pure single-language strings and increased dropdown width to 20 to prevent text clipping.
  - CN: 彻底简化了边框主题下拉框显示（移除冗余双语括号），并拓宽了组件宽度以确保长文本条目完整展示。

## [2.3.2] - 2026-03-27

### 🌈 彩虹重构与样品模式 (Rainbow Reborn & Sample Mode)
- **富士全谱渐变 (Fuji Rainbow Batch Slicing)**: 实现了真正的“连续光谱长卷”逻辑。在批量处理时，系统会自动将完整的彩虹光谱动态等分为 N 份（基于导入照片总数），确保拼接后呈现出丝滑、连贯、高保真的一体化视觉感。针对“灰感”反馈进行了专项饱和度回调。
- **马卡龙双色随机渐变 (Macaron Dynamic Gradient)**: 针对马卡龙模式（rainbow）进行了高保真升级。单张照片现在支持基于索引的 **“双色线性渐变”**（如粉过渡到蓝），营造出极其灵动、梦幻的视觉表现。
- **官方演示模式 (SAMPLE Metadata Mode)**: 新增 `is_sample` 参数支持。开启后，渲染引擎将强制覆盖相机、镜头、参数、胶卷等所有元数据为 **“SAMPLE”** 占位符，完美适配商业展示与样片分发。
- **排版去反色加固 (Locked Dark Typography)**: 统一锁定了所有彩虹主题的字体配色为经典的 **“深空灰”**（浅色模式标准）。废除了亮度自适应反白逻辑，确保在一片绚烂背景中依然具备顶级的阅读清晰度。

## [2.3.0-alpha] - 2026-03-27

### 开发初始化 / Development Initialization
- **[Task] v2.3.0 周期启动 / Lifecycle Start**:
  - EN: Created `v2.3.0` branch and bumped global version to `2.3.0-alpha`.
  - CN: 开启 `v2.3.0` 开发分支，并将全局版本号更新至 `2.3.0-alpha`。
- **[Docs] 文档规范重构 / Documentation Standards**:
  - EN: Initialized v2.3.0 release notes and overhauled progress tracking artifacts to be bilingual according to new AI guidelines.
  - CN: 初始化 v2.3.0 发布说明，并根据新的 AI 准则将进度追踪文档重构为中英双语格式。

## [2.2.3] - 2026-03-25

### Core & Contact Sheet / 核心与底片索引
- **[Fix] Manual Film Name Preservation / 手动胶卷名称锁定**:
  - EN: Fixed an issue where manual film inputs were overwritten by standard database names; manual strings are now strictly preserved.
  - CN: 修复了手动输入的胶卷型号会被数据库标准格式覆盖的问题，现在系统会严格保留用户的原始输入（如 KODAK 5207）。
- **[Fix] 135 Emulsion Display / 135 乳剂号显示修复**:
  - EN: Resolved a bug in the 135 renderer where the emulsion number was hidden; it now displays correctly alongside the film name.
  - CN: 修复了 135 渲染器中乳剂号被隐藏的 Bug，现在乳剂号会与胶卷名正常拼接显示。
- **[Feature] Flexible Image Sorting / 灵活图片排序**:
  - EN: Added support for sorting contact sheet images by Filename or EXIF Date, with an optional Reverse toggle.
  - CN: 底片索引新增了“图片排序”功能，支持按文件名或拍摄时间排序，并提供一键倒序开关。

### GUI & Environment / 界面与用户体验
- **[Fix] Advanced Settings Layout / 高级设置布局修复**:
  - EN: Refactored the Advanced Settings and EXIF Overrides into a balanced Grid layout to prevent text clipping and ensure consistent column widths.
  - CN: 将“高级设置”与“EXIF 覆盖”重构为等宽格栅布局（Grid），彻底解决了由于字符长度导致的标签挤压与输入框对不齐问题。
- **[Stability] Robust Multi-Source Sync / 强力多源同步**:
  - EN: Enhanced asset sync with Gitee API Token (CAPTCHA bypass), physical file verification (force download if empty), and robust ZIP root detection.
  - CN: 彻底重构资源同步逻辑，引入 Gitee Token 绕过验证码，增加“物理文件检索”机制（空文件夹强制重下），并优化了 ZIP 压缩包根目录自动识别。
- **[Feature] Config Decoupling / 配置文件解耦**:
  - EN: Decoupled `layouts.json`, `films.json`, and `contact_layouts.json` into `GT23_Assets/config` for easy user editing; internal defaults are automatically exported on first run.
  - CN: 实现了配置文件的全面解耦，现在 `layouts.json`、`films.json` 与 `contact_layouts.json` 会在首次运行时自动释放到 `GT23_Assets/config` 目录，且优先于内置配置加载，方便用户直接修改参数。
