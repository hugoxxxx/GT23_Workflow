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

- [x] **v1.0 - v1.8**: Basic layout, Dynamic EXIF, and Auto-rotation. | 完成基础排版、动态 EXIF 及自动旋转。
- [x] **135 to 67 Coverage**: Full contact sheet support for all formats. | **已完成：索引工具支持 135 到 67 全画幅覆盖。**
- [ ] **Border Tool Aesthetic**: Fine-tuning layout for 645/67 (66 is currently optimized). | **进行中：优化 645/67 边框审美（目前 66 画幅已调优）。**
- [ ] **v1.9 (Next)**: **Executable Packaging (EXE)**. | **下一步：完成程序封包 (EXE)。**
- [ ] **v2.0**: **GUI Interface**. | 开发图形界面版本。

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

### 🖼️ Canvas Size / 画布尺寸

- **English:** The canvas is set to a 10-inch aspect ratio. This specific proportion is chosen because it most closely matches the dimensions of a full roll of film when printed and stored, ensuring a natural and authentic layout.
- **中文:** 画布设定为 10 寸比例。选择这一比例的原因，是因为它最接近完整一卷底片冲洗、收纳后的物理尺寸，能够确保排版呈现出自然且真实的视觉效果。

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

---

## 📸 Samples | 示例
### 135format
<!-- 居中显示并限制宽度 -->
<p align="center">
  <img src="https://private-user-images.githubusercontent.com/18653086/536665968-5248b9de-018d-4a4f-91d2-235e8aa0042e.jpg?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3Njg1NjA3NTYsIm5iZiI6MTc2ODU2MDQ1NiwicGF0aCI6Ii8xODY1MzA4Ni81MzY2NjU5NjgtNTI0OGI5ZGUtMDE4ZC00YTRmLTkxZDItMjM1ZThhYTAwNDJlLmpwZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAxMTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMTE2VDEwNDczNlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTU5OTE2MTZhZWZiNGE1YjQ0MWM2NDY3NWM4MzY4ZWY1N2Q4N2JhMGU2YmQwOGJlZWFiYjM1MTA4MzQxOWY1ODEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.xttdj3aZ2jkRJ_ClbJousnW2lS2s5O6HtFvOqtzOClg" width="400" alt="135format">
</p>

### 66format
<!-- 居中显示并限制宽度 -->
<p align="center">
  <img src="https://private-user-images.githubusercontent.com/18653086/536665969-eb9763e9-897b-4178-b849-d610e587c646.jpg?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3Njg1NjA3NTYsIm5iZiI6MTc2ODU2MDQ1NiwicGF0aCI6Ii8xODY1MzA4Ni81MzY2NjU5NjktZWI5NzYzZTktODk3Yi00MTc4LWI4NDktZDYxMGU1ODdjNjQ2LmpwZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAxMTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMTE2VDEwNDczNlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTEwYWMwYTgyYzEzMjlhZTEwMGYxNTM5MGMwZTFmMGJlYWI3MWUyOWRiMDI3Y2ZiNTU5NGMyNzc5YTFmMWY5ZTAmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.wTUND4PG7YpWg2mOMKOf5zBfhbIyfK5w8SUiT2wbEcI" width="400" alt="66format">
</p>

### 645format_landscape
<!-- 居中显示并限制宽度 -->
<p align="center">
  <img src="https://private-user-images.githubusercontent.com/18653086/536666170-30a2bb16-de7d-45da-8514-06d920602ac7.jpg?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3Njg1NjA3NTYsIm5iZiI6MTc2ODU2MDQ1NiwicGF0aCI6Ii8xODY1MzA4Ni81MzY2NjYxNzAtMzBhMmJiMTYtZGU3ZC00NWRhLTg1MTQtMDZkOTIwNjAyYWM3LmpwZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAxMTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMTE2VDEwNDczNlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWY2MzZiYTVmZjkwOTJmMTVlZTAzZGMzNmI3MTVkOGU2YzNiZDUzMDY5N2E2ZTEwNjc0NjhkMGIwY2M5ZGQ3YmYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.c3jTVffoZ21aPJyOhGKa0bkeKI7vwxZGGFIcjwheHdI" width="400" alt="645format_L">
</p>

### 645format_portrait
<!-- 居中显示并限制宽度 -->
<p align="center">
  <img src="https://private-user-images.githubusercontent.com/18653086/536666171-56946997-0736-47ad-a838-2fabf6affcf5.jpg?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3Njg1NjA3NTYsIm5iZiI6MTc2ODU2MDQ1NiwicGF0aCI6Ii8xODY1MzA4Ni81MzY2NjYxNzEtNTY5NDY5OTctMDczNi00N2FkLWE4MzgtMmZhYmY2YWZmY2Y1LmpwZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAxMTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMTE2VDEwNDczNlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWExNWEyZDU2OGYxM2YxM2JhNmRkNDJhNWUyZTNmYmU5NThmZTkxNzllMWU3ZTMzZjVmOTIxODc3ODk1NjYwMjQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.faqRnHn8Wv47Y73KL3ZJ40opxRKrt_tJ7pnhOLYUI_w" width="400" alt="645format_P">
</p>

### 67format
<!-- 居中显示并限制宽度 -->
<p align="center">
  <img src="https://private-user-images.githubusercontent.com/18653086/536665967-c42c4076-21a5-4045-a928-635bf34b4fd4.jpg?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3Njg1NjA3NTYsIm5iZiI6MTc2ODU2MDQ1NiwicGF0aCI6Ii8xODY1MzA4Ni81MzY2NjU5NjctYzQyYzQwNzYtMjFhNS00MDQ1LWE5MjgtNjM1YmYzNGI0ZmQ0LmpwZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAxMTYlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMTE2VDEwNDczNlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTg3YmRjMDk3Y2U3MDk1ZWMzODgyZjQxZGM5NGI5ZjQyOTZlNmExMWZlNzVhOTQ2ZTZmM2FiYmVlOTAzZWE4YWQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.meTZORQ-sChjm5YOgjoAy6_Ow-BSTY_tTe65WnDTdGQ" width="400" alt="67format">
</p>

