#!/bin/bash
# deploy-to-remote.sh —— 在 192.168.1.38 (Ubuntu) 上执行的一键部署脚本
#
# 用法:
#   1. 将此脚本放到 192.168.1.38 机器上（U 盘 / scp / 微信 / 任何方式）
#   2. chmod +x deploy-to-remote.sh
#   3. ./deploy-to-remote.sh
#
# 脚本会自动:
#   - 搜索 mycompany.website 项目目录
#   - git pull 最新代码
#   - 重启 Flask 服务

set -e

# ── 配色 ─────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  mycompany.website 一键部署脚本${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# ── 1. 找到项目目录 ───────────────────────────────────────────────────
info "正在搜索项目目录..."
PROJECT_DIR=""
SEARCH_DIRS=("/var/www/mycompany.website" "/home/*/mycompany.website" "/opt/mycompany.website" "/home/*/projects/mycompany.website" "/srv/mycompany.website")

# 先用 common paths
for dir in "${SEARCH_DIRS[@]}"; do
    for match in $dir; do
        if [ -f "$match/run.py" ] && [ -d "$match/.git" ]; then
            PROJECT_DIR="$match"
            break 2
        fi
    done
done

# 如果没找到，全局搜索（限 /.git 目录定位）
if [ -z "$PROJECT_DIR" ]; then
    info "常见路径未找到，正在全局搜索（可能需要几秒）..."
    PROJECT_DIR=$(find / -maxdepth 5 -name "run.py" -path "*mycompany*" 2>/dev/null | head -1 | xargs dirname 2>/dev/null || true)
fi

if [ -z "$PROJECT_DIR" ]; then
    warn "未找到项目目录。请手动输入项目路径："
    read -p "项目路径: " PROJECT_DIR
    if [ ! -f "$PROJECT_DIR/run.py" ]; then
        error "路径无效: $PROJECT_DIR/run.py 不存在"
    fi
fi

info "项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR"

# ── 2. 检查 Python 环境 ───────────────────────────────────────────────
info "检查 Python 环境..."
if ! command -v python3 &>/dev/null; then
    error "未找到 python3，请先安装 Python"
fi
python3 --version

# 检查依赖
if ! python3 -c "import flask" &>/dev/null; then
    warn "flask 未安装，正在安装依赖..."
    pip3 install -r requirements.txt || pip install -r requirements.txt
fi

# ── 3. Git pull 最新代码 ──────────────────────────────────────────────
info "拉取最新代码..."
CURRENT_BRANCH=$(git branch --show-current)
info "当前分支: $CURRENT_BRANCH"

# 先 stash 本地改动（如果有）
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    warn "检测到本地改动，先 stash..."
    git stash push -m "auto-stash before deploy $(date +%Y%m%d-%H%M%S)"
fi

git pull origin "$CURRENT_BRANCH" || {
    warn "git pull 失败，尝试从 Gitea 拉取..."
    git pull origin "$CURRENT_BRANCH" --rebase || error "git pull 失败，请手动检查"
}

LATEST_COMMIT=$(git log -1 --format="%h %s")
info "最新提交: $LATEST_COMMIT"

# ── 4. 重启 Flask 服务 ───────────────────────────────────────────────
info "正在重启 Flask 服务..."

# 查找并停止旧的 Flask 进程
OLD_PIDS=$(pgrep -f "python.*run.py" 2>/dev/null || true)
if [ -n "$OLD_PIDS" ]; then
    info "停止旧进程: $OLD_PIDS"
    kill $OLD_PIDS 2>/dev/null || true
    sleep 2
    # 强杀残留
    OLD_PIDS2=$(pgrep -f "python.*run.py" 2>/dev/null || true)
    if [ -n "$OLD_PIDS2" ]; then
        warn "强制终止残留进程: $OLD_PIDS2"
        kill -9 $OLD_PIDS2 2>/dev/null || true
    fi
else
    info "未发现运行中的 Flask 进程"
fi

# ── 5. 重新启动 ──────────────────────────────────────────────────────
info "启动 Flask 服务..."

# 确保 .env 存在
if [ ! -f .env ]; then
    warn ".env 不存在，正在生成..."
    python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(48)}\nFLASK_HOST=0.0.0.0\nFLASK_PORT=5000\nFLASK_DEBUG=0')" > .env
    info ".env 已生成"
fi

# 后台启动
nohup python3 run.py > /tmp/mycompany-flask.log 2>&1 &
NEW_PID=$!
info "Flask 已启动，PID=$NEW_PID"

# 等待启动
sleep 2
if kill -0 $NEW_PID 2>/dev/null; then
    info "服务启动成功！"
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${GREEN}  部署完成！${NC}"
    echo -e "${CYAN}  访问地址: http://192.168.1.38:5000/${NC}"
    echo -e "${CYAN}  查看日志: tail -f /tmp/mycompany-flask.log${NC}"
    echo -e "${CYAN}  停止服务: kill $NEW_PID${NC}"
    echo -e "${CYAN}========================================${NC}"
else
    warn "进程可能未成功启动，请查看日志: /tmp/mycompany-flask.log"
    tail -20 /tmp/mycompany-flask.log
fi
