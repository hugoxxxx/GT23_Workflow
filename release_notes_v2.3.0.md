# GT23 Film Workflow v2.3.0-alpha Release Notes

## [2.3.0-alpha] - 2026-03-28

### 🌈 边框美学 2.0 (Border Aesthetics 2.0)
本周期重点重构了边框渲染引擎，引入了全新的双模彩虹体系与专业演示模式。
This cycle redefines the border engine with dual-mode rainbows and professional demo capabilities.

#### 1. 双模彩虹系统 (Dual-Mode Rainbow System)
- **富士彩虹 [PREMIUM] (Fuji Rainbow)**:
  - **全局长卷 (Global Slicing)**: 实现了“连续光谱长卷”逻辑。在批量处理时，系统会自动将完整的彩虹光谱动态等分为 N 份（基于导入张数），确保拼接后呈现出丝滑连贯的一体化视觉感。
  - **高饱和校准 (Vibrant Calibration)**: 针对专业审美进行了色彩饱和度回调，找回了单张模式下那种鲜艳夺目的高级感。
- **马卡龙渐变 (Macaron Dynamic Gradient)**:
  - **动态双色渐变**: 废除了原本的单色块背景，代之以基于索引的“随机双色线性渐变”。单张照片极具梦幻感，批量导出时则呈现出灵动的韵致。

#### 2. 专业化增强 (Professional Enhancements)
- **官方演示模式 (SAMPLE Metadata Mode)**: 新增 `is_sample` 全局开关。开启后，引擎将强制覆盖相机、镜头、参数等元数据为 **“SAMPLE”** 占位符，完美适配商业展示与样片分发。
- **排版去反色加固 (Locked Dark Typography)**: 统一锁定了所有彩虹主题的字体配色为经典的 **“深空灰”**（浅色模式标准）。确保在一片绚烂背景中依然具备顶级的阅读清晰度。

#### 3. 核心修复与优化 (Core Fixes)
- **极冷调深色模式 (Midnight Blue-Black)**: 深色模式背景进化为极致清冷的冷调蓝黑 `(15, 16, 20)`。
- **Logo 智能保护**: 仅对图标中的暗中像素进行反色处理，完美保留品牌原色（如哈苏 V/蔡司 T* 红色标识）。

### 📸 样片全集预览 (Showcase Preview Pack)
所有渐变模式的 5/7/10 张连拼样片已统一归档至核心目录下的 `v2.3.0_Previews` 文件夹，方便一键上传。
All 5/7/10 frame showcase strips for rainbow modes are now archived in the `v2.3.0_Previews` folder for easy sharing.

- **[马卡龙双色渐变全集 (Macaron Strip Pack)](file:///d:/Projects/GT23_Workflow/v2.3.0_Previews/)**
- **[富士全谱长卷全集 (Fuji Strip Pack)](file:///d:/Projects/GT23_Workflow/v2.3.0_Previews/)**

---
### 🛠️ 进度跟踪 (Current Progress)
- [x] 边框模式开发深色模式
- [x] 边框模式开发彩虹模式 (富士长卷 + 马卡龙渐变)
- [ ] 边框模式实现各张照片的自定义数据独立保存 (UI State Persistence)
- [ ] 接触印相模式开发半格模式 (Half-Frame Contact Sheet)

---
*Optimized by Antigravity — Redefining Film Aesthetics.* 🛠️🎨✨
