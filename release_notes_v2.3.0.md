# GT23 Film Workflow v2.3.0 发布说明

## � 模块一：边框样式与社交分享增强 (Border Styles & Socials)
在 v2.3.0 版本中，我们深耕社交媒体分享审美，带来了 3 款全新边框主题与极致极简的交互逻辑。

### 1.1 🌈 彩虹相纸 (Rainbow Theme)
灵感源自经典的富士渐变相纸。系统会自动计算批量照片的光谱顺序，呈现出丝滑、无断点的彩虹渐变长卷。

![Rainbow 10-Image Strip](previews/v2.3/strip_rainbow_10.jpg)
*彩虹相纸：10 张横向连拼连续渐变效果展示。*

### 1.2 🍭 马卡龙色系 (Macaron Palette)
专为朋友圈九宫格打造。提供 9 种精选动态渐变色，并引入基于物理位置的确定性分配算法，确保每次预览色彩始终如一。

![Macaron 9-Grid Preview](previews/v2.3/grid_macaron.jpg)
*马卡龙配色：九宫格梦幻渐变展示。*

### 1.3 🌑 专业深色边框 (Professional Dark Border)
针对高对比度作品推出的极致深空灰背景，配合白墨增强的反色算法，确保 Logo 与文字极具质感。

![Dark Border Sample](previews/v2.3/sample_dark.jpg)
*深色边框：更适合极简主义的作品展示。*

### 1.4 � 纯净模式与智能记忆 (Pure Mode & State Memory)
- **纯净模式**: 一键隐藏所有文字与参数，仅保留色彩边框。
- **配置记忆**: 每张照片独立记忆显隐设置，切换图片时自动恢复，极大提升操作流。

---

## 🎞️ 模块二：接触印相与 135HF 渲染重构 (Contact Sheet & 135HF Rebirth)
针对资深胶片摄影师，我们完成了半格索引页渲染器的底层架构重组。

### 2.1 135HF v3.0 (统一旋转架构)
解决了 P（水平条）与 L（垂直条）在物理参数上的非对称痛点。现在两种方向具备完全一致的物理精度（228mm 总带宽，0.5mm 对称 margins）。

**P/L 模式双向样片展示：**
````carousel
![135HF P-Mode](previews/v2.3/135hf_p_mode.jpg)
P 模式：传统水平底片条排版
<!-- slide -->
![135HF L-Mode](previews/v2.3/135hf_l_mode.jpg)
L 模式：垂直底片条旋转架构（ branding/numbering 已自动旋转）
````

### 2.2 72 画幅补全与居中无损裁切
- **满额补齐**: 索引页始终填满 72 个槽位（不足部分透出底片基色），还原最真实的底片观感。
- **拒绝拉伸**: 引入 `ImageOps.fit` 裁切算法，非标比例（如 1:1, 16:9）照片也能在 18x24mm 槽位内精准居中对齐。

### 2.3 “半格模式”专用开关 (GUI Linkage)
底片索引面板新增独立工具按钮开关，不论自动识别结果如何，只要按下即可强制切入 135HF 逻辑，并实现 P/L 面板的智能联动。

---
## 🛠️ 下一阶段计划
- [ ] **多卷合拼 (Multi-Roll Merge)**：支持在一个索引页中合成多卷胶片的预览。

---
*Stay analog in a digital world. 🎞️📸*
