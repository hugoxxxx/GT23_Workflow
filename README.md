# GT23_Workflow

### [English] | [中文]

A dedicated tool for film photographers to generate **Digital Contact Sheets** and professionally processed film borders. It organizes your scans into professional physical film strip layouts and automatically restores shooting parameters (EXIF) onto the "DataBack".

专为胶片摄影师设计的 **数字接触印样** 与 **底片边框处理** 工具。它能将扫描件排版为专业的底片切片样式，并自动将拍摄参数（EXIF）还原为"数码背印"。

---

## 🔥 What's New — v2.0.0 (GUI Edition)

- **GUI Released | 正式发布 GUI**
   - EN: Brand‑new desktop app built with `tkinter + ttkbootstrap`. Two panels: Border Tool and Contact Sheet, bilingual UI with auto language detection.
   - CN: 基于 `tkinter + ttkbootstrap` 的全新桌面版，提供「边框工具 / 底片索引」两大面板，内置中英双语并自动识别系统语言。

- **MKL Runtime Included | 内置 MKL 运行库**
   - EN: Bundle Intel MKL/OpenMP DLLs from Conda env to resolve "Failed to extract entry: mkl_avx2.2.dll".
   - CN: 自动打包 Conda 环境中的 MKL/OpenMP DLL，修复 “mkl_avx2.2.dll 解包失败”。

- **Dev/Build Streamlined | 开发/打包流程简化**
   - EN: Single Conda env name `gt23`; UTF‑8 batch outputs; safer clean‑build with process unlock.
   - CN: 统一环境名 `gt23`，批处理改为 UTF‑8，打包前自动清理并解锁旧进程。

- **Consistency & Maintainability | 一致性与可维护性**
   - EN: Centralized version in `version.py`; window titles auto‑sync. Dependencies aligned to `ttkbootstrap` (removed unused PySide6).
   - CN: 版本集中到 `version.py` 并自动同步窗口标题；依赖切换为 `ttkbootstrap`（移除未使用的 PySide6）。

Notes | 说明:
- EN: CLI is paused for this release — GUI is the primary distribution.
- CN: 本次发布暂停维护 CLI，主推 GUI 桌面版。

## 📷 About the Name | 项目名称由来

**EN**: The name "GT23" pays homage to two legendary Contax compact cameras that shaped my film photography journey: the **G2** and **T3**. Both were once part of my collection, but circumstances led me to part with them. Since then, their prices have soared far beyond reach, closing the door on any chance of reunion. The memories of shooting with these exceptional cameras remain vivid, and when it came time to name a tool dedicated to film photography, honoring them felt like the only fitting tribute.

**CN**: 项目名称 "GT23" 致敬了影响我胶片摄影之路的两部 Contax 传奇紧凑型相机：**G2** 和 **T3**。它们曾是我的珍藏，但因缘际会最终出手。此后价格飙升，再也难以企及，重逢无望。用这两部杰出相机拍摄的记忆依然鲜活，当我着手开发一款胶片摄影工具时，用它们的名字致敬，是唯一合适的选择。

---

## 🖼️ GUI Preview | 界面预览

<table>
  <tr>
    <td align="center">
      <strong>Border Tool | 边框工具</strong><br>
      <img src="https://github.com/hugoxxxx/photos/blob/9bddc22fa9f3dc0b66f95a9e98f5d20c265c3b06/GT23samples/GUI.png" width="100%" alt="GT23 Border Tool">
    </td>
    <td align="center">
      <strong>Contact Sheet | 底片索引</strong><br>
      <img src="https://github.com/hugoxxxx/photos/blob/9bddc22fa9f3dc0b66f95a9e98f5d20c265c3b06/GT23samples/GUI-2.png" width="100%" alt="GT23 Contact Sheet">
    </td>
  </tr>
</table>

---

## 🚀 Key Features | 核心功能

* **Dual Toolsets | 双重工具集**: 
    * **Border Tool**: Professional cropping, padding, and aesthetic border processing for individual scans. Features real-time preview, auto date selection, EXIF visibility toggle, and customizable border ratio. | **边框美化工具**: 为单张扫描件提供专业的裁剪、填充及边框美化处理。支持实时预览、自动选择日期、EXIF 信息显隐控制、自定义边框比例。
    * **Contact Sheet (135/120)**: Automated index sheet generation with physical film simulation. | **底片索引工具**: 自动化生成具备物理底片质感的索引印样。

* **Dynamic DataBack | 动态背印**:
    * EN: Automatically reads EXIF (Date, Aperture, Shutter, Film stock) for **each individual frame**. Simulated glowing orange LED/Segment font styles. | CN: 自动读取每一帧的 EXIF 信息（日期、光圈、快门、胶片型号）。采用仿真 LED 橙色七段数码管字体。

* **Expanded Film Library | 扩展胶片库**:
    * EN: Now supports a significantly larger film database, covering more film stock variants and brands with accurate EdgeCode and color profiles. | CN: 现已支持更大规模的胶片库，涵盖更多胶片品牌与型号，包含准确的喷码与视觉颜色配置。

* **135 Precision Layout with Smart Sprocket Rendering | 135 精准排版与智能齿孔渲染**:
    * EN: **Optimized sprocket design**: Automatically switches sprocket styles based on film type (ISO 1007 compliant vector rendering). Date placed at inner bottom-right; EXIF centered in outer bottom margin. | CN: **优化的齿孔设计**：根据不同胶片类型自动切换齿孔样式（ISO 1007 标准矢量渲染）。日期位于右下角，EXIF 参数居中显示在下方黑边。
    * **Smart Global Crop**: Automatic vertical cleanup at the right edge to ensure a clean finish. | CN: **智能全局裁切**：自动清理右侧多余黑边，确保视觉整洁。

* **Fixed Frame Count Indicator | 固定张数黑条提示**:
    * EN: The black film leader strip is **always generated** according to film format spec (135: 36 frames, 645: 16 frames, 66: 12 frames, 67: 10 frames), **even if fewer photos are merged**. This serves as a visual reminder of how many frames were wasted or not exposed. | CN: 黑色胶片领导条严格按照胶片规格生成（135：36张、645：16张、66：12张、67：10张），**即使合并的照片数量不足也会完整显示**。这可以直观地提醒摄影师一卷有多少张废片或未曝光的底片。

* **Auto-Rotation**: Intelligent orientation handling for consistent visual flow. | CN: **自动旋转**：智能处理图像方向，确保版面流畅。

---

## 📦 Installation & Usage | 安装与使用

### Option A: GUI Executable (Recommended) | GUI 可执行程序（推荐）

**EN**: Download the latest `.exe` from Releases, place it in a working folder, then double‑click to launch the GUI.

**CN**: 从 Releases 下载最新 `.exe`，放到工作目录后双击运行即可进入 GUI。

Steps | 步骤：
1. Create a working directory | 创建工作目录：

   ```
   MyProject/
   ├── GT23_Workflow.exe
   ├── photos_in/          (Put scanned JPG/PNG here | 放入扫描 JPG/PNG)
   └── photos_out/         (Outputs will appear here | 输出结果在此)
   ```

2. Launch GUI | 启动 GUI：

   - Border Tool tab: single‑scan border processing | 边框工具：单张扫描的边框美化
   - Contact Sheet tab: 135/120 contact sheet rendering | 底片索引：135/120 版式渲染

3. Results | 结果：
   - EN: Processed images are saved into `photos_out/`.
   - CN: 处理图片输出到 `photos_out/`。

---

### Option B: Build From Source | 源码构建（进阶）

**EN**: For developers. Use Conda env `gt23` and run `build_gui.bat`.

**CN**: 面向开发者。使用 Conda 环境 `gt23`，运行 `build_gui.bat` 进行打包。

#### Setup Steps | 设置步骤

1. **Clone the Repository | 克隆代码库**:
   ```bash
   git clone https://github.com/yourusername/GT23_Workflow.git
   cd GT23_Workflow
   ```

2. **Create/Activate env | 创建/激活环境**:
   ```powershell
   conda create -n gt23 python=3.11 -y
   conda activate gt23
   pip install -r requirements-gui.txt
   ```

3. **Build EXE | 打包 EXE**:
   ```powershell
   .\build_gui.bat
   ```

---

## 🗺️ Roadmap | 路线图

- [x] **v1.0 - v1.8**: Basic layout, Dynamic EXIF, Auto‑rotation | 完成基础排版、动态 EXIF、自动旋转
- [x] **v1.9 - v2.0**: Multi‑format (66/645/67/135), film library expansion, sprocket rendering, EXE packaging | 多画幅、胶片库扩展、齿孔渲染、EXE 封包
- [x] **v2.0.0**: Ship GUI desktop app with real-time preview, EXIF/date controls | 正式发布 GUI 桌面版，支持实时预览、EXIF/日期控制
- [ ] **Future**: No further plans at this time | 远期暂无规划

---

## 🖼️ Canvas Size | 画布尺寸

- **English:** The canvas is set to a 10-inch aspect ratio. This specific proportion is chosen because it most closely matches the dimensions of a full roll of film when printed and stored, ensuring a natural and authentic layout.
- **中文:** 画布设定为 10 寸比例。选择这一比例的原因，是因为它最接近完整一卷底片冲洗、收纳后的物理尺寸，能够确保排版呈现出自然且真实的视觉效果。

---

## 🎞️ Supported Film Formats | 支持的胶片格式

| Format | Frames per Roll | Frame Count Display |
|--------|-----------------|-------------------|
| **135** | 36 | Always shows 36-frame leader (EN) / 总是显示 36 格黑条 (CN) |
| **645** | 16 | Always shows 16-frame leader (EN) / 总是显示 16 格黑条 (CN) |
| **66** | 12 | Always shows 12-frame leader (EN) / 总是显示 12 格黑条 (CN) |
| **67** | 10 | Always shows 10-frame leader (EN) / 总是显示 10 格黑条 (CN) |

---

## 📂 Project Structure | 项目结构

```
GT23_Workflow/
├── main.py                      (EN: Entry point | CN: 程序入口)
├── build.spec                   (EN: PyInstaller config | CN: PyInstaller 配置)
├── requirements.txt             (EN: Python dependencies | CN: Python 依赖)
├── README.md                    (This file)
├── apps/
│   ├── border_tool.py           (EN: Single-image border processor | CN: 单图边框处理)
│   └── contact_sheet.py         (EN: Multi-format contact sheet generator | CN: 多格式索引页生成器)
├── core/
│   ├── metadata.py              (EN: EXIF extraction & film matching | CN: EXIF 提取与胶片匹配)
│   ├── renderer.py              (EN: Pro-grade border renderer | CN: 高级边框渲染器)
│   ├── typo_engine.py           (EN: Typography with kerning | CN: 排版与字距调整)
│   └── renderers/               (EN: Format-specific renderers | CN: 画幅特定渲染器)
│       ├── base_renderer.py
│       ├── renderer_135.py      (EN: 135 format with sprockets | CN: 135 格式含齿孔)
│       ├── renderer_645.py      (EN: 645 format dual-mode | CN: 645 格式双模式)
│       ├── renderer_66.py       (EN: 6×6 square format | CN: 6×6 正方形格式)
│       └── renderer_67.py       (EN: 6×7 landscape format | CN: 6×7 横向格式)
├── config/
│   ├── films.json               (EN: Film library with EdgeCode & colors | CN: 胶片库含喷码与颜色)
│   ├── layouts.json             (EN: Film format layout specs | CN: 画幅版式规格)
│   └── contact_layouts.json     (EN: Contact sheet layout config | CN: 索引页版式配置)
├── assets/fonts/                (EN: Typography resources | CN: 排版字体资源)
├── photos_in/                   (EN: Input scanned images | CN: 输入扫描照片)
└── photos_out/                  (EN: Output processed sheets | CN: 输出处理结果)
```

---

## 🎞️ 135 Layout Details | 135 排版细节

* **Date (日期)**: Placed at **Inner Bottom-Right** of each frame. | 位于每帧照片内部的 **右下角**。
* **EXIF (参数)**: Centered in the **Outer Bottom Margin** (under sprockets). | 居中显示在照片下方 **齿孔外的黑边** 中。
* **Clean Edge (全局截断)**: Trailing black strips are automatically wiped to prevent UI artifacts. | 自动清理右侧多余黑边与序号，确保视觉整洁。

---

## 📸 Sample Outputs | 示例输出

### 🎞️ Contact Sheet Examples | 底片索引示例

<table>
<tr>
<td width="50%" align="center">
<b>135 Format</b> (36 frames)<br/>
<img src="https://github.com/hugoxxxx/photos/blob/24e295b82f6a78ca1a877d576b40a4ee5607c1c1/GT23samples/ContactSheet_135.jpg" width="100%" alt="135format">
</td>
<td width="50%" align="center">
<b>66 Format</b> (12 frames)<br/>
<img src="https://github.com/hugoxxxx/photos/blob/24e295b82f6a78ca1a877d576b40a4ee5607c1c1/GT23samples/ContactSheet_66.jpg" width="100%" alt="66format">
</td>
</tr>
<tr>
<td width="50%" align="center">
<b>645 Landscape</b> (16 frames)<br/>
<img src="https://github.com/hugoxxxx/photos/blob/24e295b82f6a78ca1a877d576b40a4ee5607c1c1/GT23samples/ContactSheet_645-L.jpg" width="100%" alt="645format_L">
</td>
<td width="50%" align="center">
<b>645 Portrait</b> (16 frames)<br/>
<img src="https://github.com/hugoxxxx/photos/blob/24e295b82f6a78ca1a877d576b40a4ee5607c1c1/GT23samples/ContactSheet_645-P.jpg" width="100%" alt="645format_P">
</td>
</tr>
<tr>
<td colspan="2" align="center">
<b>67 Format</b> (10 frames)<br/>
<img src="https://github.com/hugoxxxx/photos/blob/24e295b82f6a78ca1a877d576b40a4ee5607c1c1/GT23samples/ContactSheet_67.jpg" width="50%" alt="67format">
</td>
</tr>
</table>

### 🔍 Detail Examples | 细节示例

<table>
<tr>
<td width="50%" align="center">
<b>135 Movie Perforation | 电影卷齿孔</b><br/>
<img src="https://github.com/hugoxxxx/photos/blob/24e295b82f6a78ca1a877d576b40a4ee5607c1c1/GT23samples/%E5%BE%AE%E4%BF%A1%E5%9B%BE%E7%89%87_20260117185247_87_68.png" width="100%" alt="135_movie_perforation">
</td>
<td width="50%" align="center">
<b>135 Standard Perforation | 标准齿孔</b><br/>
<img src="https://github.com/hugoxxxx/photos/blob/24e295b82f6a78ca1a877d576b40a4ee5607c1c1/GT23samples/%E5%BE%AE%E4%BF%A1%E5%9B%BE%E7%89%87_20260117185339_88_68.png" width="100%" alt="135_standard_perforation">
</td>
</tr>
<tr>
<td colspan="2" align="center">
<b>66 Border Example | 66 边框示例</b><br/>
<img src="https://github.com/hugoxxxx/photos/blob/858c3dbadff82bcf6ece7de72a15c25d25f93746/GT23samples/GT23_66.png" width="50%" alt="66_border">
</td>
</tr>
</table>

---

## 🛠️ Troubleshooting | 故障排除

**EXE runs but says "No images found" | EXE 运行但提示"没有找到图片"**:
* EN: Make sure you created `photos_in/` folder next to the EXE, and placed JPG/PNG files inside it.
* CN: 确保在 EXE 同级目录创建了 `photos_in/` 文件夹，并放入 JPG/PNG 文件。

**Film not recognized | 胶片无法识别**:
* EN: The tool will prompt you to enter the film name manually. Type the film name or abbreviation (e.g., `Portra 400`, `Fuji Pro`, `HP5`).
* CN: 工具会提示你手动输入胶片名称。输入胶片名称或简称（如 `Portra 400`、`Fuji Pro`、`HP5`）。

**Permission denied when running | 运行时出现权限拒绝**:
* EN: On macOS/Linux, you may need to make the script executable: `chmod +x main.py`
* CN: 在 macOS/Linux 上，可能需要使脚本可执行：`chmod +x main.py`

---

## 📧 Support | 技术支持

EN: If you encounter issues, please contact: **xjames007@gmail.com**

CN: 遇到问题请联系：**xjames007@gmail.com**

---

## 📝 License | 许可证

MIT License - See LICENSE file for details. | MIT 许可证 - 详见 LICENSE 文件。

---

## 🙏 Credits | 致谢

EN: Thanks to all film photographers who provided feedback and inspiration for this tool.

CN: 感谢所有胶片摄影师提供的反馈和灵感。
```