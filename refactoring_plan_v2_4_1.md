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
5. **排版引擎升级** (`core/typography/`)
   - 迁移 CJK 降级逻辑 (`FontResolver`) 与字号自适应缩放逻辑 (`TextAdjuster`)。

### 第三阶段：几何布局与齿孔模式 (Geometry)
6. **布局解算器迁移** (`core/layout/calculator.py`)
   - 迁移 `target_ratio` 补边计算与 side/top/bottom 边距分配逻辑。
7. **齿孔模式模块化** (`core/layout/sprocket.py`)
   - 将齿孔模式下的特殊边距覆盖逻辑独立。

### 第四阶段：特效引擎与主题重构 (Aesthetics)
8. **特效剥离** (`core/effects/`)
   - 迁移 `_apply_pro_shadow`（投影）与 `_apply_matte_texture`（纹理）。
9. **主题渲染器实现** (`core/theme/`)
   - 按照基类接口，将 `Light`, `Dark`, `Frosted`, `SlateTeal` 及各种渐变主题的 `draw` 逻辑搬迁至对应文件。

### 第五阶段：FilmRenderer 瘦身 (Integration)
10. **流水线重组** (`core/renderer.py`)
    - 删减 80% 以上的代码，改为调用上述模块。
    - 确保 `process_image` 仅包含高层逻辑流转。

---

## 🚦 验收标准
- [ ] 核心渲染效果与原版 1:1 像素级一致（通过 Diff 测试）。
- [ ] `core/renderer.py` 代码量显著下降，逻辑清晰。
- [ ] 模块间耦合度降低，支持单模块单元测试。
- [ ] 启动速度与渲染性能无退化。
