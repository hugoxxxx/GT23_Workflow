
# Change Log / 变更日志

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
