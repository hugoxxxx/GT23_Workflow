# GT23 Film Workflow v2.1.0 Release Notes
# GT23 胶片工作流 v2.1.0 发布说明

**Release Date | 发布日期: 2026-03-09**

---

## 🎉 What's New | 新功能

### Camera Logo System | 相机 Logo 系统
- **EN**: Automatic camera logo detection and rendering. Optimized for **Kyocera/Contax** rangefinder series: **Contax G1, G2, T, T2, T3, TVS I/II/III**. Replaces textual camera info with high-fidelity vector logos.
- **CN**: 自动相机 Logo 识别与渲染。首发适配 **京瓷/康泰时（Contax）** 旁轴及便携系列：**Contax G1, G2, T, T2, T3, TVS I/II/III**。系统将自动使用高保真矢量图标替换原有的相机型号文字。

### Zeiss T* Highlight | 蔡司 T* 红色标识
- **EN**: Special support for Zeiss lenses. The "T*" identification in lens info is now rendered in the signature Zeiss red (`#ed1f25`) for a more professional and aesthetic look.
- **CN**: 针对蔡司镜头的专项优化。镜头型号中的 "T*" 标识现在会以蔡司标志性的红色（`#ed1f25`）呈现，排版更加专业且精致。

---

## 🔧 Improvements & Fixes | 改进与修复

### Pixel-Perfect Centering | 像素级视觉对齐
- **EN**: Upgraded Typography Engine with **Ink BBox** (Ink Bounding Box) algorithm. Ensures absolute horizontal centering based on visual pixels rather than character advance, aligning logos and text perfectly.
- **CN**: 升级排版引擎，引入 **Ink BBox（墨迹包围盒）算法**。居中逻辑从“字符步进”进化为“视觉墨迹”对齐，确保 Logo 与文字在视觉中轴线上达到像素级的严丝合缝。

### Windows SVG Compatibility | Windows SVG 兼容性修复
- **EN**: Integrated automatic Cairo DLL resolution for Windows environments. Resolves issues where SVG rendering would fail due to missing system libraries in blank environments.
- **CN**: 针对 Windows 环境内置了自动加载 Cairo DLL 的逻辑。解决了在纯净系统环境下因缺失运行库导致 SVG 图标无法正常显示的兼容性问题。

### Border Aesthetics | 边框排版微调
- **EN**: Improved vertical spacing between title and subtitle for a more balanced layout. Optimized film matching keywords for "FUJICHROME RDP III" and "EKTACHROME E100".
- **CN**: 微调了主副标题之间的垂直间距，使整体布局更加疏朗平衡。同时优化了 "FUJICHROME RDP III" 和 "EKTACHROME E100" 的自动匹配关键字，识别更精准。

---

## 📦 Installation | 安装
- **Option A: Windows Executable** | 请下载发布的 `GT23_Workflow_v2.1.0.zip` 并运行 `main.exe`。
- **Option B: From Source** | `git pull` 最新代码并确保 conda 环境 `gt23` 已安装 `cairosvg`。

---

## 🙏 Credits | 致谢
Special thanks to the community for providing high-quality camera logos and feedback!
感谢社区提供的优质相机矢量 Logo 及针对排版对齐的宝贵反馈！
