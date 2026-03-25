# Change Log / 变更日志

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

## [2.2.3] - 2026-03-25

### Core & Functionality / 核心与功能
- **[Feature] Config Decoupling / 配置文件解耦**:
  - EN: Externalized `layouts.json` and `films.json` to `GT23_Assets/config/`. Users can now modify parameters without re-compiling.
  - CN: 将 `layouts.json` 和 `films.json` 配置文件外挂至 `GT23_Assets/config/`。由于实现了配置解耦，用户无需重新打包即可自定义边框与胶片参数。
- **[Feature] Manual Film Preservation / 手动胶卷名锁定**:
  - EN: Manual film strings are now strictly preserved and no longer overwritten by standard database matching.
  - CN: 实现了手动胶卷名称的强制锁定，确保用户手动输入的型号不再被数据库标准名覆盖。
- **[Feature] Flexible Image Sorting / 灵活图片排序**:
  - EN: Added filename and EXIF date sorting for contact sheets, including a reverse toggle.
  - CN: 索引页工具新增排序功能：支持按“文件名”或“拍摄时间”排序，并配备“倒序”开关。
- **[Fix] 135 Emulsion Display / 修复 135 乳剂号显示**:
  - EN: Resolved a bug where emulsion numbers were hidden in 135 format renders.
  - CN: 修复了 135 画幅渲染时乳剂号被隐藏的 Bug。

### Stability & Sync / 稳定性与同步
- **[Performance] Robust Multi-Source Sync / 强力多源同步**:
  - EN: Implemented physical file validation and Gitee Token mechanism to resolve "empty folder" download issues.
  - CN: 引入了物理文件校验与 Gitee API Token 机制，彻底解决了特定网络环境下同步成功但文件夹为空的问题。
- **[Aesthetics] 2026 Brand Icon / 2026 品牌图标更新**:
  - EN: Integrated high-resolution 2026 GT23 logo and generated multi-size .ico for Windows binaries.
  - CN: 集成了高清 2026 版 GT23 品牌图标，并为 Windows 版本同步生成了多尺寸 .ico 资源。
- **[Fix] UI Grid Alignment / 界面格栅对齐**:
  - EN: Refactored Advanced Settings with a uniform grid layout to prevent label crowding in different languages.
  - CN: 重构了高级设置面板的格栅布局，解决了多语言下标签重叠与对齐不均的问题。

## [2.2.2] - 2026-03-23

### Core & Efficiency / 核心与效率
- **[Performance] Extreme EXE Size Optimization / 极致 EXE 体积优化**:
  - EN: Slashed EXE size from ~200MB to **38.84 MB** (80% reduction) by purging 150MB+ of unused MKL/OpenMP binaries via manual `build.spec` filtering.
  - CN: 通过在 `build.spec` 中实施手动二进制过滤，彻底剔除 150MB+ 的冗余 MKL/OpenMP 库，将 EXE 体积从约 200MB 降至 **38.84 MB**，减重达 80%！
- **[Stability] Robust Sync Failover & Validation / 容错同步与签名校验**:
  - EN: Implemented automatic failover between GitHub and Gitee remotes. Added `PK\x03\x04` ZIP signature validation to prevent crashes from HTML error pages (404/Login redirects).
  - CN: 实现了 GitHub 与 Gitee 双源自动切换机制。新增了 `PK\x03\x04` ZIP 签名强制校验，有效防止因网络重定向或 404 HTML 页面导致的同步崩溃。
- **[Feature] Manual Image Rotation / 手动图像旋转**:
  - EN: Added minimalist, zero-background rotation icons (↺/↻) with 14pt primary color styling. Implemented automatic EXIF orientation fixing via `ImageOps.exif_transpose`.
  - CN: 新增了极简、无背景的旋转图标（↺/↻），采用 14pt 品牌色设计。引入了 `ImageOps.exif_transpose` 自动修复 EXIF 方向信息。
- **[Fix] Unified Rotation Logic / 统一旋转逻辑**:
  - EN: Fixed a critical bug where preview rotation was not passed to the batch engine. Now "What You See Is What You Get" is fully implemented for both single and batch renders.
  - CN: 修复了预览旋转角度未传递至批量引擎的 Bug，实现了单张预览与批量导出结果的完全一致。
- **[Fix] Batch Engine Stability / 批量引擎稳定性修复**:
  - EN: Resolved `NameError` and `UnboundLocalError` in `apps/border_tool.py` and fixed a UI bug where the completion dialog showed "0 photos processed".
  - CN: 解决了批量处理引擎中的变量定义报错，并修复了处理完成后弹窗错误显示“已处理 0 张照片”的统计 Bug。
- **[Architecture] Triple-Path Logic Alignment / 三位一体路径对齐**:
  - EN: Standardized asset pathing across Sync Engine, Renderer, and MetadataHandler to use a consistent `GT23_Assets` folder next to the EXE.
  - CN: 统一了同步引擎、渲染器与元数据处理器三方的路径逻辑，确保一键同步后图标与配置文件能立刻被软件精准识别。
- **[Feature] Smart Incremental Web Sync / 智能增量 Web 同步**:
  - EN: Implemented remote commit hash validation via Gitee/GitHub APIs; the app now skips redundant ZIP downloads if the asset library is already up to date.
  - CN: 引入了基于 Gitee/GitHub API 的远程 Commit Hash 校验机制；当资源库已是最新时，程序会自动跳过全量 ZIP 下载，极大节省了流量与同步时间。

### GUI & User Experience / 界面与用户体验
- **[Enhancement] Bilingual Sync Feedback Polish / 同步反馈双语优化**:
  - EN: Optimized the sync result dialog to display only the relevant language (EN or CN) based on current user settings, eliminating cluttered dual-language presentation.
  - CN: 优化了同步结果对话框的显示逻辑，根据用户当前语言设置精准展示单一语言（中文或英文），解决了之前“中英双语堆叠”导致的视觉凌乱。


### GUI & Stability / 界面与稳定性
- **[Fix] UI Stability Hotfix / 界面稳定性大修复**:
  - EN: Resolved `TclError` (pady/padx) and `NameError` in Settings and Sync dialogs by refactoring the core GUI logic and geometry management.
  - CN: 通过重构 GUI 核心逻辑与几何管理器，彻底解决了设置和同步对话框中的 `TclError`（pady/padx 参数错误）及 `NameError` 崩溃问题。
- **[Enhancement] Polished Settings UI / 深度优化设置界面**:
  - EN: Implemented a foolproof vertical layout for sync sources and adopted high-quality system fonts ("Microsoft YaHei" & "Segoe UI") to ensure crisp rendering and prevent text clipping in English mode.
  - CN: 引入了防呆式纵向同步源布局，并采用系统级原生字体（微软雅黑与 Segoe UI），确保了在高分屏下文字渲染精密且英文文本不再被截断。
- **[Feature] Dynamic "About" Dialog / 动态“关于”窗口**:
  - EN: Refactored the About dialog to dynamically pull version, author, and email info from `version.py`, ensuring data consistency across the app.
  - CN: 重构了“关于”对话框，使其版本、作者及联系信息自动与 `version.py` 同步，消灭了硬编码导致的数据滞后。
- **[Performance] Preview Debouncing Engine / 预览渲染防抖引擎**:
  - EN: Implemented a 300ms debounce timer for preview renders; successfully reduced redundant startup "Render Complete" logs from 5 lines to 1.
  - CN: 为预览渲染引入了 300ms 防抖机制，成功将启动时因初始化触发的冗余“渲染完成”日志从 5 条降至 1 条，显著优化了性能感。

### Assets & Synchronization / 资产与同步
- **[Architecture] Asset Decoupling (GT23_Assets) / 资产库彻底分离**:
  - EN: Decoupled 121+ camera logos into a standalone repository (`GT23_Assets`) and integrated it as a Git Submodule, significantly reducing main repository size and improving asset maintenance.
  - CN: 将 121+ 款相机图标彻底从主仓库剥离，建立独立的 `GT23_Assets` 资源库并以 Git Submodule 形式集成，大幅精简了主仓库体积并提升了资源维护效率。
- **[Feature] Dual-Remote Sync Strategy / 双源远程同步策略**:
  - EN: Implemented a robust dual-target synchronization system (GitHub + Gitee) with automatic failover, ensuring reliable asset updates regardless of network conditions in different regions.
  - CN: 实现了 GitHub + Gitee 双目标远程同步系统，支持自动故障切换，确保国内外用户在不同网络环境下都能稳定更新资源。
- **[Feature] "Sync Border Assets" One-Click Update / 一键资源同步功能**:
  - EN: Added a user-friendly sync feature in the Help menu that supports automatic ZIP download and extraction for users without a local Git environment.
  - CN: 在帮助菜单中新增了“同步边框资源”功能，支持在无 Git 环境下自动下载 ZIP 包并完成静默解压归位。
- **[Feature] Real-time Asset Statistics / 实时资产加载统计**:
  - EN: The Processing Log now displays the exact count of loaded camera logos (SVG+PNG) alongside the film count on startup.
  - CN: 程序启动日志现在会同步展示已加载的相机边框（SVG+PNG）实时总数，让资产库规模一目了然。
- **[Fix] Non-Git Sync Reliability / 修复 Git 环境缺失下的同步中断**:
  - EN: Resolved crashes in `asset_sync.py` by adding missing `os/sys` imports and refining the Web/ZIP fallback download sequence.
  - CN: 补全了 `asset_sync.py` 中缺失的 `os/sys` 导入，并优化了 Web/ZIP 模式下的降级下载流程，确保非开发环境下也能一键同步。


## [2.2.0] - 2026-03-14

### GUI & User Experience / 界面与用户体验
- [v2.2.0] Consolidate Android Migration Master Spec (Bilingual/Detailed)
- [v2.2.0] Massive logo library expansion (121 models) and asset decoupling via GT23_Assets submodule
- [v2.2.0] [GUI] Added "Sync Border Assets" feature in Help menu for one-click library updates
- **[Feature] One-Page Layout Optimization / “一页流”布局优化**:
  - EN: Redesigned settings panel with a wider 750px sidebar and a compact 2-column grid for Advanced Settings and EXIF Overrides.
  - CN: 重新设计了设置面板：将侧边栏宽度增至 750px，并将高频使用的“高级设置”与“EXIF 覆盖”调整为紧凑的双列网格布局。
- **[Enhancement] High-DPI & Visibility / 高分屏适配与可见性增强**:
  - EN: Increased default window height to 1100px to ensure core action buttons are visible without scrolling on most displays.
  - CN: 将默认窗口高度提升至 1100px，配合宽度调整，实现了核心功能“一眼全览”的目标，大幅减少了垂直滚动操作。
- **[Fix] UI Stability Hotfix / 界面稳定性修复**:
  - EN: Fixed an `AttributeError` during language switching and resolved a `TclError` caused by an invalid layout option.
  - CN: 修复了切换语言时可能出现的属性读取报错，并解决了因非法布局参数导致的启动崩溃问题。

### Assets & Customization / 资源与定制化
- **[Feature] External Logo Management / Logo 资源外置化**:
  - EN: Implemented auto-bootstrapping for logos; the app now automatically creates an external `logos/` folder next to the EXE for easy user customization.
  - CN: 实现了 Logo 资源的外置引导逻辑：程序在打包后首次运行时会自动在 EXE 同级目录下生成 `logos/` 文件夹，方便用户免打包增加自定义 Logo。
- **[Enhancement] Professional Neutral Reference / 专业中性预览参考**:
  - EN: Updated the official Logo Map with a professional neutral background for a clear visual reference of border and label interactions.
  - CN: 更新了官方 Logo 全景图，采用专业的中性背景，为摄影师提供更清晰的边框与标签交互预览参考。
- **[Fix] EOS R1 Logo Matching / 修复 EOS R1 图标匹配**:
  - EN: Renamed `EOS R1.png` to `CANON-EOS R1.png` to ensure correct automatic brand-model matching.
  - CN: 将 `EOS R1.png` 更名为 `CANON-EOS R1.png`，确保了该机型能根据 EXIF 数据自动匹配品牌图标。

### Build & Deployment / 构建与部署
- **[Feature] Versioned EXE Naming / EXE 文件名自动化版本管理**:
  - EN: Output executable now automatically includes version suffixes (e.g., `GT23_Workflow_v2.2.0.exe`).
  - CN: 生成的可执行文件现在会自动包含版本号后缀（如 `GT23_Workflow_v2.2.0.exe`），方便用户管理不同版本的安装包。
- **[Enhancement] Streamlined Build Script / 优化打包批处理**:
  - EN: Removed blocking `pause` commands in `build_gui.bat` for smoother automation and cleared file locks before building.
  - CN: 移除了 `build_gui.bat` 中的阻塞性 `pause` 命令，并在构建前自动清理文件占用，提升了打包过程的连贯性。


## [2026-03-13] - v2.1.1 Hotfix

### Logo Recognition & Assets / 图标识别与资源修复
- **[Fix] TVS Logo SVG Repair / 修复 TVS 图标受损**:
  - EN: Repaired corrupted `viewBox` in `CONTAX-TVS.svg` that caused it to render as an empty image.
  - CN: 修复了 `CONTAX-TVS.svg` 文件中损坏的 `viewBox` 属性（宽度为负值），解决了该机型图标渲染为空白的问题。
- **[Enhancement] Uniform Logo Scaling / 图标视觉尺寸统一化**:
  - EN: Implemented "Crop-then-Scale" logic to ensure all logos have identical visual height regardless of internal whitespace in the source files.
  - CN: 实现了“先裁剪后缩放”逻辑，通过物理剔除图标透明留白再进行等比缩放，确保了 30 余款不同品牌 Logo 在视觉上的整齐划一。
- **[Enhancement] Extreme Fuzzy Matching / 极端模糊匹配引擎**:
  - EN: Implemented symbol-agnostic matching that ignores spaces and hyphens (e.g., "TVS II" now correctly matches the "TVSII" asset).
  - CN: 引入了符号无关的匹配逻辑，自动忽略空格、横杠等特殊字符（例如：让 EXIF 中的 "TVS II" 能自动对准本地的 "TVSII" 图标资源）。

## [2026-03-11] - v2.1.0 Release

### Camera Logo & Typography / 相机图标与排版系统
- **[Feature] Vector Logo Support / 矢量图标支持**:
  - EN: Integrated high-quality SVG logos for Contax G/T/TVS series.
  - CN: 集成了 Contax G/T/TVS 等系列的高质量矢量 SVG 图标。
- **[Feature] PNG/Raster Logo Support / PNG 栅格图标支持**:
  - EN: Added support for bitmap logos (e.g., Pentax 67) to enhance user-defined camera identification.
  - CN: 增加了对位图图标（如 Pentax 67）的支持，允许用户自定义更多非矢量相机标识。
- **[Enhancement] Smart Model Matching / 智能型号匹配**:
  - EN: Implemented intelligence to detect popular models (G2, T3, 67, etc.) even when brand name (Make) is missing from EXIF.
  - CN: 实现了智能型号识别，即使 EXIF 中缺失品牌信息，也能自动匹配 G2, T3, 67 等机型的图标。
- **[Enhancement] Optical Centering (Ink BBox) / 视觉对齐 (Ink BBox)**:
  - EN: Re-engineered text/logo centering based on actual "Ink" pixels rather than character advance for pixel-perfect balance.
  - CN: 基于“墨迹像素”而非字符步进重构了对齐算法，确保 Logo 与文字在视觉中轴线上达到完美的物理对齐。
- **[Enhancement] Zeiss T* Highlight / 蔡司 T* 红色标识**:
  - EN: Automatically detects "T*" in lens models and renders it in standard Zeiss Red (#ed1f25).
  - CN: 自动检索镜头型号中的 "T*"，并将其渲染为蔡司标准的鲜红色 (#ed1f25)。

### Social Media & Performance / 社交平台与性能优化
- **[Feature] Pro JPEG Export / 专业 JPEG 导出流程**:
  - EN: Defaulted to ultra-high-resolution (4500px) and near-lossless (Quality 98) JPEG for maximum compatibility.
  - CN: 默认采用 4500px 超清分辨率与 98 几乎无损质量的 JPEG 导出，确保全平台最佳兼容性。
- **[Performance] Rendering Engine Overhaul (PNG to JPEG) / 渲染引擎重构 (PNG 切换为 JPEG)**:
  - EN: Switched from a high-compression PNG pipeline to an optimized JPEG workflow, delivering a **3x-5x faster rendering speed** while maintaining near-lossless quality.
  - CN: 渲染引擎由高压缩 PNG 流程全面重构为优化的 JPEG 流程。在保持几乎无损画质的前提下，**渲染速度提升了 3-5 倍**，实现秒级导出。
- **[Fix] Hardened Shadows (No More White Corners) / 阴影硬化 (彻底解决白角问题)**:
  - EN: Pre-flattens shadows on white background to prevent artifacts when social platforms (e.g., Xiaohongshu) compress images.
  - CN: 实现了阴影本地硬化复合，避免了小红书等平台在压缩透明底图时产生的“白色方块”或阴影丢失问题。
- **[Adjustment] Shadow Margin Refinement / 阴影边距精修**:
  - EN: Reduced shadow margin by 50% for a more compact and modern professional look.
  - CN: 将衬底阴影边距缩小了一半，使整体视觉效果更紧凑、更精致。

### Stability & UX / 稳定性与体验改进
- **[Fix] GUI Preview Hang / 修复 GUI 预览卡死**:
  - EN: Resolved hang caused by hardcoded .png extension; now dynamically tracks real output files.
  - CN: 修复了因硬编码 .png 后缀导致的 GUI 预览卡死问题，现在支持动态追踪实际输出格式。
- **[Fix] Logo Centering Collision / 修复 Logo 居中冲突**:
  - EN: Fixed variable shadowing bug that caused logos to be left-aligned instead of centered.
  - CN: 修复了一个变量名冲突导致的 Bug，该 Bug 曾导致 Logo 无法居中（靠左显示）。
- **[Fix] GUI Error Handling / 改进 GUI 异常处理**:
  - EN: Fixed NameError in exception dialogs to ensure error messages are properly displayed.
  - CN: 修复了异常对话框中的变量名错误，确保在运行出错时能正确弹出提示信息。


## [2026-02-01]

### Matin Slide Mode Re-engineering / 马田幻灯片模式重构
- **[Feature] Slide Master v4 (Precision Lightbox Edition) / 幻灯片“大师版 v4” (精密仿真)**:
  - EN: Strict brightness calibration: Board (#F5F5F5) > Mount (#E2E2E2). Fixed previous edge-inversion.
  - CN: 严格明暗校准：灯板 (#F5F5F5) > 片框 (#E2E2E2)。从根本上解决了边缘处亮度倒挂的问题。
  - EN: Recessed Inner Shadow: Implemented realistic depth using blurred masking instead of outlines.
  - CN: 真实内凹陷阴影：弃用机械描边，采用模糊蒙版技术模拟阶梯状的物理下陷感。
  - EN: Refined Bloom & Texture: 8-10px warm bloom and optimized 1.5% monochromatic noise.
  - CN: 优化溢光与纹理：应用 8-10px 暖色 Bloom 环境光与优化的 1.5% 单色噪点。

### Layout Calibration & Proportions / 布局校准与比例修复
- **[Fix] Scale-Aware Rendering / 感知缩放的渲染系统**:
  - EN: Refactored all internal offsets (text, corners, glow) to be proportional to cell size.
  - CN: 将所有内部偏移（文字、圆角、溢光）重构为相对于格口尺寸的比例计算，修复了预览图比例失准问题.
- **[Layout] Binder Hole Offset / 装订孔偏置校准**:
  - EN: Set fixed 20mm (472px) left margin for binder holes and implemented even horizontal distribution for gaps.
  - CN: 设置了固定的 20mm (472px) 左边距用于避让装订孔，并实现了等间距均布逻辑。
- **[Visual] Minimalist Cleanup / 视觉去装饰化**:
  - EN: Removed all legacy skip-shadows and bevels in favor of clean physical geometry.
  - CN: 移除了所有旧有的投影和倒角装饰，转向纯粹的物理几何呈现。

### Realistic Handwriting & Custom Labels / 真实手写体与自定义标签
- **[Feature] handright Library Integration / handright 库集成**:
  - EN: Integrated `handright` library for organic jitter in character rotation and spacing.
  - CN: 集成了 `handright` 库，实现了字符旋转和间距的自然随机抖动。
- **[Feature] Multiply Blend Mode / 正片叠底混合模式**:
  - EN: Applied Multiply blending for labels to simulate realistic oil marker ink on surfaces.
  - CN: 标签采用正片叠底模式绘制，模拟油性记号笔覆盖在表面上的真实观感。
- **[Feature] Font Selection & Bolding / 字体选择与加粗**:
  - EN: Added UI for font selection and implemented alpha dilation to simulate thicker marker strokes (Bold).
  - CN: 增加了字体选择 UI，并通过 Alpha 扩张算法模拟了更粗的记号笔笔触（加粗效果）。
- **[Fix] Font Size & Format Consistency / 字号与画幅一致性修复**:
  - EN: Fixed mismatch between single preview and final render by propagating `label_cfg` to all paths.
  - CN: 通过在所有路径传递 `label_cfg`，修复了单张预览与最终生成图中字号不一致的问题。

### Interactive Settings & Anti-Aliasing (Part 2) / 交互式设置与抗锯齿 (第二部分)
- **[Aesthetics] 3x Oversampling Anti-Aliasing / 3 倍过采样抗锯齿**:
  - EN: Implemented 3x oversampling with Lanczos downscaling for silk-smooth text edges.
  - CN: 实现了 3 倍过采样配合 Lanczos 缩小算法，消灭了手写文字的边缘锯齿，获得丝滑观感。
- **[Aesthetics] Smooth Bolding / 平滑加粗**:
  - EN: Replaced harsh dilation with `MaxFilter` + `GaussianBlur` to simulate organic marker ink bleeding.
  - CN: 将硬性的边缘扩张替换为 `MaxFilter` + `GaussianBlur` 组合，模拟真实墨水的微量晕染感。
- **[UI] Handright Settings Dialog / 手写体设置对话框**:
  - EN: Added scrollable and resizable dialog for real-time adjustment of word spacing, line spacing, and jitters.
  - CN: 增加了支持滚动和拉伸的设置弹窗，支持实时调节字距、行距以及各种随机抖动参数。
- **[UI] Regenerate Button / 重新生成按钮**:
  - EN: Added a "Regenerate" button to quickly refresh random handwriting variations without parameter changes.
  - CN: 增加了“重新生成”按钮，允许在不改变参数的情况下快速刷新随机的手写变化。
