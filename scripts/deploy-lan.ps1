# deploy-lan.ps1 —— 部署到局域网 (http://192.168.1.38:5000)
#
# 用法:
#   .\scripts\deploy-lan.ps1              # 前台启动（Ctrl+C 停止）
#   .\scripts\deploy-lan.ps1 -Background  # 后台启动
#   .\scripts\deploy-lan.ps1 -Stop        # 停止后台进程
#   .\scripts\deploy-lan.ps1 -Status      # 查看后台进程状态
#
# 启动前会自动检查依赖、生成 .env（如缺失），然后启动 Flask 开发服务器。
# 注意: 这是局域网内部使用的开发部署，不适合公网暴露。

param(
    [switch]$Background,  # 后台运行
    [switch]$Stop,        # 停止后台进程
    [switch]$Status       # 查看状态
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..").Path
$EnvFile = "$ProjectRoot\.env"
$PidFile = "$ProjectRoot\.deploy-lan.pid"
$LogFile = "$ProjectRoot\.deploy-lan.log"
$TargetHost = '0.0.0.0'   # 监听所有网卡，局域网内可通过 http://192.168.1.38:5000 访问
$TargetPort = 5000

# ── 函数：检查 Python 环境 ──────────────────────────────────────────
function Test-PythonEnv {
    try {
        $pyVer = python --version 2>&1
        Write-Host "[OK] Python 已就绪: $pyVer" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
        exit 1
    }

    # 检查关键依赖是否已安装
    $missing = @()
    $deps = @('flask', 'python-dotenv', 'pyyaml', 'Pillow')
    foreach ($dep in $deps) {
        $result = python -c "import $($dep -replace '-','_')" 2>&1
        if ($LASTEXITCODE -ne 0) {
            $missing += $dep
        }
    }
    if ($missing.Count -gt 0) {
        Write-Host "[WARN] 缺少依赖: $($missing -join ', ')，将自动安装..." -ForegroundColor Yellow
        pip install -r "$ProjectRoot\requirements.txt"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] 依赖安装失败" -ForegroundColor Red
            exit 1
        }
        Write-Host "[OK] 依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "[OK] Python 依赖已就绪" -ForegroundColor Green
    }
}

# ── 函数：初始化 .env（缺失时生成） ─────────────────────────────────
function Initialize-EnvFile {
    if (-not (Test-Path $EnvFile)) {
        Write-Host "[INFO] .env 不存在，自动生成..." -ForegroundColor Yellow

        # 生成随机 SECRET_KEY
        $secretKey = python -c "import secrets; print(secrets.token_urlsafe(48))"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] 无法生成 SECRET_KEY" -ForegroundColor Red
            exit 1
        }

        @"
# 由 deploy-lan.ps1 自动生成 ($(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
SECRET_KEY=$secretKey
FLASK_HOST=$TargetHost
FLASK_PORT=$TargetPort
FLASK_DEBUG=0
"@ | Out-File -FilePath $EnvFile -Encoding utf8

        Write-Host "[OK] .env 已生成（SECRET_KEY 随机创建）" -ForegroundColor Green
    } else {
        Write-Host "[OK] .env 已存在" -ForegroundColor Green

        # 确保 .env 中有 FLASK_HOST 和 FLASK_PORT
        $content = Get-Content $EnvFile -Raw -Encoding utf8
        $updated = $false

        if ($content -notmatch 'FLASK_HOST=') {
            Add-Content $EnvFile "`nFLASK_HOST=$TargetHost" -Encoding utf8
            $updated = $true
        }
        if ($content -notmatch 'FLASK_PORT=') {
            Add-Content $EnvFile "`nFLASK_PORT=$TargetPort" -Encoding utf8
            $updated = $true
        }

        if ($updated) {
            Write-Host "[INFO] 已补充 FLASK_HOST / FLASK_PORT 到 .env" -ForegroundColor Yellow
        }
    }
}

# ── 函数：停止后台进程 ──────────────────────────────────────────────
function Stop-BackgroundServer {
    if (-not (Test-Path $PidFile)) {
        Write-Host "[INFO] 未找到后台进程 PID 文件，服务可能未在运行" -ForegroundColor Yellow
        return
    }
    $pid = Get-Content $PidFile
    try {
        $proc = Get-Process -Id $pid -ErrorAction Stop
        Write-Host "[INFO] 正在停止进程 PID=$pid ($($proc.ProcessName))..." -ForegroundColor Yellow
        $proc.Kill()
        $proc.WaitForExit(5000)
        Write-Host "[OK] 进程已停止" -ForegroundColor Green
    } catch {
        Write-Host "[INFO] 进程 PID=$pid 已不存在" -ForegroundColor Yellow
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

# ── 函数：查看状态 ──────────────────────────────────────────────────
function Show-Status {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile
        try {
            $proc = Get-Process -Id $pid -ErrorAction Stop
            Write-Host "[STATUS] 服务运行中  PID=$pid  进程=$($proc.ProcessName)  启动时间=$($proc.StartTime)" -ForegroundColor Green
            Write-Host "         地址: http://192.168.1.38:$TargetPort" -ForegroundColor Green
        } catch {
            Write-Host "[STATUS] PID 文件存在但进程已停止 (PID=$pid)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[STATUS] 服务未运行" -ForegroundColor Yellow
    }
}

# ── 函数：前台启动 ──────────────────────────────────────────────────
function Start-ForegroundServer {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  启动 Flask 开发服务器" -ForegroundColor Cyan
    Write-Host "  局域网地址: http://192.168.1.38:$TargetPort" -ForegroundColor Cyan
    Write-Host "  本机地址:   http://127.0.0.1:$TargetPort" -ForegroundColor Cyan
    Write-Host "  按 Ctrl+C 停止" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    $env:FLASK_HOST = $TargetHost
    $env:FLASK_PORT = $TargetPort
    $env:FLASK_DEBUG = '0'

    Set-Location $ProjectRoot
    python run.py
}

# ── 函数：后台启动 ──────────────────────────────────────────────────
function Start-BackgroundServer {
    # 先停掉已有的
    if (Test-Path $PidFile) {
        Stop-BackgroundServer
        Start-Sleep -Seconds 1
    }

    Write-Host "[INFO] 以后台方式启动..." -ForegroundColor Yellow

    $env:FLASK_HOST = $TargetHost
    $env:FLASK_PORT = $TargetPort
    $env:FLASK_DEBUG = '0'

    # 创建启动脚本
    $launcherScript = @"
Set-Location '$ProjectRoot'
python run.py 2>&1
"@

    $launcherPath = "$ProjectRoot\.deploy-lan-launcher.ps1"
    $launcherScript | Out-File -FilePath $launcherPath -Encoding utf8

    # 启动后台 PowerShell 进程
    $proc = Start-Process powershell.exe -ArgumentList "-NoProfile -WindowStyle Hidden -File `"$launcherPath`"" -PassThru -WindowStyle Hidden
    $proc.Id | Out-File -FilePath $PidFile -Encoding utf8

    Start-Sleep -Seconds 3

    # 确认进程还活着
    try {
        $check = Get-Process -Id $proc.Id -ErrorAction Stop
        Write-Host "[OK] 服务已后台启动  PID=$($proc.Id)" -ForegroundColor Green
        Write-Host "     地址: http://192.168.1.38:$TargetPort" -ForegroundColor Green
        Write-Host "     日志: $LogFile" -ForegroundColor Green
        Write-Host "     停止: .\scripts\deploy-lan.ps1 -Stop" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] 进程启动后立即退出，请检查" -ForegroundColor Red
    }
}

# ══════════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════════

Set-Location $ProjectRoot

if ($Stop) {
    Stop-BackgroundServer
    exit 0
}

if ($Status) {
    Show-Status
    exit 0
}

# 启动前检查
Test-PythonEnv
Initialize-EnvFile

if ($Background) {
    Start-BackgroundServer
} else {
    Start-ForegroundServer
}
