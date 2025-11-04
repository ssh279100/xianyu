#!/usr/bin/env python3
"""Simple launcher for Start.py.

Usage:
    python sb.py start   # 后台启动服务
    python sb.py stop    # 停止服务
    python sb.py status  # 查看状态
    python sb.py log     # 实时查看日志（按 Ctrl+C 退出）

环境变量已经在脚本内写死，如需调整，在下方 `COOKIE_CLOUD_*` 常量修改即可。
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"
START_SCRIPT = PROJECT_ROOT / "Start.py"
PID_FILE = PROJECT_ROOT / "start.pid"
LOG_FILE = PROJECT_ROOT / "realtime.log"

# 优先从环境变量读取 CookieCloud 配置（部署脚本会提前导入 .env）
COOKIE_CLOUD_HOST = os.getenv("COOKIE_CLOUD_HOST", "").strip()
COOKIE_CLOUD_UUID = os.getenv("COOKIE_CLOUD_UUID", "").strip()
COOKIE_CLOUD_PASSWORD = os.getenv("COOKIE_CLOUD_PASSWORD", "").strip()


def read_pid() -> int | None:
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except ValueError:
            return None
    return None


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    else:
        return True


def start() -> None:
    pid = read_pid()
    if pid and is_running(pid):
        print(f"Start.py 已在运行 (PID={pid})")
        return

    if not VENV_PYTHON.exists():
        sys.exit(f"未找到虚拟环境 Python: {VENV_PYTHON}")

    env = os.environ.copy()

    cookiecloud_env = {
        "COOKIE_CLOUD_HOST": COOKIE_CLOUD_HOST,
        "COOKIE_CLOUD_UUID": COOKIE_CLOUD_UUID,
        "COOKIE_CLOUD_PASSWORD": COOKIE_CLOUD_PASSWORD,
    }

    # 仅在值非空时覆盖，便于通过 shell 手动导出环境变量
    env.update({k: v for k, v in cookiecloud_env.items() if v})

    # 确保日志文件存在
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_fp = LOG_FILE.open("a", encoding="utf-8")

    cmd = [str(VENV_PYTHON), str(START_SCRIPT)]
    process = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,  # 让进程独立于当前终端
    )
    PID_FILE.write_text(str(process.pid))
    print(f"Start.py 已启动，PID={process.pid}，日志写入 {LOG_FILE}")


def stop() -> None:
    pid = read_pid()
    if not pid:
        print("未找到 PID 文件，服务可能未运行。")
        return

    if not is_running(pid):
        print("进程不存在，清理 PID 文件。")
        PID_FILE.unlink(missing_ok=True)
        return

    os.killpg(pid, signal.SIGTERM)
    print(f"已发送终止信号到 PID {pid}，等待退出...")

    # 简单等待几秒钟
    for _ in range(10):
        if not is_running(pid):
            break
        time.sleep(0.5)

    if is_running(pid):
        print("进程尚未退出，尝试强制终止。")
        os.killpg(pid, signal.SIGKILL)

    PID_FILE.unlink(missing_ok=True)
    print("服务已停止。")


def status() -> None:
    pid = read_pid()
    if pid and is_running(pid):
        print(f"Start.py 正在运行 (PID={pid})。日志文件: {LOG_FILE}")
    else:
        print("Start.py 未运行。")


def tail_log() -> None:
    if not LOG_FILE.exists():
        print("日志文件不存在。")
        return

    print(f"实时查看 {LOG_FILE}，按 Ctrl+C 退出。")
    try:
        with LOG_FILE.open("r", encoding="utf-8", errors="ignore") as fp:
            fp.seek(0, os.SEEK_END)
            while True:
                line = fp.readline()
                if not line:
                    time.sleep(0.5)
                else:
                    print(line, end="")
    except KeyboardInterrupt:
        print("\n已退出日志查看。")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start.py 管理脚本")
    parser.add_argument("command", choices=["start", "stop", "status", "log"], help="操作命令")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "start":
        start()
    elif args.command == "stop":
        stop()
    elif args.command == "status":
        status()
    elif args.command == "log":
        tail_log()


if __name__ == "__main__":
    main()

