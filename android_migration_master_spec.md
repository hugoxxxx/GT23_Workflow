# GT23 Workflow: Android 移植全模块终极规范 (Master Migration Spec)

> **[CN] 致新环境 Agent/开发者：** 本文档是专为 GT23 从 Python/Desktop 迁移至 Android/Kotlin 而设计的“全合一”技术蓝图。它合并了存储架构、模块映射及所有渲染算法。
> **[EN] To New Agent/Developer:** This is the "All-in-One" technical blueprint for migrating GT23 from Python/Desktop to Android/Kotlin. It consolidates storage architecture, module mapping, and all rendering algorithms.

---

## 1. 核心架构与模块映射 (Architecture & Module Mapping)

### 1.1 项目入口与生命周期 (App Entry)
| 组件 (Component) | 桌面版 (Desktop - `main.py`) | Android 版 (Kotlin/Compose) |
| :--- | :--- | :--- |
| **入口 (Entry)** | `main()` + `ttk.Window` | `MainActivity` + `Jetpack Compose` |
| **异步/并发** | `threading` | `Kotlin Coroutines` + `ViewModel` |
| **语言切换** | `detect_system_language()` | `res/values/strings.xml` |

### 1.2 核心模块逻辑 (Core Logic)
- **元数据处理器 (`core/metadata.py`)**: 
    - 需切换至 `androidx.exifinterface:exifinterface`。
    - 必须移植 `sorted_features` 算法：按字符长度**倒序**匹配（如 "PORTRA 400" 优于 "PORTRA"）。
- **底片配置 (`config/`)**:
    - 将 `films.json` 与 `layouts.json` 放入 `assets/config/`，使用 `Moshi` 或 `Kotlin Serialization` 解析。

---

## 2. 安卓存储架构与资源管理 (Storage & Assets)

### 2.1 资源分区管理 (Scoped Storage)
| 资产类型 | 存放路径 (Android Path) | 读取方式 |
| :--- | :--- | :--- |
| **内置 Logo/字体** | `src/main/assets/` | `AssetManager` |
| **用户自定义 Logo** | `context.filesDir/custom_logos` | 直接文件流读取 (无需权限) |
| **中间缓存/临时图** | `context.cacheDir` | 自动清理空间 |

### 2.2 成片持久化 (Saving Output)
**[IMPORTANT]** 必须使用 `MediaStore` API 确保照片能进入系统相册：
- **路径**: `Pictures/GT23_Workflow/` 或 `DCIM/GT23_Workflow/`
- **操作**: 通过 `ContentResolver` 执行 `insert` 操作并获取输出流。

---

## 3. 渲染引擎算法深挖 (Rendering Algorithms - "Secret Sauce")

### 3.1 135 画幅物理模拟 (`renderer_135.py`)
- **齿孔路径 (Sprockets)**: 核心算法是手绘 `android.graphics.Path`。
    - **电影卷 (Motion)**: 使用“圆弧侧缘”路径。
    - **标准卷 (Standard)**: 使用 `drawRoundRect`。
- **物理比例**: 依据 ISO 1007 标准。
    - 计算公式：`px_per_mm = (CanvasWidth - 2 * Margin) / Total_MM_Length`。

### 3.2 120 系列 (645, 66, 67) 画幅
- **不稳定性模拟**: 移植 `random.randint` 逻辑，在喷码位置加入 0~100px 的向下抖动，还原工业连喷感。
- **6x7 特殊版式**: 渲染循环需手动控制：Row 1-2 (4帧), Row 3 (2帧)。
- **余白裁剪**: 在每一列渲染结束后，强制用背景色 (`#EBEBEB`) 覆盖剩余区域直至底边。

---

## 4. 排版与视觉对齐 (Typography & Visuals)

- **视觉中心校准 (`core/typo_engine.py`)**: 
    - 弃用基于 Advance 的字符间距，改用 `Paint.getTextBounds()` 获取矩形。
    - 计算公式：`TargetCenterY - (TextHeight / 2) - TextTopOffset`，确保 Logo 与文字物理对齐。
- **特殊字体预设**: 
    - `Segment.ttf` (数码管风格), `LED Dot-Matrix.ttf` (喷码风格) 必须作为 App 资源加载。
    - 默认主副标题映射比例：**1 : 0.78**。

---

## 5. 关键全局参数对照表 (Global Constants)

| 参数 (Param) | 默认值 (Value) | 逻辑含义 (Meaning) |
| :--- | :--- | :--- |
| `side_edge_ratio` | 0.04 (4%) | 胶片左右预留黑边比例 |
| `bottom_ratio` | 0.13 (13%) | 边框底部操作区比例 |
| `shadow_radius` | 3.0 ~ 5.0 | 立体预览时的阴影模糊半径 |
| `marking_color` | `#F58223` | 经典橙色喷码颜色 |

---
**[CN] 提示:** 老大要求：所有输出必须中英双语。在 Android 端渲染时，请注意 `Bitmap` 的内存管理，建议开启 `inBitmap` 复用。
**[EN] Tip:** "Boss" (USER) requires: All output must be bilingual. When rendering on Android, pay attention to `Bitmap` memory management; reuse via `inBitmap` is recommended.
