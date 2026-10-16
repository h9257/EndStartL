"""
EndStartL (Lite Edition) - 鹰角启动器单脚本极简自动化
拉起启动器 -> 检测并等待更新 -> 自动点击开始游戏 -> 退出程序
"""

import os
import sys
import time
import argparse
import subprocess
import logging
from pathlib import Path

# Fix console encoding for Chinese / Unicode
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.bot import DesktopBot
from core.window import list_windows, activate_window

logger = logging.getLogger("EndStartL")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s")

DEFAULT_LAUNCHER_DIR = r"E:\games\Hypergryph Launcher"
DEFAULT_EXE_NAME = "Launcher.exe"


def find_launcher_window():
    """查找鹰角启动器真实窗口，精确匹配 Qt 启动器，严格排除终端控制台与文件资源管理器。"""
    windows = list_windows()

    # 1. 优先匹配 Qt 类名且标题包含鹰角/Hypergryph
    for w in windows:
        title = w["title"]
        class_name = w.get("class_name", "")
        if class_name.startswith("Qt"):
            if title == "鹰角启动器" or "鹰角" in title or "Hypergryph" in title:
                return w

    # 2. 标题精确匹配，排除控制台和本程序自身
    for w in windows:
        title = w["title"]
        class_name = w.get("class_name", "")
        if class_name in ("ConsoleWindowClass", "CASCADIA_HOSTING_WINDOW_CLASS", "CabinetWClass"):
            continue
        if any(ign in title for ign in ("文件资源管理器", "自动拉起", "EndStart", "cmd.exe", "powershell")):
            continue
        if title == "鹰角启动器":
            return w

    return None


def wait_update_completed(bot: DesktopBot, dry_run: bool = False, max_wait_hours: float = 4.0) -> bool:
    """持续监控游戏更新状态。在下载与解包全部完成后，自动点击“开始游戏”拉起游戏。"""
    READY_KEYWORDS = ["开始游戏", "启动", "进入游戏"]
    CONFIRM_KEYWORDS = ["确定", "确认", "完成", "安装完成"]

    start_time = time.time()
    last_log_time = 0
    poll_interval = 4.0

    while time.time() - start_time < max_wait_hours * 3600:
        time.sleep(poll_interval)

        # 确保启动器窗口正常连接
        if not bot.is_window_alive():
            target_win = find_launcher_window()
            if not target_win:
                logger.warning("等待更新中：启动器窗口暂时不可见，稍后重试...")
                time.sleep(2.0)
                continue
            bot.connect(target_win["hwnd"])

        ocr_results = bot.ocr()

        # 1. 优先检查“开始游戏”是否已就绪
        ready_btn = None
        for kw in READY_KEYWORDS:
            for item in ocr_results:
                if kw in item["text"]:
                    ready_btn = item
                    break
            if ready_btn:
                break

        if ready_btn:
            cx, cy = ready_btn["center"]
            logger.info("==================================================")
            logger.info(f"🎉 游戏更新已顺利完成！检测到启动按钮: [{ready_btn['text']}] ({cx}, {cy})")
            logger.info("==================================================")

            if dry_run:
                logger.info("[Dry Run 模式] 不实际执行点击。")
                return True

            logger.info(f"正在自动点击启动游戏 ({cx}, {cy}) ...")
            bot.activate()
            time.sleep(0.5)
            clicked = bot.click(cx, cy)
            if clicked:
                logger.info("✅ 游戏已通过自动化程序成功拉起！")
                time.sleep(3.0)
                return True
            else:
                logger.error("点击启动按钮失败！")
                return False

        # 2. 检查是否有完成类弹窗需要点击确认
        for item in ocr_results:
            if any(ckw in item["text"] for ckw in CONFIRM_KEYWORDS) and len(item["text"]) <= 6:
                logger.info(f"检测到更新过渡提示弹窗 [{item['text']}]，自动点击确认...")
                bot.click(*item["center"])
                time.sleep(1.0)
                break

        # 3. 定期（每 12 秒）输出下载速度与百分比进度，避免刷屏
        if time.time() - last_log_time >= 12.0:
            last_log_time = time.time()
            progress_texts = []
            for item in ocr_results:
                txt = item["text"]
                if any(ind in txt for ind in ("%", "MB/s", "KB/s", "GB", "MB", "正在", "校验", "解压", "下载")):
                    progress_texts.append(txt)

            if progress_texts:
                summary = " | ".join(progress_texts[:3])
                logger.info(f"[更新进行中] {summary}")
            else:
                elapsed_min = (time.time() - start_time) / 60
                logger.info(f"[更新进行中] 正在持续监测更新进度... (已等待 {elapsed_min:.1f} 分钟)")

    logger.error("等待游戏更新超时（超过最大限制时间）！")
    return False


def run(
    launcher_dir: str = DEFAULT_LAUNCHER_DIR,
    timeout: float = 35.0,
    dry_run: bool = False
) -> bool:
    """主执行逻辑：拉起 -> 识别/更新 -> 启动 -> 退出"""
    logger.info("=== [EndStartL] 开始执行鹰角启动器单脚本自动化 ===")

    launcher_path = Path(launcher_dir) / DEFAULT_EXE_NAME
    if not launcher_path.exists():
        logger.error(f"找不到启动器程序: {launcher_path}")
        return False

    # 1. 检查启动器是否已经在运行中
    target_win = find_launcher_window()
    if target_win:
        logger.info(f"检测到鹰角启动器已在运行中: [{target_win['title']}] (HWND: {target_win['hwnd_hex']})")
    else:
        logger.info(f"正在拉起启动器进程: {launcher_path} ...")
        launched = False
        try:
            import ctypes
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "open", str(launcher_path), "", str(launcher_dir), 1
            )
            if ret > 32:
                launched = True
                logger.info("已通过系统 Shell 接口调用启动程序。")
        except Exception as e:
            logger.warning(f"ShellExecute 启动异常: {e}")

        if not launched:
            try:
                subprocess.Popen([str(launcher_path)], cwd=str(launcher_dir), shell=False)
                launched = True
            except Exception as e:
                logger.error(f"启动进程失败: {e}")
                return False

        logger.info(f"等待启动器主窗口出现 (最大等待 {timeout} 秒)...")
        start_t = time.time()
        while time.time() - start_t <= timeout:
            target_win = find_launcher_window()
            if target_win:
                logger.info(f"成功发现启动器窗口: [{target_win['title']}] ({target_win['hwnd_hex']})")
                break
            time.sleep(1.0)

    if not target_win:
        logger.error("超时未检测到鹰角启动器窗口！")
        return False

    # 2. 激活并连接 MaaFramework 视觉识别引擎
    activate_window(target_win["hwnd"])
    time.sleep(1.0)

    logger.info("正在连接视觉识别引擎 (MaaFramework)...")
    try:
        bot = DesktopBot()
        if not bot.connect(target_win["hwnd"], activate=True):
            logger.error("连接窗口控制器失败！")
            return False
    except Exception as e:
        logger.error(f"初始化识别引擎失败: {e}")
        return False

    # 3. OCR 识别按钮状态
    logger.info("正在对启动器界面进行全屏 OCR 扫描，识别按钮状态...")
    READY_KEYWORDS = ["开始游戏", "启动", "进入游戏"]
    UPDATE_KEYWORDS = ["更新", "立即更新", "更新游戏", "获取更新"]
    PROGRESS_KEYWORDS = ["正在下载", "正在更新", "正在校验", "正在解包", "下载中", "更新中", "校验中", "暂停"]
    CONFIRM_KEYWORDS = ["确定", "确认", "继续更新", "继续"]

    def find_target(ocr_list, keywords):
        for kw in keywords:
            for item in ocr_list:
                if kw in item["text"]:
                    return item, kw
        return None, None

    matched_item = None
    matched_keyword = None
    scan_start = time.time()

    while time.time() - scan_start <= 15.0:
        ocr_results = bot.ocr()
        matched_item, matched_keyword = find_target(ocr_results, READY_KEYWORDS)
        if matched_item:
            break
        matched_item, matched_keyword = find_target(ocr_results, UPDATE_KEYWORDS)
        if matched_item:
            break
        prog_item, prog_kw = find_target(ocr_results, PROGRESS_KEYWORDS)
        if prog_item:
            matched_item, matched_keyword = prog_item, "更新进行中"
            break

        logger.info("界面可能仍在加载过渡中，稍后重试扫描...")
        time.sleep(1.5)

    if not matched_item:
        logger.error("未能找到启动或更新按钮！当前界面文本:")
        for t in bot.ocr()[:10]:
            logger.error(f"  - [{t['text']}] at {t['center']}")
        return False

    # 4. 执行针对性动作
    if matched_keyword in UPDATE_KEYWORDS:
        cx, cy = matched_item["center"]
        logger.info(f"🔄 检测到游戏存在新版本更新: [{matched_item['text']}] (坐标: {cx}, {cy})")
        if dry_run:
            logger.info("[Dry Run 模式] 识别到更新按钮，不实际执行点击。")
            return True

        logger.info(f"正在自动点击触发游戏更新 ({cx}, {cy}) ...")
        bot.activate()
        time.sleep(0.3)
        bot.click(cx, cy)
        time.sleep(2.0)

        # 检查是否弹出更新确认对话框
        confirm_results = bot.ocr()
        confirm_btn, _ = find_target(confirm_results, CONFIRM_KEYWORDS)
        if confirm_btn and len(confirm_btn["text"]) <= 6:
            ccx, ccy = confirm_btn["center"]
            logger.info(f"检测到更新确认弹窗 [{confirm_btn['text']}]，自动点击确认...")
            bot.click(ccx, ccy)
            time.sleep(2.0)

        logger.info("⏳ 游戏更新已触发，自动化程序将持续在后台等待更新下载与解压完成...")
        return wait_update_completed(bot, dry_run=dry_run)

    elif matched_keyword == "更新进行中":
        logger.info(f"⏳ 检测到游戏当前已处于下载/更新状态中: [{matched_item['text']}]")
        if dry_run:
            logger.info("[Dry Run 模式] 检测到更新进行中，跳过等待。")
            return True
        logger.info("自动化程序将持续在后台等待更新下载与解压完成...")
        return wait_update_completed(bot, dry_run=dry_run)

    else:
        # 直接点击开始游戏
        cx, cy = matched_item["center"]
        logger.info(f"🎯 成功识别到启动按钮: [{matched_item['text']}]")
        logger.info(f"   匹配关键词: '{matched_keyword}', 置信度: {matched_item['score']:.2f}, 坐标: ({cx}, {cy})")

        if dry_run:
            logger.info(f"[Dry Run 模式] 识别成功，不实际执行点击。")
            return True

        logger.info(f"正在模拟鼠标点击启动按钮 ({cx}, {cy}) ...")
        bot.activate()
        time.sleep(0.3)
        clicked = bot.click(cx, cy)

        if clicked:
            logger.info("✅ 启动按钮点击成功！游戏正在启动中...")
            time.sleep(2.0)
            return True
        else:
            logger.error("❌ 点击动作执行失败！")
            return False


def main():
    parser = argparse.ArgumentParser(description="EndStartL - 鹰角启动器单脚本极简自动化 (MaaFramework Core)")
    parser.add_argument("--dir", default=DEFAULT_LAUNCHER_DIR, help="启动器所在目录路径")
    parser.add_argument("--timeout", type=float, default=35.0, help="等待窗口出现超时秒数")
    parser.add_argument("--dry-run", action="store_true", help="仅识别测试，不触发真实点击")
    args = parser.parse_args()

    success = run(launcher_dir=args.dir, timeout=args.timeout, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
