# GUI测试指南 | GUI Testing Guide

## 🚀 快速启动 | Quick Start

### 1. 环境准备 Environment Setup
```powershell
# 创建GUI专用环境（仅首次）
conda create -n gt23gui python=3.11 -y

# 激活环境
conda activate gt23gui

# 安装依赖
pip install -r requirements-gui.txt
```

### 2. 启动GUI Launch GUI
```powershell
# 确保在项目目录下
cd D:\Projects\GT23_Workflow

# 启动GUI
python main.py
```

---

## ✅ 功能测试清单 | Feature Test Checklist

### 边框工具 Border Tool
- [ ] **界面加载**
  - [ ] Tab显示正常
  - [ ] 所有组件可见
  - [ ] 胶片库下拉列表加载（应有86种胶片）
  
- [ ] **文件选择**
  - [ ] 点击"浏览"按钮打开文件对话框
  - [ ] photos_in文件夹自动检测
  - [ ] 文件数量正确显示
  
- [ ] **模式切换**
  - [ ] 胶片/数码单选按钮切换
  - [ ] 切换到数码时胶片选择区隐藏
  
- [ ] **处理流程**
  - [ ] 准备测试图片在photos_in/
  - [ ] 点击"开始处理"按钮
  - [ ] 进度条显示
  - [ ] 日志实时更新
  - [ ] 处理完成后弹出提示
  - [ ] photos_out/中生成结果

### 底片索引 Contact Sheet
- [ ] **界面加载**
  - [ ] Tab切换正常
  - [ ] photos_in自动检测
  
- [ ] **参数输入**
  - [ ] 画幅选择下拉框（自动/135/645/66/67）
  - [ ] 胶片名称输入（可选）
  - [ ] 乳剂号输入（可选）
  
- [ ] **生成流程**
  - [ ] 准备至少6张同画幅照片
  - [ ] 点击"生成索引页"
  - [ ] 进度消息显示
  - [ ] 生成成功提示
  - [ ] 输出文件正确

### 菜单栏 Menu Bar
- [ ] **文件菜单**
  - [ ] "打开工作目录"能打开文件管理器
  - [ ] "退出"关闭程序
  
- [ ] **帮助菜单**
  - [ ] "关于"显示版本信息
  - [ ] "GitHub仓库"打开浏览器

---

## 🐛 已知限制 | Known Limitations

1. **Python版本要求**
   - 必须使用Python 3.11
   - Python 3.13会导致DLL加载错误

2. **路径限制**
   - 必须在项目根目录运行
   - photos_in/photos_out必须存在

3. **并发处理**
   - 处理过程中不能重复点击按钮（已禁用）
   - 不支持取消正在进行的任务

---

## 📝 反馈测试结果 | Report Test Results

测试完成后，请记录：

### 成功的功能 ✅
- 列出所有正常工作的功能

### 发现的问题 ❌
- 描述问题现象
- 复现步骤
- 错误信息截图

### 改进建议 💡
- UI/UX改进
- 功能增强
- 性能优化

---

## 🔧 常见问题 | Troubleshooting

### Q: 窗口无法启动
```powershell
# 检查环境
conda activate gt23gui
python --version  # 应该是3.11.x

# 检查依赖
pip list | findstr PySide6

# 重新安装
pip install --force-reinstall PySide6
```

### Q: 胶片库加载失败
- 确保config/films.json存在
- 检查JSON格式是否正确

### Q: 处理失败
- 检查photos_in/中的图片格式（支持jpg/png）
- 查看日志输出窗口的错误信息
- 确保core/渲染模块正常工作

---

## 🎯 下一步计划 | Next Steps

Phase 2功能增强：
- [ ] 实时预览功能
- [ ] 批量文件列表显示
- [ ] 配置记忆（上次使用的胶片等）
- [ ] 拖拽上传支持
- [ ] 快捷键支持
- [ ] 多语言界面切换

---

测试愉快！Have fun testing! 🎉
