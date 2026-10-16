# ⚡ EndStartL (Lite Edition) - 鹰角启动器单脚本极简自动化

**EndStartL** 是基于 **MaaFramework 官方原生引擎** 构建的鹰角启动器专用极简自动化工具。

彻底剥离 WebUI、FastAPI、Uvicorn 与图像编辑依赖，专为**命令行极速运行**与**开机/桌面一键启动**量身定制。

---

## ✨ 核心特性

- 🎯 **单任务极致精简**：专为《明日方舟：终末地》/ 鹰角启动器定制，体积较完整版减少超过 50%。
- 🔄 **全自动更新闭环**：
  - 启动器有更新时自动点击“更新”并确认；
  - 自动监控下载速率与完成百分比；
  - 更新安装完毕后自动点击“开始游戏”；
  - 游戏拉起后自动退出自身并关闭控制台窗口。
- 🛡️ **UAC 自动提权**：双击批处理自动检测并请求 Windows 管理员权限，杜绝权限不足引起的启动失败。
- 🔍 **离线高精度 OCR**：内置 PaddleOCR 离线模型，毫秒级定位目标按钮，无需联网。

---

## 🚀 使用方法
  **配置启动器路径**：修改main.py第33行。

### 1. 双击一键启动与关闭（推荐）
- **一键启动游戏**：双击 [launch_game.bat](file:///E:/AAAprojects/EndStartL/launch_game.bat)（拉起启动器、更新并启动游戏，拉起后自动退出）。
- **一键关闭启动器**：双击 [close_launcher.bat](file:///E:/AAAprojects/EndStartL/close_launcher.bat)（安全终止启动器主程序与常驻进程，完成后自动关闭黑框）。
- **完全静默运行**：
  - [launch_game_silent.vbs](file:///E:/AAAprojects/EndStartL/launch_game_silent.vbs)（100% 后台静默启动）
  - [close_launcher_silent.vbs](file:///E:/AAAprojects/EndStartL/close_launcher_silent.vbs)（100% 后台静默关闭）

### 2. 命令行调用 (CLI)
```bash
# 激活环境并直接运行
.\.venv\Scripts\python.exe main.py

# 仅测试识别（Dry Run 模式，不执行真实点击）
.\.venv\Scripts\python.exe main.py --dry-run

```

---

## 📁 项目结构

```text
EndStartL/
├── launch_game.bat          # 双击拉起批处理 (自带 UAC 提权，完成后自动退出)
├── launch_game_silent.vbs   # 100% 静默运行脚本
├── close_launcher.bat       # 双击关闭启动器批处理 (自动终止 Games.exe 与 Launcher.exe)
├── close_launcher_silent.vbs# 100% 静默关闭脚本
├── main.py                  # 核心自动化控制脚本
├── requirements.txt         # 极简依赖库 (仅 MaaFw)
├── core/
│   ├── bot.py               # MaaFramework 原生视觉与点击封装
│   └── window.py            # Win32 原生窗口探测与句柄管理
└── resource/                # MaaFramework 核心离线 OCR 推理模型
    ├── config/
    └── model/ocr/
```
