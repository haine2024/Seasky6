#!/usr/bin/env python3
# ============================================================
# enable_pages.py — 启用 GitHub Pages（一次性，需要 PAT）
#
# 注意：PAT 必须带 `repo` + `pages` 权限，且 Windows Credential
# Manager 在非交互 shell 下读取会 SIGTERM，因此该脚本**通常会失败**。
# 推荐改用 MANUAL_FIX.md 里写的 UI 路径（30 秒搞定）。
#
# 用法：
#   python enable_pages.py
#
# 它会自动：
#   1. 从 git credential helper 读出你之前配好的 PAT
#   2. 调 GitHub API 给 Seasky6 启用 Pages（Source: GitHub Actions）
#   3. 触发 Actions 跑一次 deploy workflow
#   4. 轮询等站点上线，最多 90 秒
#   5. 验活 + 验证 AdSense 代码是否真的出现在线上页面
#
# 整个过程 PAT 不会经过 AI/聊天，只在你的本机使用
# ============================================================

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import urllib.parse

# ---- 配置（按需修改） ----
REPO_OWNER = "haine2024"
REPO_NAME = "Seasky6"
PAGES_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pages"
SITE_URL = f"https://{REPO_OWNER}.github.io/{REPO_NAME}/"
EXPECTED_PUBLISHER_ID = "ca-pub-1956340995769142"


def get_pat_from_git() -> str:
    """从 Windows Credential Manager 读出 git 已存的 GitHub PAT"""
    print("[1/5] 从 git credential helper 读 PAT...")
    try:
        out = subprocess.run(
            ["git", "credential", "fill"],
            input=f"protocol=https\nhost=github.com\n",
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0:
            raise RuntimeError(f"git credential fill 失败: {out.stderr}")
        for line in out.stdout.splitlines():
            if line.startswith("password="):
                pat = line.split("=", 1)[1].strip()
                if pat:
                    return pat
        raise RuntimeError("credential helper 没返回密码")
    except FileNotFoundError:
        raise RuntimeError("找不到 git 命令")
    except subprocess.TimeoutExpired:
        raise RuntimeError("credential helper 超时（可能没配 PAT，请先跑 setup_github_auth）")


def gh_api(method: str, url: str, pat: str, body: dict | None = None):
    """GitHub API 请求"""
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {pat}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "auto-money-agent-enabler",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def enable_pages(pat: str) -> tuple[bool, str]:
    """调用 API 启用 Pages（Source: GitHub Actions）"""
    print("[2/5] 调 GitHub API 启用 Pages（Source = GitHub Actions）...")
    status, body = gh_api("POST", PAGES_URL, pat, body={"build_type": "workflow"})
    if status == 201:
        return True, "✓ Pages 已启用，正在等 Actions 跑首次部署"
    if status == 409:
        # 409 = 已经启用
        status2, body2 = gh_api("GET", PAGES_URL, pat)
        if status2 == 200:
            return True, f"✓ Pages 之前已启用（{body2.get('build_type')}），继续下一步"
        return False, f"已启用但状态异常：{body2}"
    if status == 401:
        return False, "✗ PAT 无效或过期，需要重新生成"
    if status == 403:
        return False, (
            f"✗ PAT 权限不够（需要 `pages: write` / `repo` 权限）。\n"
            f"   API 报错：{body.get('message', '')}"
        )
    return False, f"✗ API 调用失败 (HTTP {status}): {body}"


def trigger_workflow(pat: str) -> bool:
    """手动触发 deploy workflow（万一 Pages 启用后没自动跑）"""
    print("[3/5] 手动触发 deploy workflow...")
    url = (
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/"
        f"actions/workflows/deploy-tool-station.yml/dispatches"
    )
    status, body = gh_api("POST", url, pat, body={"ref": "main"})
    return status in (204, 404)  # 404 means workflow file doesn't exist, that's OK


def wait_for_site(timeout: int = 90) -> bool:
    """轮询等站点上线"""
    print(f"[4/5] 等待站点上线（最多 {timeout} 秒）...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(SITE_URL, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode(errors="ignore")
                # 检查 1: 不是 GitHub 404
                if "Site not found" in body or "404" in body[:1000]:
                    time.sleep(3)
                    continue
                # 检查 2: AdSense 代码真的在
                if EXPECTED_PUBLISHER_ID in body:
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(3)
                continue
        except Exception:
            pass
        time.sleep(3)
    return False


def verify_adsense() -> tuple[bool, str]:
    """验证 AdSense 代码是否真的在页面里"""
    print("[5/5] 验证 AdSense 代码是否在部署页面里...")
    try:
        req = urllib.request.Request(SITE_URL, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode(errors="ignore")
            if EXPECTED_PUBLISHER_ID in html:
                return True, f"✓ AdSense 代码确认在线上页面（{SITE_URL}）"
            return False, "✗ 站点上线了但 AdSense 代码没找到"
    except Exception as e:
        return False, f"✗ 验证失败：{e}"


def main():
    print("=" * 60)
    print(f"目标仓库:  github.com/{REPO_OWNER}/{REPO_NAME}")
    print(f"目标站点:  {SITE_URL}")
    print(f"AdSense ID: {EXPECTED_PUBLISHER_ID}")
    print("=" * 60)

    # 1. 读 PAT
    try:
        pat = get_pat_from_git()
        print(f"       ✓ 读到 PAT（长度 {len(pat)}）")
    except RuntimeError as e:
        print(f"\n{e}")
        print("\n请先跑 setup_github_auth.bat / .sh 配 PAT")
        sys.exit(1)

    # 2. 启用 Pages
    ok, msg = enable_pages(pat)
    print(f"       {msg}")
    if not ok:
        sys.exit(1)

    # 3. 触发 workflow（页面可能没自动触发）
    if trigger_workflow(pat):
        print("       ✓ workflow 已触发（或不存在，会跳过）")
    else:
        print("       ⚠ workflow 触发失败（不影响 Pages 已启用）")

    # 4. 等站点上线
    if not wait_for_site():
        print("\n✗ 90 秒内没看到站点上线")
        print("   检查: https://github.com/{}/{}/actions".format(REPO_OWNER, REPO_NAME))
        sys.exit(1)
    print("       ✓ 站点已上线")

    # 5. 验证 AdSense
    ok, msg = verify_adsense()
    print(f"       {msg}")
    if ok:
        print("\n" + "=" * 60)
        print("🎉 全部跑通！")
        print(f"   站点地址:   {SITE_URL}")
        print(f"   AdSense ID: {EXPECTED_PUBLISHER_ID}")
        print()
        print("下一步：去 AdSense 后台把 URL 改成上面这个站点地址")
        print(f"   字段值:    {SITE_URL}")
        print("   然后点'验证'。")
        print("=" * 60)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()