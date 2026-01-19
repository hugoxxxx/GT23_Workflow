# Cairo 库安装指南 / Cairo Library Installation Guide

## 问题描述 / Problem Description
**EN**: CairoSVG requires the Cairo graphics library (DLL files) to be installed on Windows.  
**CN**: CairoSVG 需要在 Windows 上安装 Cairo 图形库（DLL文件）。

## 解决方案 / Solutions

### 方案1：GTK3 运行时安装（推荐 / Recommended）

1. **下载 / Download**:  
   访问 https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases  
   下载最新版本的 `gtk3-runtime-x.x.x-x-x-x-ts-win64.exe`

2. **安装 / Install**:  
   - 运行安装程序  
   - ✅ **重要**: 勾选 "Set up PATH environment variable to include GTK+"  
   - 完成安装

3. **验证 / Verify**:  
   ```powershell
   # 重启终端后运行
   where cairo-2.dll
   ```

4. **重新运行项目 / Rerun**:  
   ```powershell
   D:/Projects/GT23_Workflow/venv/Scripts/python.exe main.py
   ```

### 方案2：手动下载 DLL（快速但不推荐 / Quick but not recommended）

1. 从 https://www.gyan.dev/ffmpeg/builds/ 或其他来源下载 `cairo.dll`
2. 将 DLL 文件放入以下任一位置：
   - `C:\Windows\System32\`
   - 或项目根目录 `d:\Projects\GT23_Workflow\`
   - 或 `venv\Scripts\` 目录

### 方案3：使用 Conda 环境（如果你使用 Anaconda / If using Anaconda）

```bash
conda install -c conda-forge cairo
```

## 验证安装 / Verification

运行以下命令测试 Cairo 是否正确安装：

```powershell
D:/Projects/GT23_Workflow/venv/Scripts/python.exe -c "from cairosvg import svg2png; print('Cairo OK!')"
```

如果输出 `Cairo OK!` 说明安装成功。

## 为什么需要这个？/ Why is this needed?

- **EN**: The 135 film format renderer (`renderer_135.py`) uses SVG to render sprocket holes according to ISO 1007 standards, which requires CairoSVG for rasterization.
- **CN**: 135 画幅渲染器 (`renderer_135.py`) 使用 SVG 绘制符合 ISO 1007 标准的齿孔，需要 CairoSVG 进行栅格化。

## 其他画幅是否受影响？/ Are other formats affected?

- **66, 645, 67 画幅**: ❌ 不需要 Cairo，可以正常运行
- **135 画幅**: ✅ 需要 Cairo 才能渲染齿孔

---

**更新日期 / Updated**: 2026-01-19
