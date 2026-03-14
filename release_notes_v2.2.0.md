# GT23 Film Workflow v2.2.0 Release Notes

## 🏮 新版本特性 / What's New

### 1. “一页全览”：更直观的交互体验 / One-Page Experience: Intuitive Interaction
我们彻底重构了 GUI 布局。通过将控制侧边栏拓宽至 **750 像素** 并引入 **全网格布局**，现在 90% 的场景下你都可以在一个画面内看全所有设置项。
*   **EN:** Completely overhauled the GUI layout. By widening the sidebar to **750px** and introducing a **full-grid layout**, you can now see all settings in one frame without scrolling.
*   **EN:** Default window height increased to **1100px** to ensure core buttons are always visible.
*   **CN:** 核心功能区域全面采用分列排布，窗口高度默认提升至 **1100 像素**，实现了“一眼全览，无需滚动”的目标。

### 2. 无限可能：外置 Logo 管理 / Infinite Possibilities: External Logo Management
终于，你可以无需找我改代码就能添加自己的相机 Logo 了。
*   **EN:** Finally, you can add your own camera logos without touching a single line of code.
*   **EN:** **External Folder:** The app now automatically generates a `logos` folder next to the EXE.
*   **EN:** **Plug & Play:** Just drag your new logos (JPG/PNG/SVG) into the folder and restart. Default logos are automatically protected and extracted on first run.
*   **CN:** **外置文件夹**：软件会在 EXE 同级目录下自动生成 `logos` 文件夹。
*   **CN:** **即加即用**：只需将新图标拖进去并重启即可。默认图标会在首次运行时自动释放。

---

## ⌨️ 标签对应与匹配指南 / EXIF & Label Mapping Guide

为了让图标识别更精准，请参考下表进行手动输入或 EXIF 检查：
*   **EN:** Refer to the table below for precise logo matching and EXIF verification:

| 界面标签 (UI Label) | 手动输入示例 (Manual Input) | 自动读取 EXIF (Auto-EXIF) | 说明 (Notes) |
| :--- | :--- | :--- | :--- |
| **Make** | CONTAX, FUJIFILM | `Make` | 品牌名，匹配时的次级关键字 (Brand keyword) |
| **Model** | **G2**, **T3**, **GA645** | `Model` | **核心关键字**，匹配图标主要靠它 (Core matching key) |
| **Shutter** | 1/125, 1s | `ExposureTime` | 快门速度，自动补全 "s" (Shutter speed) |
| **Aperture** | 2.8, 8, 16 | `FNumber` | 光圈值，自动补全 "f/" (Aperture value) |
| **ISO** | 100, 400, 800 | `ISOSpeedRatings` | 感光度 (Sensitivity) |
| **Lens** | Planar 45mm f/2 | `LensModel` | 镜头完整型号 (Full lens model) |

> **💡 重要提示 / Important Tips:**
> - **Logo Matching**: 软件会基于 `Model` 进行模糊匹配。你可以填 `CONTAX` + `G2`，也可以直接在 `Model` 填 `CONTAX G2`。
> - **EN:** The software performs fuzzy matching based on the `Model` tag.
> - **Manual Override**: 只要你在界面填了内容，软件就会**忽略**原图 EXIF，优先使用你的输入。
> - **EN:** Manual input always takes precedence over embedded EXIF data.

---

## 📷 目前支持的默认图标 / Default Supported Logos

![Logo Full Map](assets/LOGO_FULL_MAP.jpg)
*Updated: 49 supported cameras with 18% Grey Neutral Reference.*

只要 `Model` 或 `Make` 包含以下关键字，即可自动显示官方图标：
*   **EN:** Icons are automatically displayed if `Model` or `Make` tags include the following keywords:

| 品牌 (Brand) | 支持型号关键字 (Keywords) |
| :--- | :--- |
| **CONTAX** | G1, G2, T, T2, T3, TVS, TVS II, TVS III |
| **CANON** | A-1, AE-1, R1, R3, R5 II, R6 II, R6 III |
| **FUJIFILM** | GA645, GA645i, GA645wi, GF670, GS645, GS645S, GS645W |
| **MAMIYA** | 645AFD, 645E, 645PRO, 645PROTL, 645SUPER, 6MF, 7II, C330, RB67PROS, RB67PROSD, RZ67, RZ67PROIID |
| **PENTAX** | 67, 67ii, 6X7 |
| **BRONICA** | EC, ETRS, ETRSi, GS-1 |
| **MINOLTA** | TC-1, X700 |
| **ROLLEI** | 35, 35S, 35T, 35QZ |
| **HASSELBLAD** | 500CM |
| **KODAK** | RETINA II |

---

> **🛠️ 进阶：如何添加自己的 Logo？ / Pro: How to Add Custom Logos?**
> 1. 将文件命名为 `品牌-型号.png`（如 `LEICA-M6.png`）。(Name file as `BRAND-MODEL.png`)
> 2. 放入 EXE 目录下的 `logos` 文件夹。(Place in the `logos` folder next to EXE)
> 3. 重启软件，手动在 **Model** 填入 `M6` 即可！(Restart and type `M6` in Model field)

---

## �️ 稳定性修复 / Stability & Performance
*   **EN:** Fixed occasional crashes during language switching (CN/EN).
*   **CN:** 修复了切换中英文时偶尔崩溃的问题。
*   **EN:** Resolved layout clipping issues on High-DPI displays with Windows scaling.
*   **CN:** 修复了在部分高缩放比例屏幕下出现的排版截断问题。
*   **EN:** Optimized PanedWindow ratio locking for a consistent UI state.
*   **CN:** 优化了分栏比例锁定，确保界面状态始终整洁如一。

---
*Enjoy your film workflow with GT23!* 🎞️✨
