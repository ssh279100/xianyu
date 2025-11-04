#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
APP_NAME="xianyu-auto-reply"
PYTHON_BIN=${PYTHON_BIN:-python3}

echo "[${APP_NAME}] 使用目录: ${SCRIPT_DIR}"

if [ ! -f "${SCRIPT_DIR}/requirements.txt" ]; then
  echo "[${APP_NAME}] 请在项目根目录运行本脚本。当前未找到 requirements.txt。" >&2
  exit 1
fi

if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  if [ "${ID:-}" != "ubuntu" ]; then
    echo "[${APP_NAME}] 警告: 检测到非 Ubuntu 系统 (${ID:-unknown})，脚本仍会继续，但可能失败。"
  fi
fi

if command -v sudo >/dev/null 2>&1 && [ "${EUID:-0}" -ne 0 ]; then
  SUDO="sudo"
else
  SUDO=""
fi

echo "[${APP_NAME}] 更新 apt 包索引..."
${SUDO} apt-get update -y

echo "[${APP_NAME}] 安装依赖: git, ${PYTHON_BIN}, python3-venv, python3-pip..."
${SUDO} apt-get install -y git ${PYTHON_BIN} python3-venv python3-pip curl

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[${APP_NAME}] 未找到 ${PYTHON_BIN}，请检查系统 Python 安装。" >&2
  exit 1
fi

if [ -f "${SCRIPT_DIR}/.env" ]; then
  echo "[${APP_NAME}] 从 .env 加载环境变量"
  set -a
  # shellcheck disable=SC1090
  source "${SCRIPT_DIR}/.env"
  set +a
fi

mkdir -p "${SCRIPT_DIR}/data" "${SCRIPT_DIR}/logs" "${SCRIPT_DIR}/backups"

if [ ! -d "${SCRIPT_DIR}/venv" ]; then
  echo "[${APP_NAME}] 创建虚拟环境"
  "${PYTHON_BIN}" -m venv "${SCRIPT_DIR}/venv"
fi

echo "[${APP_NAME}] 升级 pip"
"${SCRIPT_DIR}/venv/bin/pip" install --upgrade pip wheel setuptools

echo "[${APP_NAME}] 安装项目依赖"
"${SCRIPT_DIR}/venv/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt"

echo "[${APP_NAME}] 启动服务 (sb.py start)"
"${SCRIPT_DIR}/venv/bin/python" "${SCRIPT_DIR}/sb.py" start

echo "[${APP_NAME}] 部署完成。查看状态: ${SCRIPT_DIR}/venv/bin/python sb.py status"
echo "[${APP_NAME}] 查看实时日志: ${SCRIPT_DIR}/venv/bin/python sb.py log"

