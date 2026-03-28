# GT23 Film Workflow v2.3.0 发布说明 (Release Notes)

## 📸 模块一：边框样式与社交分享增强 (Module 1: Border Styles & Socials)
在 v2.3.0 版本中，我们深耕社交媒体分享审美，带来了 3 款全新边框主题与极致极简的交互逻辑。
In v2.3.0, we've focused on social media ethics, introducing 3 new border themes and ultra-minimalist interaction logic.

### 1.1 🌈 彩虹相纸 (Rainbow Theme)
灵感源自经典的富士渐变相纸。系统会自动计算批量照片的光谱顺序，呈现出丝滑、无断点的彩虹渐变长卷。
Inspired by classic Fujifilm Instax rainbow paper. The system automatically calculates the spectral order of batch photos, creating a smooth, seamless rainbow gradient long-strip.

<img src="previews/v2.3/strip_rainbow_10.jpg" width="800" alt="Rainbow Strip">
*彩虹相纸：10 张横向连拼连续渐变效果展示 (10-Image Continuous Gradient).*

### 1.2 🍭 马卡龙色系 (Macaron Palette)
专为朋友圈九宫格打造。提供 9 种精选动态渐变色，并引入基于物理位置的确定性分配算法，确保每次预览色彩始终如一。
Designed for the WeChat Moments 9-grid. Features 9 curated dynamic gradients with a location-based deterministic allocation algorithm, ensuring consistent colors every time you preview.

<img src="previews/v2.3/grid_macaron.jpg" width="600" alt="Macaron 9-Grid">
*马卡龙配色：九宫格梦幻渐变展示 (Macaron 9-Grid Dreamy Gradient).*

### 1.3 🌑 专业深色边框 (Professional Dark Border)
针对高对比度作品推出的极致深空灰背景，配合白墨增强的反色算法，确保 Logo 与文字极具质感。
A deep space gray background for high-contrast works. Coupled with white-ink enhancement algorithms, it ensures logos and text are sharp and premium.

<img src="previews/v2.3/sample_dark.jpg" width="600" alt="Dark Border Sample">
*深色边框：更适合极简主义的作品展示 (Dark Border: Ideal for Minimalist Photography).*

### 1.4 🧊 纯净模式与智能记忆 (Pure Mode & State Memory)
- **纯净模式 (Pure Mode)**: 一键隐藏所有文字与参数，仅保留色彩边框。Hide all text and parameters with one click, leaving only the colored border.
- **配置记忆 (State Memory)**: 每张照片独立记忆显隐设置，切换图片时自动恢复。Each photo remembers its own visibility settings, automatically restoring them when you switch images.

---

## 🎞️ 模块二：接触印相与全新的 135HF 半格模式 (Module 2: Contact Sheet & 135HF Mode)
这是影友期待已久的功能，现在正式适配 135 半格底片 (18x24mm)。
A long-awaited feature, now officially compatible with 135 half-frame film (18x24mm).

### 2.1 🎞️ 全新 135HF 半格索引支持 (All-New 135HF Support)
专为半格相机打造。现在支持两种经典的底片排列方式，满足不同的叙事表达：
Designed specifically for half-frame cameras. Now supports two classic layouts for different narrative expressions:
- **P 模式（横向/Horizontal）**: 传统的水平底片条排版，完美呈现底片的连续感和电影感视觉。Traditional horizontal strip layout, perfect for capturing continuous narrative and cinematic vibes.
- **L 模式（纵向/Vertical）**: 独特的垂直底片条排列，底片边上的品牌名、数字标号和拍摄信息会自动旋转对齐。Unique vertical strip arrangement, with branding, numbering, and shooting info automatically rotated and aligned.

**样片展示 (Samples)：**

<img src="previews/v2.3/135hf_p_mode.jpg" width="800" alt="135HF P-Mode">
*P 模式：传统水平底片条排版 (P-Mode: Traditional Horizontal Strips)*

<img src="previews/v2.3/135hf_l_mode.jpg" width="800" alt="135HF L-Mode">
*L 模式：独特垂直排列方式 (L-Mode: Unique Vertical Arrangement)*

### 2.2 📸 满额排版与智能对齐 (Full Layout & Smart Alignment)
为了追求极致的物理仿真，我们在半格渲染逻辑中加入了以下改进：
Pursuing extreme physical simulation, we've added the following improvements to the half-frame rendering logic:
- **始终完整 (Always Full)**: 索引页始终呈现完整的 72 个画幅槽位，还原冲印店的原始观感。The contact sheet always presents 72 full slots, restoring the authentic lab-printed look.
- **居中不拉伸 (Center Fitting)**: 无论照片比例如何，系统都会在半格框内精准居中展示，杜绝变形。Regardless of aspect ratio, photos are perfectly centered within the half-frame slots without stretching.

### 2.3 🔘 极简一键开关 (Minimalist Toggle)
我们在界面上新增了“半格模式”工具按钮。一键开启即可实现功能强制覆盖，并在同一面板下自由切换排版方向。
New "Half-Frame Mode" toggle button. Enable it with one click for manual override and switch orientations seamlessly within the same panel.

---
## 🛠️ 下一阶段计划 (Next Phase)
- [ ] **安卓版本全功能同步 (Android Sync)**：将 v2.3.0 的新特性同步至移动端。Syncing v2.3.0 features to the mobile version.
- [ ] **多卷合拼 (Multi-Roll Merge)**：支持在一个索引页中合成多卷胶片的预览。Supporting multi-roll preview generation in one sheet.

---
*Stay analog in a digital world. 🎞️📸*
