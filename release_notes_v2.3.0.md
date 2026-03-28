# GT23 Film Workflow v2.3.0-alpha Release Notes

## [2.3.0-alpha] - 2026-03-28

### 🌈 边框美学 2.0 (Border Aesthetics 2.0)
本周期重点重构了边框渲染引擎，引入了全新的双模彩虹体系与专业演示模式。
This cycle redefines the border engine with dual-mode rainbows and professional demo capabilities.

#### 1. 双模彩虹系统 (Dual-Mode Rainbow System)
- **彩虹主题 [PREMIUM] (Rainbow)**:
  - **全局长卷 (Global Slicing)**: 实现了“连续光谱长卷”逻辑。在批量处理时，系统会自动将完整的彩虹光谱动态等分为 N 份（基于导入张数），确保拼接后呈现出丝滑连贯的一体化视觉感。
  - **高饱和校准 (Vibrant Calibration)**: 针对专业审美进行了色彩饱和度回调，找回了高保真的色彩高级感。
- **马卡龙渐变 (Macaron Dynamic Gradient)**:
  - **9 宫格极致对齐**: 扩展色彩库至 9 种，并实现了基于物理位置的确定性分配，完美支持朋友圈“九宫格”排版。

#### 2. 状态持久化与独立性 (State Persistence & Independence)
- **单图显隐开关持久化**: 每个图片的 EXIF 字段（制造、型号、镜头、快门、光圈、ISO）可见性设置现在会独立保存，切换图片时自动恢复，告别全局覆盖的困扰。
- **拖拽色彩重排同步**: 马卡龙色系现在支持随缩略图拖拽排序实时更新背景色，实现交互逻辑与视觉反馈的完美闭环。

#### 3. 专业化增强 (Professional Enhancements)
- **官方演示模式 (SAMPLE Metadata Mode)**: 新增 `is_sample` 全局开关。开启后，引擎将强制覆盖相机、镜头、参数等元数据为 **“SAMPLE”** 占位符，完美适配商业展示与样片分发。
- **排版去反色加固 (Locked Dark Typography)**: 统一锁定了所有彩虹主题的字体配色为经典的 **“深空灰”**（浅色模式标准）。确保在一片绚烂背景中依然具备顶级的阅读清晰度。

#### 4. 极简与本地化 (Minimalism & Localization)
- **纯净模式 (Pure Mode)**: 全新“纯净模式”上线。勾选后，渲染引擎将全量滤除相机信息、参数文本与 Logo 图层，实现 100% 极简视觉（特别适用于展示艺术背景）。
- **中文字体降级 (CJK Fallback)**: 深度集成了 CJK 字符检测引擎。当识别到手动输入的中文（如“徕卡”、“哈苏”）时，会自动将字库降级为系统原生**微软雅黑**，彻底解决乱码。
- **回车即时预览 (Enter-to-Refresh)**: 为设置面板中所有参数 Entry 字段绑定了键盘事件，输入完成按回车即可立即触发现场渲染。

#### 5. 核心修复与优化 (Core Fixes)
- **术语一致性**: “富士彩虹”正式精简命名为 **“彩虹” (Rainbow)**。
- **UI 视野优化**: 拓宽了主题下拉框的显示宽度（至 20 像素），解决了长文本截断问题。
- **Logo 智能保护**: 仅对图标中的暗中像素进行反色处理，保留品牌原色（如蔡司 T* 红色标识）。

### 📸 样片全集预览 (Showcase Preview Pack)
所有渐变模式的 5/7/10 张连拼样片已统一归档至核心目录下的 `v2.3.0_Previews` 文件夹，方便一键上传。
All 5/7/10 frame showcase strips for rainbow modes are now archived in the `v2.3.0_Previews` folder for easy sharing.

---
### 🛠️ 进度跟踪 (Current Progress)
- [x] 边框模式开发深色模式
- [x] 边框模式开发彩虹模式 (长卷彩虹 + 马卡龙渐变)
- [x] 边框模式实现纯净模式与中文适配
- [x] 边框模式实现各张照片的自定义数据独立保存 (UI State Persistence)
- [ ] 接触印相模式开发半格模式 (Half-Frame Contact Sheet)

---
*Optimized by Antigravity — Redefining Film Aesthetics.* 🛠️🎨✨
