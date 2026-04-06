# GT23 Workflow v2.3.1 更新说明 (Release Notes)

---

## ⚡ 预览体验优化 (Preview Optimization)
- **即时反馈 / Instant Feedback**：
  - CN: 由于优化了底层的内存处理机制，现在调整边框参数（如边距、字体大小）时，预览图几乎没有延迟，能做到即点即看。
  - EN: Optimized the underlying memory processing mechanism. Now, adjusting border parameters (margins, font size, etc.) triggers near-instant preview updates.
- **画质对齐 / Rendering Parity**：
  - CN: 修复了预览图和最终导出稿阴影不一致的问题，现在预览时看到的阴影效果就是最终成片的样式。
  - EN: Fixed the shadow inconsistency between the preview and final output. The shadow effect you see in the preview is now bit-for-bit identical to the final exported image.

## 📂 批量处理与排序 (Batch Processing & Ordering)
- **有序命名 / Sequential Naming**：
  - CN: 在“马卡龙”和“彩虹”模式下，导出的文件名会自动加上 `001_`, `002_` 等序号前缀，严格遵循用户在界面中调整后的样片排序。
  - EN: In "Macaron" and "Rainbow" modes, exported filenames now include sequential prefixes (e.g., `001_`, `002_`), strictly following the custom sort order set in the GUI.

## 📦 资源库更新 (Logo Library Update)
- **型号扩容 / Model Expansion**：
  - CN: 同步更新了数十款相机 Logo（总计 200 余款），新增对索尼 A7CII, A7R5, 徕卡 M11-P/D, M10-R, 富士 X-T5 等机型支持。
  - EN: Updated the logo library with dozens of new models (200+ total), including support for Sony A7CII, A7R5, Leica M11-P/D, M10-R, Fujifilm X-T5, etc.
- **自动检测 / Auto-Detection**：
  - CN: 只要您的照片包含 EXIF 信息，现在程序能更精准地自动匹配这些最新热门机型的 Logo。
  - EN: Improved identification accuracy. The program now maps the correct logos automatically for these popular modern camera models based on image EXIF data.
- **交互优化 / UX Optimization**：
  - CN: 手动选择胶片时，在下拉框中选择或输入后按回车，预览图都会自动刷新。
  - EN: Selecting an item from the film dropdown or pressing Enter after manual input now triggers an immediate preview refresh.

## 📸 EXIF 元数据录入 (EXIF Metadata Overrides)
- **原图保留 / Metadata Preservation**：
  - CN: 导出 JPEG 图片现在能完整保留原图的 EXIF 信息（如日期、地理位置等），不再是“白板”文件。
  - EN: Exported JPEG images now preserve full original EXIF metadata (Date, GPS, etc.) instead of being "blank" metadata files.
- **手动覆盖 / Manual Overrides**：
  - CN: 支持通过侧边栏手动改写品牌、型号、镜头、快门、光圈、ISO 等参数，并精准注入到图片底层。
  - EN: Supports manually overriding Make, Model, Lens, Shutter, Aperture, and ISO via the sidebar, with precise injection into the image metadata.
- **全局应用 / Global Sync**：
  - CN: 新增“全局应用”开关。开启后，填写的参数会同步给当前批次内的所有图片，方便批量统一处理。
  - EN: Added an "Apply to All" toggle. When enabled, your manual EXIF overrides are synchronized across all images in the current batch for efficient batch processing.

## 🛠️ 其他修复 (Bug Fixes)
- **列表删除修复 / Deletion Sync Fix**：
  - CN: 修复了在预览条中删除图片后，后台导出列表未同步更新导致依旧会处理已删除图片的 Bug。
  - EN: Fixed a bug where deleting images from the thumbnail strip did not correctly update the background processing list.
- **稳定性修复 / Stability Fix**：
  - CN: 修复了在 Windows 某些环境下程序可能报错及部分线程碰撞导致的启动崩溃问题。
  - EN: Resolved startup crashes and thread-safety issues occurring in certain Windows environments.
- **内存优化 / Memory Efficiency**：
  - CN: 微调了批量导出时的内存分配逻辑，在高强度任务下运行更稳。
  - EN: Refined the memory allocation logic for batch processing, ensuring smoother operation during heavy rendering tasks.
