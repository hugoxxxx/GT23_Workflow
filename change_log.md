# Change Log / 变更日志

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
- **[Performance] Massive Speed Boost / 导出速度飞跃**:
  - EN: 3x-5x faster rendering compared to legacy PNG pipeline due to highly optimized JPEG encoding.
  - CN: 得益于优化的 JPEG 编码流程，渲染速度相比以往的 PNG 模式提升了 3-5 倍，渲染缩短至秒级。
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
