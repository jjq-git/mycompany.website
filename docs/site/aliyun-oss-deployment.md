# 阿里云 OSS 部署操作手册

本文记录把本项目生成的静态站部署到阿里云 OSS，并通过已经配置好的 CDN 自定义域名对外访问的操作流程。

当前流程是**人工发布流程**，适合站点 6，也可通过替换参数用于其他站点。后台“发布”按钮目前只负责构建，不会自动上传 OSS。

## 一、站点 6 的已确认配置

| 项目 | 值 |
| --- | --- |
| 站点 ID | `6` |
| 正式域名 | `https://www.dengtec.com` |
| OSS Bucket | `www-dengtec-com` |
| OSS 区域 | 北京 |
| OSS Endpoint | `https://oss-cn-beijing.aliyuncs.com` |
| 本地产物目录 | `output/6` |
| Bucket 目标目录 | 根目录 |
| 启用语言 | `zh-CN`、`zh-TW`、`en` |

内容更新时只需要重新构建并上传 OSS。不要重复创建 Bucket，也不要修改已经生效的 CDN、CNAME、DNS 或 HTTPS 证书。

## 二、发布所需条件

### 2.1 本机软件

- Python 和项目依赖已安装；
- 可以执行 `python -m flask --app run build-site 6`；
- 已安装阿里云 OSS Python SDK：

```powershell
python -m pip install oss2
```

验证：

```powershell
python -c "import oss2; print(oss2.__version__)"
```

### 2.2 阿里云资源

- 已存在 Bucket：`www-dengtec-com`；
- Bucket 位于北京区域；
- `www.dengtec.com` 已通过 CDN/CNAME 指向该 Bucket；
- HTTPS 证书已经生效；
- RAM 用户至少具有目标 Bucket 的以下权限：
  - 读取 Bucket 信息；
  - 列出对象；
  - 读取对象；
  - 上传和覆盖对象。

日常内容发布不需要删除权限。部署脚本不会删除 Bucket 中的对象。

### 2.3 发布凭据

使用专门的 OSS RAM 用户凭据，不要长期复用短信服务凭据，也不要使用阿里云主账号 AccessKey。

凭据不得：

- 写进本文档、代码或 Git；
- 粘贴到聊天记录；
- 直接写进 PowerShell 历史命令；
- 输出到部署日志。

本项目首选把凭据保存在以下本机私密文件中：

```text
.private/aliyun-oss.env
```

该目录已被 `.gitignore` 忽略。文件只保存在受信任的部署电脑上，内容使用无引号的
`KEY=value` 格式：

```dotenv
ALIYUN_OSS_ACCESS_KEY_ID=<实际 AccessKey ID>
ALIYUN_OSS_ACCESS_KEY_SECRET=<实际 AccessKey Secret>
```

每次部署前，在项目根目录执行下面的 PowerShell。脚本会先确认文件确实被 Git 忽略，
然后只把两个白名单变量加载到当前进程；检查结果只显示 `set` / `unset`，不会输出凭据：

```powershell
$credentialPath = ".private\aliyun-oss.env"

git check-ignore --quiet -- $credentialPath
if ($LASTEXITCODE -ne 0) {
    throw "$credentialPath 未被 Git 忽略，拒绝加载"
}
if (-not (Test-Path -LiteralPath $credentialPath)) {
    throw "缺少本机凭据文件：$credentialPath"
}

$credentialNames = @(
    "ALIYUN_OSS_ACCESS_KEY_ID",
    "ALIYUN_OSS_ACCESS_KEY_SECRET"
)

Get-Content -LiteralPath $credentialPath -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) {
        return
    }

    $parts = $line.Split("=", 2)
    if ($parts.Count -ne 2) {
        throw "凭据文件存在无效行"
    }

    $name = $parts[0].Trim()
    $value = $parts[1].Trim()
    if ($credentialNames -contains $name) {
        if ([string]::IsNullOrWhiteSpace($value)) {
            throw "$name 未填写"
        }
        Set-Item -LiteralPath "Env:$name" -Value $value
    }
}

$credentialNames | ForEach-Object {
    $value = [Environment]::GetEnvironmentVariable($_, "Process")
    "{0}={1}" -f $_, $(
        if ([string]::IsNullOrWhiteSpace($value)) { "unset" } else { "set" }
    )
}

if ($credentialNames | Where-Object {
    [string]::IsNullOrWhiteSpace(
        [Environment]::GetEnvironmentVariable($_, "Process")
    )
}) {
    throw "OSS 发布凭据未完整加载"
}
```

如果不使用本地私密文件，也可以选择在 Windows 用户环境变量中保存：

```powershell
[Environment]::SetEnvironmentVariable(
    "ALIYUN_OSS_ACCESS_KEY_ID",
    "实际 AccessKey ID",
    "User"
)
[Environment]::SetEnvironmentVariable(
    "ALIYUN_OSS_ACCESS_KEY_SECRET",
    "实际 AccessKey Secret",
    "User"
)
```

重新打开 PowerShell 后确认用户变量已设置，但不要打印变量值：

```powershell
@(
    "ALIYUN_OSS_ACCESS_KEY_ID",
    "ALIYUN_OSS_ACCESS_KEY_SECRET"
) | ForEach-Object {
    $value = [Environment]::GetEnvironmentVariable($_, "User")
    "{0}={1}" -f $_, $(if ([string]::IsNullOrWhiteSpace($value)) { "unset" } else { "set" })
}
```

把用户环境变量加载到当前 PowerShell：

```powershell
$env:ALIYUN_OSS_ACCESS_KEY_ID = [Environment]::GetEnvironmentVariable(
    "ALIYUN_OSS_ACCESS_KEY_ID",
    "User"
)
$env:ALIYUN_OSS_ACCESS_KEY_SECRET = [Environment]::GetEnvironmentVariable(
    "ALIYUN_OSS_ACCESS_KEY_SECRET",
    "User"
)
```

## 三、每次发布使用的参数

在项目根目录打开 PowerShell：

```powershell
Set-Location "F:\dengtec\mycompany.website11"

$env:DEPLOY_SITE_ID = "6"
$env:DEPLOY_DOMAIN = "www.dengtec.com"
$env:DEPLOY_BUCKET = "www-dengtec-com"
$env:DEPLOY_ENDPOINT = "https://oss-cn-beijing.aliyuncs.com"
$env:DEPLOY_OUTPUT = (Resolve-Path "output").Path + "\6"
```

如果部署其他站点，必须同时替换站点 ID、正式域名、Bucket、Endpoint 和产物目录，不能只改其中一项。

## 四、正式构建

不要直接上传后台预览产物。发布前必须重新执行正式构建：

```powershell
python -m flask --app run build-site $env:DEPLOY_SITE_ID
```

成功时应显示：

```text
已生成: F:\dengtec\mycompany.website11\output\6
```

统计产物：

```powershell
$files = Get-ChildItem -LiteralPath $env:DEPLOY_OUTPUT -Recurse -File

[pscustomobject]@{
    Files = $files.Count
    MiB = [math]::Round(
        (($files | Measure-Object Length -Sum).Sum / 1MB),
        2
    )
} | Format-List
```

不要为了“清理”而手动删除整个 `output/`。构建命令负责生成当前站点的正式产物。

## 五、发布前阻断检查

### 5.1 禁止预览地址进入正式产物

```powershell
$previewMatches = rg -n "/preview/|/_preview/" $env:DEPLOY_OUTPUT `
    -g "*.html" -g "*.xml" -g "*.txt"

if ($previewMatches) {
    $previewMatches
    throw "正式产物包含 preview 地址，停止部署。"
}
```

### 5.2 检查正式域名、canonical、hreflang 和 sitemap

```powershell
@'
from pathlib import Path
import os
import re
import xml.etree.ElementTree as ET

root = Path(os.environ["DEPLOY_OUTPUT"])
domain = os.environ["DEPLOY_DOMAIN"]
origin = f"https://{domain}/"
issues = []
indexed_pages = 0

for path in root.rglob("*.html"):
    relative = path.relative_to(root).as_posix()

    # 根语言跳转页和嵌入式媒体包不是可索引内容页。
    if relative == "index.html" or relative.startswith("assets/media-packages/"):
        continue

    text = path.read_text(encoding="utf-8", errors="replace")
    canonical = re.findall(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',
        text,
        re.I,
    )

    if len(canonical) != 1:
        issues.append(f"{relative}: canonical 数量为 {len(canonical)}")
        continue

    indexed_pages += 1
    if not canonical[0].startswith(origin):
        issues.append(f"{relative}: canonical 不是正式域名")

    for href in re.findall(
        r'<link[^>]+rel=["\']alternate["\'][^>]+'
        r'hreflang=["\'][^"\']+["\'][^>]+href=["\']([^"\']+)',
        text,
        re.I,
    ):
        if not href.startswith(origin):
            issues.append(f"{relative}: hreflang 不是正式域名")

sitemap = root / "sitemap.xml"
if not sitemap.exists():
    issues.append("缺少 sitemap.xml")
    sitemap_urls = []
else:
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls = [
        node.text
        for node in ET.parse(sitemap).findall(".//s:loc", ns)
    ]
    for url in sitemap_urls:
        if not url.startswith(origin):
            issues.append(f"sitemap 包含错误域名：{url}")

print(f"indexed_pages={indexed_pages}")
print(f"sitemap_urls={len(sitemap_urls)}")
print(f"issues={len(issues)}")

for issue in issues[:50]:
    print(issue)

if issues:
    raise SystemExit(2)
'@ | python -
```

任何阻断检查失败时都不要继续上传，应先修复构建配置或页面数据。

## 六、只读确认 OSS

第一次部署、凭据轮换或 Bucket 参数变化后执行：

```powershell
@'
import os
import oss2

auth = oss2.Auth(
    os.environ["ALIYUN_OSS_ACCESS_KEY_ID"],
    os.environ["ALIYUN_OSS_ACCESS_KEY_SECRET"],
)
bucket = oss2.Bucket(
    auth,
    os.environ["DEPLOY_ENDPOINT"],
    os.environ["DEPLOY_BUCKET"],
    connect_timeout=30,
)

bucket.get_bucket_info()
count = 0
size = 0

for item in oss2.ObjectIterator(bucket):
    count += 1
    size += item.size

print(
    f"bucket={os.environ['DEPLOY_BUCKET']} "
    f"objects={count} bytes={size}"
)
print("read_only_auth=ok")
'@ | python -
```

如果返回区域错误，先核对 Endpoint。站点 6 使用北京区域，不是杭州区域。

## 七、备份将被覆盖的线上对象

每次上传前都执行差异备份。备份包括：

- 完整线上对象清单；
- 将被覆盖的旧对象；
- 本次新增对象列表；
- 线上多余对象列表；
- ZIP 压缩包。

脚本只读取 OSS，不修改线上对象：

```powershell
@'
from pathlib import Path
from datetime import datetime
import concurrent.futures
import hashlib
import json
import os
import shutil
import oss2

root = Path(os.environ["DEPLOY_OUTPUT"])
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_root = (
    Path("output")
    / "_deploy_backups"
    / f"site{os.environ['DEPLOY_SITE_ID']}"
    / stamp
).resolve()
objects_root = backup_root / "objects"
objects_root.mkdir(parents=True, exist_ok=False)

auth = oss2.Auth(
    os.environ["ALIYUN_OSS_ACCESS_KEY_ID"],
    os.environ["ALIYUN_OSS_ACCESS_KEY_SECRET"],
)
bucket = oss2.Bucket(
    auth,
    os.environ["DEPLOY_ENDPOINT"],
    os.environ["DEPLOY_BUCKET"],
    connect_timeout=30,
)

remote = {
    item.key: {
        "etag": item.etag.strip('"').lower(),
        "size": item.size,
        "last_modified": item.last_modified,
    }
    for item in oss2.ObjectIterator(bucket)
}
local = {
    path.relative_to(root).as_posix(): path
    for path in root.rglob("*")
    if path.is_file()
}

changed = []
for key, path in local.items():
    old = remote.get(key)
    if old is None:
        continue
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    if old["size"] != path.stat().st_size or old["etag"] != digest:
        changed.append(key)

new = sorted(set(local) - set(remote))
stale = sorted(set(remote) - set(local))
manifest = {
    "created_at": datetime.now().astimezone().isoformat(),
    "bucket": os.environ["DEPLOY_BUCKET"],
    "endpoint": os.environ["DEPLOY_ENDPOINT"],
    "remote_objects": remote,
    "changed_keys": sorted(changed),
    "new_keys": new,
    "stale_remote_keys": stale,
}
(backup_root / "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

def download(key):
    target = objects_root / Path(key)
    target.parent.mkdir(parents=True, exist_ok=True)
    result = bucket.get_object_to_file(key, str(target))
    if result.status != 200:
        raise RuntimeError(f"{key}: HTTP {result.status}")
    return target.stat().st_size

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    sizes = list(pool.map(download, changed))

archive = shutil.make_archive(
    str(backup_root),
    "zip",
    root_dir=backup_root,
)
print(f"backup_dir={backup_root}")
print(f"backup_archive={archive}")
print(
    f"changed={len(changed)} new={len(new)} "
    f"stale_remote={len(stale)} backup_bytes={sum(sizes)}"
)
'@ | python -
```

确认脚本输出了 `backup_archive` 后才能继续。备份默认位于：

```text
output/_deploy_backups/site6/<时间>.zip
```

`stale_remote` 只做报告，不自动删除。

## 八、上传正式产物

下面的脚本沿用 2026-07-22 和 2026-07-23 已验证成功的发布策略：

- 上传全部正式产物；
- 覆盖同名对象；
- 不删除其他对象；
- HTML、XML、TXT 禁止缓存；
- CSS、JS、图片等静态资源长期缓存；
- 上传后检查关键对象大小。

```powershell
@'
from pathlib import Path
import concurrent.futures
import mimetypes
import os
import threading
import oss2

root = Path(os.environ["DEPLOY_OUTPUT"])
endpoint = os.environ["DEPLOY_ENDPOINT"]
bucket_name = os.environ["DEPLOY_BUCKET"]

for content_type, suffix in (
    ("text/css", ".css"),
    ("application/javascript", ".js"),
    ("application/wasm", ".wasm"),
    ("image/webp", ".webp"),
    ("image/svg+xml", ".svg"),
    ("video/mp4", ".mp4"),
    ("application/xml", ".xml"),
):
    mimetypes.add_type(content_type, suffix)

files = sorted(path for path in root.rglob("*") if path.is_file())
if not files:
    raise SystemExit("没有找到构建产物")

auth = oss2.Auth(
    os.environ["ALIYUN_OSS_ACCESS_KEY_ID"],
    os.environ["ALIYUN_OSS_ACCESS_KEY_SECRET"],
)
thread_state = threading.local()

def client():
    if not hasattr(thread_state, "bucket"):
        thread_state.bucket = oss2.Bucket(
            auth,
            endpoint,
            bucket_name,
            connect_timeout=30,
        )
    return thread_state.bucket

def upload(path):
    key = path.relative_to(root).as_posix()
    headers = {
        "Content-Type": (
            mimetypes.guess_type(path.name)[0]
            or "application/octet-stream"
        )
    }
    if path.suffix.lower() in (".html", ".xml", ".txt"):
        headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    else:
        headers["Cache-Control"] = "public, max-age=31536000"

    result = client().put_object_from_file(
        key,
        str(path),
        headers=headers,
    )
    if result.status not in (200, 201):
        raise RuntimeError(f"{key}: HTTP {result.status}")
    return path.stat().st_size

print(
    f"Uploading {len(files)} files "
    f"to oss://{bucket_name}/ ...",
    flush=True,
)
completed = 0
uploaded_bytes = 0
errors = []

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    future_map = {
        pool.submit(upload, path): path
        for path in files
    }
    for future in concurrent.futures.as_completed(future_map):
        path = future_map[future]
        try:
            uploaded_bytes += future.result()
            completed += 1
            if completed % 100 == 0 or completed == len(files):
                print(
                    f"progress {completed}/{len(files)} "
                    f"({uploaded_bytes / 1024 / 1024:.1f} MiB)",
                    flush=True,
                )
        except Exception as exc:
            errors.append((path, exc))
            if len(errors) <= 10:
                print(
                    f"ERROR {path.relative_to(root)}: "
                    f"{type(exc).__name__}: {exc}",
                    flush=True,
                )

if errors:
    raise SystemExit(f"有 {len(errors)} 个文件上传失败")

bucket = oss2.Bucket(
    auth,
    endpoint,
    bucket_name,
    connect_timeout=30,
)
for key in (
    "index.html",
    "static/css/main.css",
    "zh-CN/index.html",
    "zh-TW/index.html",
    "en/index.html",
    "sitemap.xml",
    "llms.txt",
):
    local_path = root / Path(key)
    head = bucket.head_object(key)
    remote_size = int(head.headers.get("Content-Length", "-1"))
    if remote_size != local_path.stat().st_size:
        raise SystemExit(
            f"{key} 验证失败："
            f"local={local_path.stat().st_size}, remote={remote_size}"
        )
    print(f"verified {key} ({remote_size} bytes)", flush=True)

print("UPLOAD_COMPLETE", flush=True)
'@ | python -
```

只有出现 `UPLOAD_COMPLETE` 才表示 OSS 上传完成。

## 九、通过正式域名验证

至少检查根入口、三种语言首页、sitemap 和 llms.txt：

```powershell
@(
    "https://www.dengtec.com/",
    "https://www.dengtec.com/zh-CN/",
    "https://www.dengtec.com/zh-TW/",
    "https://www.dengtec.com/en/",
    "https://www.dengtec.com/sitemap.xml",
    "https://www.dengtec.com/llms.txt"
) | ForEach-Object {
    curl.exe -sS -I --max-time 30 $_
}
```

预期：

- 全部返回 HTTP 200；
- HTML、sitemap、llms.txt 的 `Cache-Control` 为
  `no-cache, no-store, must-revalidate`；
- 页面 canonical 和 hreflang 使用 `https://www.dengtec.com/`；
- sitemap 不包含 localhost、OSS 域名或 `/preview/`；
- 三种语言首页内容正常；
- 新增图片可以通过正式域名打开。

需要检查页面实际内容时，不要只看 HTTP 头：

```powershell
curl.exe -sS -L --max-time 30 "https://www.dengtec.com/en/"
```

## 十、什么时候需要刷新 CDN

以下情况不需要额外刷新：

- 只修改 HTML、XML、TXT；
- 新图片使用新的文件名；
- CSS、JS、旧图片内容和对象路径均未变化。

以下情况需要在阿里云 CDN 控制台刷新对应 URL：

- 同一路径的 CSS、JS 或图片内容发生变化；
- 正式域名仍返回旧文件，但 OSS 直连地址已经是新文件；
- 调整了缓存规则。

优先刷新准确的文件 URL，不要无原因执行全站目录刷新。

## 十一、回滚

发生线上错误时：

1. 立即停止后续上传；
2. 找到本次发布前生成的备份目录；
3. 将 `objects/` 中的旧对象按原路径重新上传；
4. 不自动删除本次新增对象；
5. 重新执行正式域名验证；
6. 如果同路径静态资源被缓存，再刷新对应 CDN URL。

备份中的 `manifest.json` 记录：

- `changed_keys`：需要恢复的旧对象；
- `new_keys`：本次新增对象；
- `stale_remote_keys`：发布前线上独有对象；
- `remote_objects`：发布前完整对象元数据。

新增对象通常可以暂时保留，因为恢复后的旧 HTML 不再引用它们。确需删除时必须先人工核对 `new_keys`，不要运行递归删除命令。

## 十二、常见问题

### `NoSuchBucket` 或区域错误

检查 Bucket 和 Endpoint 是否匹配。站点 6 是：

```text
www-dengtec-com
https://oss-cn-beijing.aliyuncs.com
```

### `AccessDenied`

检查：

- 当前 PowerShell 是否加载了 OSS 环境变量；
- RAM 用户是否有目标 Bucket 的 List/Get/Put 权限；
- AccessKey 是否已被禁用或轮换；
- Bucket Policy 是否限制了该 RAM 用户。

### OSS 已更新，正式域名仍是旧内容

先比较 OSS 直连地址和正式域名：

```powershell
curl.exe -sS -I `
    "https://www-dengtec-com.oss-cn-beijing.aliyuncs.com/index.html"
curl.exe -sS -I `
    "https://www.dengtec.com/index.html"
```

如果只有正式域名是旧内容，检查 CDN 缓存并刷新准确 URL。

### canonical 出现 `/preview/`

说明上传的不是正式构建产物，或构建时正式域名配置错误。停止发布，重新执行第四、第五节，不能通过字符串替换直接修改生成后的 HTML。

## 十三、站点 6 最近一次成功发布基线

2026-07-23 的成功结果：

| 检查项 | 结果 |
| --- | --- |
| 构建产物 | 1,024 个文件，约 159 MiB |
| sitemap URL | 321 个 |
| 线上原对象 | 1,022 个 |
| 完全相同 | 793 个 |
| 覆盖更新 | 229 个 |
| 新增 | 2 个 |
| 删除 | 0 个 |
| 正式域名内容哈希验证 | 231/231 通过 |
| 根入口和三种语言首页 | HTTP 200 |
| sitemap、llms.txt | HTTP 200 |

文件数量会随内容变化，不能把上述数量作为永久硬编码判断；它只用于下次发布时识别明显异常。
