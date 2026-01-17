# GT23_Workflow

### [English] | [中文]

A dedicated tool for film photographers to generate **Digital Contact Sheets** and professionally processed film borders. It organizes your scans into professional physical film strip layouts and automatically restores shooting parameters (EXIF) onto the "DataBack".

专为胶片摄影师设计的 **数字接触印样** 与 **底片边框处理** 工具。它能将扫描件排版为专业的底片切片样式，并自动将拍摄参数（EXIF）还原为"数码背印"。

---

## 🚀 Key Features | 核心功能

* **Dual Toolsets | 双重工具集**: 
    * **Border Tool**: Professional cropping, padding, and aesthetic border processing for individual scans. | **边框美化工具**: 为单张扫描件提供专业的裁剪、填充及边框美化处理。
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

### Option A: Executable (EXE) - No Python Required | 可执行程序版本（无需 Python）

**EN**: Download the latest `.exe` from **Releases** and follow the setup below.

**CN**: 从 **Releases** 下载最新的 `.exe` 文件，按照以下步骤操作。

#### Setup Steps | 设置步骤

1. **Create a working directory | 创建工作目录**:

   ```
   MyProject/
   ├── GT23_Workflow.exe
   ├── photos_in/          (EN: Place your scanned JPG/PNG files here | CN: 在此放入扫描的 JPG/PNG 照片)
   └── photos_out/         (EN: Output results will appear here | CN: 输出结果将出现在此)
   ```

   * EN: Create a folder (e.g., `C:\GT23\`) to hold the EXE and film scans.
   * CN: 创建一个工作文件夹（例如 `C:\GT23\`），放置 EXE 文件和胶片扫描件。

2. **Prepare your photos | 准备照片**:
   * EN: Copy all scanned film images into the `photos_in/` folder.
   * CN: 将所有扫描的胶片照片复制到 `photos_in/` 文件夹中。

3. **Run the EXE | 运行程序**:
   ```powershell
   .\GT23_Workflow.exe
   ```

4. **Follow the menu prompts | 按照菜单提示操作**:
   * EN: A menu will appear. Select `[1]` for **Border Tool** or `[2]` for **Contact Sheet**.
   * CN: 会出现菜单，选择 `[1]` 进入**边框工具**，或 `[2]` 进入**底片索引工具**。

5. **Enter film information | 输入胶片信息**:
   * EN: When prompted, enter the film name, emulsion number, and other parameters.
   * CN: 按提示输入胶片名称、乳剂号等参数。

6. **Check results | 查看结果**:
   * EN: Output images will be saved in the `photos_out/` folder.
   * CN: 处理后的图像将保存到 `photos_out/` 文件夹。

---

### Option B: Python - For Advanced Users | Python 版本（适合高级用户）

**EN**: This option requires Python 3.x and manual installation of dependencies. Recommended for developers who want source code access or need to run on unsupported systems.

**CN**: 此选项需要 Python 3.x 并手动安装依赖项。适合需要源代码访问权或在不支持的系统上运行的开发者。

#### Setup Steps | 设置步骤

1. **Install Python 3.x | 安装 Python 3.x**:
   * EN: Download and install Python from [python.org](https://www.python.org/). Ensure `python` and `pip` are added to your system PATH.
   * CN: 从 [python.org](https://www.python.org/) 下载并安装 Python。确保 `python` 和 `pip` 已添加到系统 PATH。

2. **Clone the Repository | 克隆代码库**:
   ```bash
   git clone https://github.com/yourusername/GT23_Workflow.git
   cd GT23_Workflow
   ```

3. **Install Dependencies | 安装依赖项**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Tool | 运行工具**:
   ```bash
   python main.py
   ```

5. **Follow On-Screen Instructions | 按照屏幕上的说明操作**:
   * EN: Choose `[1]` for Border Tool or `[2]` for Contact Sheet. Have your film scans and desired output settings ready.
   * CN: 从菜单中选择 `[1]` 进入边框工具或 `[2]` 进入底片索引工具。准备好你的胶片扫描件和期望的输出设置。

---

## 🗺️ Roadmap | 路线图

- [x] **v1.0 - v1.8**: Basic layout, Dynamic EXIF, and Auto-rotation. | 完成基础排版、动态 EXIF 及自动旋转。
- [x] **v1.9 - v2.0**: Full multi-format support (66, 645, 67, 135), expanded film library, optimized sprocket rendering, and EXE packaging. | **已完成：多画幅支持、扩展胶片库、齿孔优化、EXE 封包。**
- [ ] **v2.1 (Next)**: Advanced batch editing, custom layout templates. | **即将推出：高级批量编辑、自定义版式模板。**
- [ ] **v3.0**: **GUI Interface**. | **长期规划：开发图形界面。**

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