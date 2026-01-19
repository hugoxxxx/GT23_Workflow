# GT23 Film Workflow v2.0.0 Release Notes
# GT23 胶片工作流 v2.0.0 发布说明

**Release Date | 发布日期**: 2026-01-19

---

## 🎉 What's New | 新功能

### GUI Desktop Application | GUI 桌面应用
- **EN**: Brand-new desktop interface built with `tkinter + ttkbootstrap`. Intuitive two-panel layout with bilingual support and automatic language detection based on system locale.
- **CN**: 基于 `tkinter + ttkbootstrap` 构建的全新桌面界面。提供直观的双面板布局，支持中英双语并根据系统区域自动识别语言。

### Enhanced Border Tool | 增强的边框工具
- **Real-time Preview | 实时预览**
  - EN: Live preview of border processing results before saving.
  - CN: 保存前实时预览边框处理效果。

- **Auto Date Selection | 自动日期选择**
  - EN: Automatically extracts and suggests shooting date from EXIF metadata.
  - CN: 自动从 EXIF 元数据提取并建议拍摄日期。

- **EXIF Visibility Control | EXIF 信息显隐控制**
  - EN: Toggle EXIF information display on/off as needed.
  - CN: 根据需要开启或关闭 EXIF 信息显示。

- **Custom Border Ratio | 自定义边框比例**
  - EN: Flexible border ratio adjustment to match your aesthetic preferences.
  - CN: 灵活调整边框比例以符合您的审美偏好。

---

## 🔧 Improvements & Fixes | 改进与修复

### Icon Reliability | 图标可靠性
- **EN**: Unified `.ico` usage for both taskbar and title bar icons. Fixed asset path resolution under PyInstaller one-file packaging via `_MEIPASS`, eliminating fallback to default Tk icon.
- **CN**: 统一使用 `.ico` 作为任务栏与标题栏图标。通过 `_MEIPASS` 适配 PyInstaller 单文件打包的资源路径，彻底解决图标回退问题。

### Runtime Dependencies | 运行时依赖
- **EN**: Bundle Intel MKL/OpenMP DLLs from Conda environment to resolve "Failed to extract entry: mkl_avx2.2.dll" error on fresh Windows installations.
- **CN**: 自动打包 Conda 环境中的 MKL/OpenMP DLL，修复在全新 Windows 系统上的 "mkl_avx2.2.dll 解包失败" 错误。

### Development Workflow | 开发流程
- **EN**: 
  - Unified Conda environment name to `gt23` for both development and packaging
  - UTF-8 batch script outputs (no more Chinese garbled text)
  - Safer build process with automatic process unlock and cleanup
- **CN**: 
  - 统一 Conda 环境名为 `gt23`，开发与打包使用相同环境
  - 批处理脚本改为 UTF-8 输出（中文不再乱码）
  - 更安全的构建流程，自动解锁旧进程并清理产物

### Code Quality | 代码质量
- **EN**: 
  - Centralized version management in `version.py`, window titles auto-sync
  - Dependencies aligned to `ttkbootstrap` (removed unused PySide6)
  - Improved maintainability and consistency
- **CN**: 
  - 版本号集中到 `version.py` 管理，窗口标题自动同步
  - 依赖切换为 `ttkbootstrap`（移除未使用的 PySide6）
  - 改善可维护性与一致性

---

## 📦 Installation | 安装

### Option A: Windows Executable (Recommended) | Windows 可执行程序（推荐）

1. **Download | 下载**: Get `GT23_Workflow.exe` from the Assets section below.

2. **Setup Working Directory | 设置工作目录**:
   ```
   MyProject/
   ├── GT23_Workflow.exe
   ├── photos_in/          (Place your scans here | 放入扫描文件)
   └── photos_out/         (Outputs appear here | 输出结果在此)
   ```

3. **Launch | 启动**: Double-click `GT23_Workflow.exe` to start the GUI.

### Option B: Build From Source | 从源码构建

```powershell
# Clone repository | 克隆仓库
git clone https://github.com/yourusername/GT23_Workflow.git
cd GT23_Workflow

# Create environment | 创建环境
conda create -n gt23 python=3.11 -y
conda activate gt23
pip install -r requirements-gui.txt

# Build EXE | 打包 EXE
.\build_gui.bat
```

---

## ⚠️ Known Issues | 已知问题

### Taskbar Icon Not Updating | 任务栏图标未更新
- **EN**: If the taskbar icon shows an old icon after installation:
  1. Unpin the old shortcut from the taskbar
  2. Launch the new `GT23_Workflow.exe`
  3. Pin the new instance to the taskbar
  4. (Alternative) Restart Windows to rebuild icon cache
  
- **CN**: 如果安装后任务栏图标显示旧图标：
  1. 取消固定旧的任务栏快捷方式
  2. 启动新的 `GT23_Workflow.exe`
  3. 将新实例固定到任务栏
  4. （可选）重启 Windows 以重建图标缓存

### First Launch Might Be Slow | 首次启动可能较慢
- **EN**: The first launch may take 5-10 seconds as Windows extracts embedded resources. Subsequent launches will be faster.
- **CN**: 首次启动可能需要 5-10 秒，因为 Windows 需要解压内嵌资源。后续启动会更快。

---

## 🔄 Upgrade Notes | 升级说明

### From v1.x CLI | 从 v1.x CLI 版本升级
- **EN**: v2.0.0 is a GUI-focused release. CLI functionality is paused for this version. If you need CLI features, please continue using v1.9.x.
- **CN**: v2.0.0 是以 GUI 为主的版本。本版本暂停维护 CLI 功能。如需 CLI 特性，请继续使用 v1.9.x。

### Configuration Files | 配置文件
- **EN**: All configuration files in `config/` folder remain compatible. No migration needed.
- **CN**: `config/` 文件夹中的所有配置文件保持兼容。无需迁移。

---

## 📝 Technical Details | 技术细节

### System Requirements | 系统要求
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: ~200MB for application and temporary files

### Dependencies (Bundled) | 依赖项（已内置）
- Python 3.11
- tkinter + ttkbootstrap 1.20.0
- Pillow 12.0.0
- ExifRead 3.5.1
- NumPy 2.4.1
- Intel MKL runtime libraries

### Build Information | 构建信息
- **Packager**: PyInstaller 6.18.0
- **Environment**: Conda (gt23)
- **Icon**: assets/GT23_Icon.ico (multi-size: 16-256px)

---

## 🙏 Credits | 致谢

**EN**: Special thanks to all film photographers who provided feedback during development. Your insights helped shape this release.

**CN**: 特别感谢所有在开发期间提供反馈的胶片摄影师。你们的见解帮助塑造了这个版本。

---

## 📧 Support | 技术支持

**EN**: For bug reports or feature requests, please open an issue on GitHub or contact: **xjames007@gmail.com**

**CN**: 如需报告问题或提出功能建议，请在 GitHub 开启 issue 或联系：**xjames007@gmail.com**

---

## 📄 License | 许可证

MIT License - See LICENSE file for details.

---

**Previous Releases**: [v1.9.x](link-to-previous-release)
