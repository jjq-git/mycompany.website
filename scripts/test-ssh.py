"""测试 WSL 中 SSH 连接到 192.168.1.38 的各种凭据组合。"""
import subprocess, sys

host = "192.168.1.38"
users = ["nx", "ubuntu", "root", "jjq", "admin", "git", "web", "flask", "mycompany", "deploy", "www-data"]
password = "Dengtec.COM"  # 用户提供的密码

def run_wsl(cmd):
    """在 WSL 中执行命令并返回 (returncode, stdout)。"""
    r = subprocess.run(["wsl", "-d", "Ubuntu", "--", "bash", "-c", cmd],
                       capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

# ── 1. 先确认 sshpass 可用 ──
rc, out, err = run_wsl("which sshpass")
print(f"sshpass: {out}")

# ── 2. 用 sshpass + 密码试所有用户名 ──
print("\n=== 密码认证 ===")
for u in users:
    rc, out, err = run_wsl(
        f"sshpass -p '{password}' ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no {u}@{host} 'echo OK_{u}' 2>&1"
    )
    if f"OK_{u}" in out:
        print(f">>> SUCCESS (password): user={u} <<<")
        print(f"    Output: {out}")
        break
    else:
        print(f"  FAIL: {u}")
        if "Permission denied" not in out and out:
            print(f"    Detail: {out[:100]}")

# ── 3. 用 myvm 密钥 + 禁用密码试 ──
print("\n=== myvm 密钥认证 ===")
for u in users:
    rc, out, err = run_wsl(
        f"ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o PasswordAuthentication=no "
        f"-i ~/.ssh/myvm {u}@{host} 'echo KEY_OK_{u}' 2>&1"
    )
    if f"KEY_OK_{u}" in out:
        print(f">>> SUCCESS (myvm key): user={u} <<<")
        break
    else:
        # 只打印非标准错误信息
        if "Permission denied" in out:
            print(f"  FAIL: {u}")
        elif out:
            first_line = out.strip().split("\n")[0]
            print(f"  FAIL: {u} -> {first_line[:80]}")

# ── 4. 用 podman-machine-default 密钥试 ──
print("\n=== podman 密钥认证 ===")
for u in users:
    rc, out, err = run_wsl(
        f"ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o PasswordAuthentication=no "
        f"-i ~/.ssh/podman-machine-default {u}@{host} 'echo POD_OK_{u}' 2>&1"
    )
    if f"POD_OK_{u}" in out:
        print(f">>> SUCCESS (podman key): user={u} <<<")
        break
    else:
        if "Permission denied" in out:
            print(f"  FAIL: {u}")
        elif out:
            first_line = out.strip().split("\n")[0]
            print(f"  FAIL: {u} -> {first_line[:80]}")

print("\n=== 完成 ===")
