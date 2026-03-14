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

## 📷 目前支持的相机列表 (Supported Cameras)

只要你的照片 EXIF 信息中的 **Model (型号)** 包含下表中的关键字，软件就会自动匹配图标。匹配时不区分大小写，且会自动忽略空格和横杠（例如 `GA 645` 也能匹配 `GA645`）。

| 品牌 (Brand) | 支持型号关键字 (Keywords / Filenames) |
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

> **💡 如何添加新 Logo？**
> 1. 准备一张透明背景的 PNG、SVG 或 JPG 图片。
> 2. 将文件命名为 `品牌-型号.png`（例如 `NIKON-Z9.png`）。
> 3. 放入 `logos` 文件夹，重新运行软件。

---

## 🛠️ 稳定性修复 / Stability Improvements
*   修复了切换中英文时偶尔崩溃的问题。
*   修复了在部分高缩放比例屏幕下出现的排版截断问题。
*   优化了 PanedWindow 的初始分栏比例锁定。

---
*Enjoy your film workflow with GT23!* 🎞️✨
