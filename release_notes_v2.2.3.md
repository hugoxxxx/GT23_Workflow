# GT23 Film Workflow v2.2.3 Release Notes (Robust & Open)

## 🛡️ 强力同步与配置开放 / Robust Sync & Open Config

### 1. 强力多源同步：彻底告别“空包” / Robust Multi-Source Sync
针对部分网络环境下“显示同步成功但文件夹为空”的问题，我们进行了底层重构。
*   **Gitee Token 绕过**: 引入 API Token 机制，彻底绕过 Gitee 网页下载时的验证码拦截。
*   **物理文件校验**: 增加“资产存在性”物理检测。即便云端 Hash 匹配，若本地 `logos` 文件夹为空，也将强制触发重新下载，确保资源万无一失。
*   **智能路径识别**: 优化了对 Gitee/GitHub 压缩包根目录的自动搜索，适配各种下载源的层级差异。

### 2. 配置文件全解耦：参数自由修改 / Config Decoupling
为了让资深用户和 EXE 用户能更灵活地调整参数，我们实现了配置文件的“外挂化”。
*   **自动释放 (Bootstrap)**: 首次运行程序时，会自动将内置的布局、胶片、索引页配置释放到 `GT23_Assets/config/` 目录。
*   **用户编辑优先**: 现在程序会优先读取 `GT23_Assets/config/` 下的外部 JSON 文件。您可以直接修改边框比例 (`layouts.json`) 或新增胶片型号 (`films.json`)，重启即可生效。

---

## 🎞️ 细节打磨：体验更专业 / Refined Experience

### 3. 手动胶卷名称锁定 / Manual Film Name Preservation
*   **EN:** Fixed an issue where manual film inputs were overwritten by standard database names; manual strings are now strictly preserved.
*   **CN:** 满足专业需求：现在手动输入的胶卷型号（如 KODAK 5207）将不再被数据库标准名中途覆盖，真正实现“所写即所得”。

### 4. 135 乳剂号显示修复 / 135 Emulsion Display Fix
*   **EN:** Resolved a bug in the 135 renderer where the emulsion number was hidden; it now displays correctly alongside the film name.
*   **CN:** 处理 135 画幅时，胶卷名旁的乳剂号现在能正常拼接并显示，细节更丰富。

### 5. 灵活图片排序 / Flexible Image Sorting
*   **EN:** Added support for sorting contact sheet images by Filename or EXIF Date, with an optional Reverse toggle.
*   **CN:** 索引页工具新增排序功能：支持按“文件名”或“拍摄时间”排序，配合“倒序”开关，让排版更随心。

---

## 🎨 界面优化 / UI Polish
*   **等宽格栅布局**: 重构了高级设置面板，解决了不同语言下标签挤压和对不齐的问题。

---
*Enjoy your film workflow with GT23 V2.2.3!* 🎞️✨
*Optimized by Antigravity — Robust, Open, Professional.* 🛠️🛡️🔓
