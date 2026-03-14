# GT23 Film Workflow v2.2.0 Release Notes

## 🏮 新版本特性 / What's New

### 1. “一页全览”：更直观的交互体验 (One-Page Experience)
我们彻底重构了 GUI 布局。通过将控制侧边栏拓宽至 **750 像素** 并引入 **全网格布局**，现在 90% 的场景下你都可以在一个画面内看全所有设置项，不再需要频繁上下滚动寻找“开始处理”按钮。
*   窗口高度默认提升至 **1100 像素**。
*   “高级设置”与“EXIF 覆盖”全面采用双列排布。

### 2. 只有 47 个图标？现在你可以加到 470 个！(External Logos)
终于，你可以无需找我改代码就能添加自己的相机 Logo 了。
*   **外置文件夹**：软件会在 EXE 同级目录下生成一个 `logos` 文件夹。
*   **即加即用**：只需将新图标（JPG/PNG/SVG）拖进去，重启软件即可识别。
*   **自动保护**：默认图标会在首次运行时自动释放。

---

---

## ⌨️ 标签对应与匹配指南 (EXIF & Label Mapping)

为了让图标识别更精准，或者手动覆盖信息，请参考下表：

| 界面标签 (UI Label) | 手动输入示例 (Manual Input) | 自动读取 EXIF (Auto-EXIF) | 说明 (Notes) |
| :--- | :--- | :--- | :--- |
| **Make** | CONTAX, FUJIFILM | `Make` | 品牌名，匹配时作为次级关键字 |
| **Model** | **G2**, **T3**, **GA645** | `Model` | **核心关键字**，匹配图标主要靠它 |
| **Shutter** | 1/125, 1s | `ExposureTime` | 快门速度，软件会自动补全 "s" |
| **Aperture** | 2.8, 8, 16 | `FNumber` | 光圈值，软件会自动补全 "f/" |
| **ISO** | 100, 400, 800 | `ISOSpeedRatings` | 感光度，数码模式下非常有用 |
| **Lens** | Planar 45mm f/2 | `LensModel` | 镜头完整型号，装饰文字的主要部分 |

> **💡 重要提示 (Tips):**
> - **Logo 匹配逻辑**：软件会基于 `Model` 进行模糊匹配。你可以填 `CONTAX` + `G2`，也可以直接在 `Model` 填 `CONTAX G2`。
> - **手动覆盖**：只要你在界面上的输入框填了内容，软件就会**忽略**原图的 EXIF 数据，改用你的输入。

---

## 📷 目前支持的默认图标 (Default Supported Logos)

只要 `Model` 包含以下关键字，即可自动显示官方图标：

| 品牌 (Brand) | 支持型号关键字 (Keywords) |
| :--- | :--- |
| **CONTAX** | G1, G2, T, T2, T3, TVS, TVS II, TVS III |
| **CANON** | A-1, AE-1, R1, R3, R5 II, R6 II, R6 III |
| **FUJIFILM** | GA645, GA645i, GA645wi, GF670, GS645, GS645S, GS645W |
| **MAMIYA** | 645AFD, 645E, 645PRO, 645PROTL, 645SUPER, 6MF, 7II, C330, RB67PROS, RB67PROSD, RZ67, RZ67PROIID |
| **PENTAX** | 67, 67ii, 6X7 |
| **BRONICA** | EC, ETRS, ETRSi, GS-1 |
| **MINOLTA** | TC-1, X700 |
| **ROLLEI** | 35, 35QZ |
| **HASSELBLAD** | 500CM |
| **KODAK** | RETINA II |

---

> **� 进阶：如何添加自己的 Logo？**
> 1. 将文件命名为 `品牌-型号.png`（如 `LEICA-M6.png`）。
> 2. 放入 EXE 目录下的 `logos` 文件夹。
> 3. 重启软件，手动在 **Model** 填入 `M6` 即可！

---

## 🛠️ 稳定性修复 / Stability Improvements
*   修复了切换中英文时偶尔崩溃的问题。
*   修复了在部分高缩放比例屏幕下出现的排版截断问题。
*   优化了 PanedWindow 的初始分栏比例锁定。

---
*Enjoy your film workflow with GT23!* 🎞️✨
