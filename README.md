# GT23_Workflow

### [English] | [中文]

A dedicated tool for film photographers to generate **Digital Contact Sheets** and professionally processed film borders. It organizes your scans into professional physical film strip layouts and automatically restores shooting parameters (EXIF) onto the "DataBack".

专为胶片摄影师设计的 **数字接触印样** 与 **底片边框处理** 工具。它能将扫描件排版为专业的底片切片样式，并自动将拍摄参数（EXIF）还原为“数码背印”。

---

## 🚀 Key Features | 核心功能

* **Dual Toolsets | 双重工具集**: 
    * **Border Tool**: Professional cropping, padding, and aesthetic border processing for individual scans. | **边框美化工具**: 为单张扫描件提供专业的裁剪、填充及边框美化处理。
    * **Contact Sheet (135/120)**: Automated index sheet generation with physical film simulation. | **底片索引工具**: 自动化生成具备物理底片质感的索引印样。
* **Dynamic DataBack | 动态背印**:
    * Automatically reads EXIF (Date, Aperture, Shutter, Film stock) for **each individual frame**.
    * Simulated glowing orange LED/Segment font styles.
* **135 Precision Layout | 135 精准排版**:
    * **v9.2 Update**: Date at inner bottom-right; EXIF centered in the bottom black margin (below sprockets).
    * **Smart Global Crop**: Automatic vertical cleanup at the right edge to ensure a clean finish.
* **Auto-Rotation**: Intelligent orientation handling for consistent visual flow.

---

## 🗺️ Roadmap | 路线图

- [x] **v1.0 **: Basic layout, Dynamic EXIF, and Auto-rotation. | 完成基础排版、动态 EXIF 及自动旋转功能。
- [x] **Integrated Toolsets**: Both Border Tool and Contact Sheet are fully operational via CLI. | **已完成：双工具链集成，支持命令行菜单切换。**
- [ ] **v1.8 (Current)**: Current goal: Improve the aesthetics of border tools for different image sizes. | **当前目标：完善不同画幅边框工具审美。**
- [ ] **v2.0**: Executable Packaging (EXE). | 完成程序封包 (EXE)，实现开箱即用。
- [ ] **v2.1**: GUI version for non-technical users. | 开发图形界面版本，彻底告别命令行。

---

## 🛠️ Quick Start | 快速开始

1.  **Dependencies | 安装依赖**:
    ```bash
    pip install Pillow exifread
    ```
2.  **Run | 运行**:
    ```bash
    python main.py
    ```
    *Choose `[1]` for Border Tool or `[2]` for Contact Sheet from the menu.* | *从菜单中选择 `[1]` 进入边框工具，或 `[2]` 进入底片索引工具。*

---

## 🎞️ 135 Layout Details | 135 排版细节

* **Date (日期)**: Placed at **Inner Bottom-Right** of each frame. | 位于每帧照片内部的 **右下角**。
* **EXIF (参数)**: Centered in the **Outer Bottom Margin** (under sprockets). | 居中显示在照片下方 **齿孔外的黑边** 中。
* **Clean Edge (全局截断)**: Trailing black strips are automatically wiped to prevent UI artifacts. | 自动清理右侧多余黑边与序号，确保视觉整洁。

---

## 📂 Project Structure | 项目结构

* `/apps/`: High-level tool implementations (`border_tool.py`, `contact_sheet.py`).
* `/core/renderers/`: Core rendering logic for various formats.
* `/assets/fonts/`: Dot-matrix and digital segment fonts.
* `main.py`: The unified entry point.

