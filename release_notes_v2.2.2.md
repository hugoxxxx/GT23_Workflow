# GT23 Film Workflow v2.2.2 Release Notes (Slim & Smart)

## 🏮 重磅更新：极简架构与智能同步 / Major Update: Slim & Smart

### 1. 80% 极限瘦身：轻量化之巅 / Extreme 80% Size Reduction
我们通过对二进制依赖的“外科手术”级精简，将 EXE 体积从约 **200MB** 暴减至 **38.8 MB**。
*   **EN:** Slashed EXE size from ~200MB to **38.8 MB** (80% reduction!) by surgically purging unused MKL/OpenMP math libraries.
*   **CN:** 彻底解决了以往“小工具大包体”的痛点，启动更快，分发更便捷。

### 2. 智能云端同步：码资分离 / Smart Asset Sync: Code-Asset Separation
现在，独立版 EXE 不再强行塞入图标。
*   **EN:** Standalone EXE now comes "Zero-Asset" for maximum speed. It prompts for **One-Click Sync** (121+ logos) on first launch.
*   **CN:** 采用全新的“码资分离”架构。首次启动时将引导**一键同步** 121+ 款相机图标，并在 EXE 旁自动建立 `GT23_Assets` 资源库。

### 3. 硬核容错：GitHub/Gitee 双向切换 / Robust Failover: Dual-Remote Strategy
*   **EN:** Implemented automatic failover between GitHub and Gitee. Added mandatory ZIP signature validation (`PK\x03\x04`) to prevent crashes from network redirects or 404 HTML pages.
*   **CN:** 实现了 GitHub 与 Gitee 双源自动切换逻辑。新增了 ZIP 签名强制校验，彻底杜绝了因网络环境波动或 HTML 报错页导致的同步崩溃。

---

## 🚀 使用指南 (独立版用户) | How to Use (EXE Users)
1. **下载并运行**: 获取 `GT23_Workflow_v2.2.2.exe` (仅约 39MB)。
2. **一键同步**: 首次启动程序会提示“是否同步资源库？”，点击**是**。
3. **满血升级**: 程序自动从云端拉取 121+ 款图标与胶片配置落位至 `GT23_Assets`。
4. **即席创作**: 无需任何配置，所有图标与机型匹配将立刻生效。

---

## 📷 全量支持图标博物馆 (121+ Models) / Asset Gallery
![Logo Full Map](assets/LOGO_FULL_MAP.jpg)

目前已支持包括 Leica, Canon, Nikon, Pentax, Mamiya, Hasselblad, Contax 在内的 **121 款** 经典机型。所有图标均来自原始说明书手工临摹。
*   **EN:** Massive library expansion covering 121+ models, all manually traced from vintage brochures to capture the soul of each brand.

---

## 🎨 UI 与稳定性优化 / UI & Stability Polish
*   **Native Typography**: 采用了系统级原生字体（微软雅黑/Segoe UI），解决了高分屏下的虚化与文本截断问题。
*   **Standardized Paths**: 统一了渲染引擎与同步引擎的路径逻辑，确保资产加载 100% 成功。
*   **requests Inside**: 修复了极简版缺失 `requests` 库导致的同步报错。

---
*Enjoy your film workflow with GT23 V2.2.2!* 🎞️✨
*Optimized by Antigravity — Faster, Lighter, Smarter.* 🛠️📉💎
