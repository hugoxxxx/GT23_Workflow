# GT23 Film Workflow v2.2.3 Release Notes

## 🎞️ 功能更新 / Functional Updates

### 1. 配置全解耦：开放参数自定义 / Config Decoupling
现在程序实现了配置文件的“外挂化”，赋予用户更高的自由度。
Externalized configuration files to provide users with greater flexibility.
- **自动释放 / Auto-Bootstrap**: 首次运行会自动将 `layouts.json` 和 `films.json` 释放至 `GT23_Assets/config/`。
- **用户编辑优先 / User-Edit Priority**: 程序优先读取外部 JSON 文件。您可以直接修改边框比例或新增胶片型号。
(External JSON files are prioritized. You can now modify border ratios or add film models without re-compiling.)

### 2. 2026 图标更新 / 2026 Brand Icon
- **视觉焕新 / Visual Refresh**: 集成了高清 2026 版 GT23 图标（assets/GT23_Icon.png）。
- **多尺寸支持 / Multi-Size Support**: 为 Windows 同步更新了多尺寸 `.ico` 资源，确保各个比例下的显示清晰。
(Integrated high-resolution logic and professional multi-size .ico for sharp rendering across all scales.)

### 3. 多项细节优化 / Refined Experience
- **手动胶卷名锁定 / Manual Film Name Preservation**: 手动输入的胶卷型号将不再被数据库标准名覆盖。
(Manual film inputs are strictly preserved and no longer overwritten by database matching.)
- **135 乳剂号展示 / 135 Emulsion Display**: 修复了 135 画幅渲染时乳剂号被隐藏的问题。
(Resolved a bug where emulsion numbers were hidden in 135 format renders.)
- **图片排序增强 / Image Sorting**: 索引页工具新增“文件名”与“拍摄时间”排序及倒序功能。
(Added filename and EXIF date sorting for contact sheets, including a reverse toggle.)

---

## 🛡️ 稳定性增强 / Stability Improvements

### 4. 底层同步重构 / Robust Sync Engine
针对特定环境下的同步失效问题，我们进行了深度加固：
Deeply reinforced the sync engine to resolve failure issues in specific network environments.
- **API Token**: 绕过 Gitee 网页端的验证码拦截，提高下载稳定性。
(By-passes Gitee web verification to improve download reliability.)
- **物理文件校验 / Physical File Audit**: 即便 Hash 匹配，若本地文件夹为空也将强制重新下载。
(Ensures assets are present; a forced re-download is triggered if the local folder is empty despite a hash match.)

### 5. 界面布局修正 / UI Polish
- **等宽格栅布局 / Uniform Grid**: 重构了高级设置面板，解决了多语言标签挤压与对齐不准的问题。
(Refactored Advanced Settings for better alignment and readability across all languages.)

---
*Enjoy your film workflow with GT23 V2.2.3!*
*Robust. Open. Professional.*
