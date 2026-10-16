#!/bin/bash
# auto-reload.sh —— Flask 自动拉取 + 重启守护脚本
#
# 用法（在 192.168.1.38 上执行）:
#   chmod +x auto-reload.sh
#   ./auto-reload.sh
#
# 脚本会持续运行:
#   1. 每 10 秒 git fetch，检查是否有新提交
#   2. 有新提交 → git pull → 同步模板表 → 停止旧 Flask → 启动新 Flask
#   3. Flask 进程崩溃 → 自动重启
#
# 停止: kill $(cat /var/www/mycompany.website/auto-reload.pid)

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
BRANCH=${BRANCH:-jan}                 # 监控的分支
FLASK_HOST=${FLASK_HOST:-0.0.0.0}
FLASK_PORT=${FLASK_PORT:-5000}
FLASK_DEBUG=${FLASK_DEBUG:-0}
# 192.168.1.38 是局域网调试部署，默认允许带缺页导出。
# .env 中显式配置 0 时仍会恢复导出死链拦截。
EXPORT_SKIP_LINK_CHECK=${EXPORT_SKIP_LINK_CHECK:-1}
LOG_FILE=${LOG_FILE:-flask_runtime.log}
VENV_DIR=${VENV_DIR:-.venv}
PID_FILE=${PID_FILE:-auto-reload.pid}

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
git config --global --add safe.directory "$PROJECT_DIR" 2>/dev/null || true

# 记录 PID
echo $$ > "$PID_FILE"

# ── 函数：准备运行环境 ───────────────────────────────────────────────
ensure_runtime() {
    cd "$PROJECT_DIR"
    if [ ! -d "$VENV_DIR" ]; then
        info "创建 Python 虚拟环境: $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi
    "$VENV_DIR/bin/python" -m pip install -r requirements.txt >/tmp/mycompany-pip-install.log 2>&1 || {
        warn "依赖安装失败，查看日志: tail -80 /tmp/mycompany-pip-install.log"
        return 1
    }
    if [ ! -f .env ]; then
        info "生成 .env"
        local secret
        secret=$("$VENV_DIR/bin/python" -c 'import secrets; print(secrets.token_urlsafe(48))')
        umask 077
        cat > .env <<ENV
SECRET_KEY=$secret
FLASK_HOST=$FLASK_HOST
FLASK_PORT=$FLASK_PORT
FLASK_DEBUG=$FLASK_DEBUG
ENV
    fi
    if ! grep -q '^EXPORT_SKIP_LINK_CHECK=' .env; then
        printf '\nEXPORT_SKIP_LINK_CHECK=%s\n' "$EXPORT_SKIP_LINK_CHECK" >> .env
    fi
}

# ── 函数：同步模板元信息到数据库 ───────────────────────────────────
scan_templates() {
    cd "$PROJECT_DIR"
    info "同步模板库到数据库..."
    set -a
    . ./.env
    set +a
    export FLASK_HOST FLASK_PORT FLASK_DEBUG EXPORT_SKIP_LINK_CHECK
    "$VENV_DIR/bin/python" -m flask --app run scan-templates || {
        warn "模板同步失败"
        return 1
    }
}

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
    ensure_runtime || return 1
    scan_templates || return 1
    info "启动 Flask (host=$FLASK_HOST port=$FLASK_PORT)..."
    cd "$PROJECT_DIR"
    set -a
    . ./.env
    set +a
    export FLASK_HOST FLASK_PORT FLASK_DEBUG EXPORT_SKIP_LINK_CHECK
    nohup "$VENV_DIR/bin/python" run.py > "$LOG_FILE" 2>&1 &
    local new_pid=$!
    sleep 3
    if kill -0 $new_pid 2>/dev/null; then
        local latest=$(git log -1 --format="%h %s")
        info "Flask 启动成功 PID=$new_pid | $latest"
        info "访问: http://192.168.1.38:$FLASK_PORT/"
    else
        warn "Flask 启动失败！查看日志: tail -80 $PROJECT_DIR/$LOG_FILE"
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
    flask_pid=$(pgrep -f "python.*run.py" 2>/dev/null | head -1 || true)
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
        if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
            warn "检测到服务器本地改动，先 stash 后再部署"
            git stash push --include-untracked -m "auto-stash before deploy $(date +%Y%m%d-%H%M%S)" >/dev/null
        fi
        git merge "origin/$BRANCH" --ff-only 2>/dev/null || {
            warn "fast-forward 失败，跳过本轮部署；请手动检查服务器 Git 状态"
            LAST_COMMIT=$(git rev-parse "$BRANCH" 2>/dev/null || echo "")
            continue
        }
        info "代码已更新: $(git log -1 --format='%h %s')"
        LAST_COMMIT="$NEW_COMMIT"
        start_flask
    fi
done
