#!/bin/bash
# auto-reload.sh —— Flask 自动拉取 + 重启守护脚本
#
# 用法（在 192.168.1.38 上执行）:
#   chmod +x auto-reload.sh
#   ./auto-reload.sh
#
# 脚本会持续运行:
#   1. 每 10 秒 git fetch，检查是否有新提交
#   2. 有新提交 → git pull → 停止旧 Flask → 启动新 Flask
#   3. Flask 进程崩溃 → 自动重启
#
# 停止: kill $(cat /tmp/mycompany-auto-reload.pid)

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[auto-reload]${NC} $(date '+%H:%M:%S') $*"; }
warn()  { echo -e "${YELLOW}[auto-reload]${NC} $(date '+%H:%M:%S') $*"; }

# ── 配置 ─────────────────────────────────────────────────────────────
POLL_INTERVAL=${POLL_INTERVAL:-10}      # 检查间隔（秒）
BRANCH=${BRANCH:-dev-20260527}         # 监控的分支
FLASK_HOST=${FLASK_HOST:-0.0.0.0}
FLASK_PORT=${FLASK_PORT:-5000}

# ── 找到项目目录 ──────────────────────────────────────────────────────
PROJECT_DIR=""
SEARCH_DIRS=("/var/www/mycompany.website" "/home/*/mycompany.website" "/opt/mycompany.website")
for dir in "${SEARCH_DIRS[@]}"; do
    for match in $dir; do
        if [ -f "$match/run.py" ] && [ -d "$match/.git" ]; then
            PROJECT_DIR="$match"
            break 2
        fi
    done
done
if [ -z "$PROJECT_DIR" ]; then
    echo "未找到项目目录，请手动输入:"
    read -p "项目路径: " PROJECT_DIR
    if [ ! -f "$PROJECT_DIR/run.py" ]; then
        echo "路径无效"; exit 1
    fi
fi

info "项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR"

# 记录 PID
echo $$ > /tmp/mycompany-auto-reload.pid

# ── 函数：停止旧 Flask 进程 ───────────────────────────────────────────
stop_flask() {
    local pids=$(pgrep -f "python.*run.py" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        info "停止 Flask 进程: $pids"
        kill $pids 2>/dev/null || true
        sleep 2
        # 强杀残留
        pids=$(pgrep -f "python.*run.py" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            warn "强制终止: $pids"
            kill -9 $pids 2>/dev/null || true
        fi
    fi
}

# ── 函数：启动 Flask ─────────────────────────────────────────────────
start_flask() {
    stop_flask
    info "启动 Flask (host=$FLASK_HOST port=$FLASK_PORT)..."
    cd "$PROJECT_DIR"
    nohup python3 run.py >> /tmp/mycompany-flask.log 2>&1 &
    local new_pid=$!
    sleep 3
    if kill -0 $new_pid 2>/dev/null; then
        local latest=$(git log -1 --format="%h %s")
        info "Flask 启动成功 PID=$new_pid | $latest"
        info "访问: http://192.168.1.38:$FLASK_PORT/"
    else
        warn "Flask 启动失败！查看日志: tail /tmp/mycompany-flask.log"
    fi
}

# ── 首次启动 ─────────────────────────────────────────────────────────
git fetch origin "$BRANCH" 2>/dev/null || warn "git fetch 失败"
start_flask

# ── 主循环：监控 + 自动重启 ──────────────────────────────────────────
LAST_COMMIT=$(git rev-parse "$BRANCH" 2>/dev/null || echo "")

info "进入监控循环（每 ${POLL_INTERVAL}s 检查一次）"
info "当前 HEAD: ${LAST_COMMIT:0:7}"

while true; do
    sleep "$POLL_INTERVAL"

    # 检查 Flask 是否还在运行
    local flask_pid=$(pgrep -f "python.*run.py" 2>/dev/null | head -1 || true)
    if [ -z "$flask_pid" ]; then
        warn "Flask 进程已退出，自动重启..."
        start_flask
        LAST_COMMIT=$(git rev-parse "$BRANCH" 2>/dev/null || echo "")
        continue
    fi

    # git fetch 检查新提交
    if ! git fetch origin "$BRANCH" 2>/dev/null; then
        continue  # 网络错误，跳过本轮
    fi

    NEW_COMMIT=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "")

    if [ -n "$NEW_COMMIT" ] && [ "$NEW_COMMIT" != "$LAST_COMMIT" ]; then
        info "检测到新提交: ${NEW_COMMIT:0:7} (旧: ${LAST_COMMIT:0:7})"
        git merge "origin/$BRANCH" --ff-only 2>/dev/null || {
            warn "fast-forward 失败，尝试 reset..."
            git reset --hard "origin/$BRANCH"
        }
        info "代码已更新: $(git log -1 --format='%h %s')"
        LAST_COMMIT="$NEW_COMMIT"
        start_flask
    fi
done
