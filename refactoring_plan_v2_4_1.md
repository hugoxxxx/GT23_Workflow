# GT23 渲染引擎模块化重构施工方案 (v2.4.1)

本方案旨在将 `core/renderer.py` 从目前的 1500+ 行精简至 150-200 行，通过职责分离提高代码的可维护性。重构将遵循“七大模块”架构，确保每个组件职责单一。

## 🎯 总体目标
- **FilmRenderer**: 仅负责渲染流水线的编排（Orchestration）。
* **core/io**: 负责图片的读、写、转及 EXIF 处理。
* **core/branding**: 负责品牌标识识别与 Logo 检索。
* **core/typography**: 负责字体解析与自适应缩放。
* **core/layout**: 负责边距、画幅比例及齿孔模式计算。
* **core/theme**: 负责不同视觉风格的具体渲染实现。
* **core/effects**: 负责投影、纹理等视觉特效。

---

## 🛠️ 施工步骤 (Step-by-Step)

### 第一阶段：底层 IO 与 工具类 (Foundation)
1. **ImageLoader 迁移** (`core/io/image_loader.py`) [x]
   - 迁移 `process_image` 中的加载、`exif_transpose`、`rotate` 及 `_smart_resize` 逻辑。
2. **ExifEditor & Saver 迁移** (`core/io/exif_editor.py`, `core/io/saver.py`) [x]
   - 迁移 `_build_exif_bytes` 及最终的 `flatten` 和 `save` 逻辑。
3. **辅助函数迁移** (`core/utils/`) [x]
   - 迁移颜色插值、几何居中等通用静态方法。

### 第二阶段：品牌识别与文字系统 (Visual Identity)
4. **品牌与 Logo 剥离** (`core/branding/`) [x]
   - 迁移镜头勋章正则识别逻辑 (`LensParser`) 及 Logo 路径检索 (`LogoFinder`)。
5. **排版引擎升级** (`core/typography/`) [x]
   - 迁移 CJK 降级逻辑 (`FontResolver`) 与字号自适应缩放逻辑 (`TextAdjuster`)。

### 第三阶段：几何布局与齿孔模式 (Geometry) [x]
6. **布局解算器迁移** (`core/layout/calculator.py`) [x]
   - 迁移 `target_ratio` 补边计算与 side/top/bottom 边距分配逻辑。
7. **齿孔模式模块化** (`core/layout/sprocket.py`) [x]
   - 将齿孔模式下的特殊边距覆盖逻辑独立。

### 第四阶段：特效引擎与主题重构 (Aesthetics) [x]
8. **特效剥离** (`core/effects/`) [x]
   - 迁移 `_apply_pro_shadow`（投影）与 `_apply_matte_texture`（纹理）。
9. **主题渲染器实现** (`core/theme/`) [x]
   - 按照基类接口，将 `Light`, `Dark`, `Frosted`, `SlateTeal` 及各种渐变主题的 `draw` 逻辑搬迁至对应文件。

### 第五阶段：FilmRenderer 深度瘦身 (Integration) [x]
10. **流水线重组与逻辑外迁** (`core/renderer.py`) [x]
    - **10.1 元数据校验下放**: 将 `process_image` 开头的元数据补全逻辑移入 `MetadataHandler`。 [x]
    - **10.2 自适应颜色感知识别**: 将磨砂模式亮度检测移至 `BaseTheme.resolve_adaptive_colors`。 [x]
    - **10.3 物理碰撞检测逻辑**: 将垂直压图提醒逻辑移至 `TextAdjuster`。 [x]
    - **10.4 方法解耦重构**: 将 200 行的长方法拆解为 `_prepare_context`, `_draw_base_layer`, `_apply_typography` 等私有子管线。 [x]
    - **10.5 字符串拼接清理**: 移除 `_prepare_strings` 冗余代码，统一调用 `LensParser` 接口。 [x]

---

### 第六阶段：UI 逻辑解耦与瘦身 (v2.5.0 Target)
11. **BorderPanel 极致瘦身与逻辑对齐** (`gui/panels/border_panel.py`)
    - **11.1 布局计算同源化**: [x] 在 `LayoutCalculator` 中提炼 `preview_ui_paddings`，并替换掉 UI 中的数学公式，实现渲染与预览数学模型 100% 对齐。
    - **11.2 美学预设配置化**: [x] 移除 UI 代码中硬编码的比例参数 (如 1:1, 4:5 预设)，将其抽离至 `assets/config/aesthetic_presets.json`。
    - **11.3 状态管理收口**: [] 将零散的 `StringVar` / `IntVar` 状态管理以及 `_save_current_to_state` 的存取逻辑统一托管给 `BorderController`。
    - **11.4 预览调度解耦**: [] 将 `BorderPanel` 中的多线程管理和 JobID 逻辑移入 Controller，UI 仅作触发与状态监听。

---

## 🚦 验收标准
- [x] 核心渲染效果与原版 1:1 像素级一致（通过 Diff 测试）。
- [x] `core/renderer.py` 代码量显著下降，逻辑清晰。
- [ ] `gui/panels/border_panel.py` 从 1400 行瘦身至 700 行内。
- [x] 模块间耦合度降低，支持单模块单元测试。
- [x] 启动速度与渲染性能无退化。
