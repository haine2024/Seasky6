#!/usr/bin/env python3
# ============================================================
# probe_pages.py — 实测 Seasky6 GitHub Pages 真实状态
#
# 用真实 HTTP 请求而不是 WebFetch，避免被 GitHub 验证页拦截
#
# 用法：
#   python probe_pages.py
#
# 输出：
#   - Repo / Pages / 站点 / AdSense 代码 / Workflow run 的真实状态
# ============================================================

import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request


REPO_OWNER = "haine2024"
REPO_NAME = "Seasky6"
SITE_URL = f"https://{REPO_OWNER}.github.io/{REPO_NAME}/"
ROOT_SITE_URL = f"https://{REPO_OWNER}.github.io/"
EXPECTED_PUBLISHER_ID = "ca-pub-1956340995769142"
UA = "auto-money-agent-probe/1.0"


def hr(title):
    print()
    print("=" * 64)
    print(f"  {title}")
    print("=" * 64)


def http(method, url, timeout=15):
    try:
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="ignore"), dict(r.headers)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        return e.code, body, {}
    except Exception as e:
        return -1, str(e), {}


def main():
    hr("Seasky6 实测诊断")
    print(f"Repo :  github.com/{REPO_OWNER}/{REPO_NAME}")
    print(f"Site :  {SITE_URL}")
    print(f"Root :  {ROOT_SITE_URL}")
    print(f"PubID:  {EXPECTED_PUBLISHER_ID}")

    # 1. 仓库存在性
    hr("[1] Repo 是否存在")
    code, body, _ = http("HEAD", f"https://github.com/{REPO_OWNER}/{REPO_NAME}")
    print(f"  https://github.com/{REPO_OWNER}/{REPO_NAME}  ->  HTTP {code}")
    if code == 404:
        print("  ✗ 仓库不存在或私有不可见")
        return 1
    elif code == 200:
        print("  ✓ 仓库存在")

    # 2. 用户主页（根 Pages）
    hr("[2] 用户根 Pages (haine2024.github.io)")
    code, body, _ = http("GET", ROOT_SITE_URL)
    snippet = body[:200].replace("\n", " ")
    if "There isn't a GitHub Pages site here" in body or "Site not found" in body:
        print(f"  HTTP {code}  ✗ 用户根 Pages 完全没启用")
        print(f"  片段: {snippet}")
    elif code == 200:
        print(f"  HTTP {code}  ✓ 用户根 Pages 已启用")
    else:
        print(f"  HTTP {code}  ? 状态未知")
        print(f"  片段: {snippet}")

    # 3. 项目 Pages
    hr("[3] 项目 Pages (haine2024.github.io/Seasky6)")
    code, body, _ = http("GET", SITE_URL)
    snippet = body[:200].replace("\n", " ")
    if "There isn't a GitHub Pages site here" in body or "Site not found" in body:
        print(f"  HTTP {code}  ✗ 项目 Pages 没启用（你看到 404 的原因）")
        print(f"  片段: {snippet}")
    elif code == 200:
        if EXPECTED_PUBLISHER_ID in body:
            print(f"  HTTP {code}  ✓ 站点已上线，AdSense 代码也在")
        else:
            print(f"  HTTP {code}  ⚠ 站点已上线但页面里没找到 AdSense 代码")
            print(f"  片段: {snippet}")
    else:
        print(f"  HTTP {code}  ? 状态未知")
        print(f"  片段: {snippet}")

    # 4. AdSense 代码存在性（如果站点上线）
    hr("[4] AdSense 代码在线上页面的存在性")
    code, body, _ = http("GET", SITE_URL)
    if code == 200:
        if EXPECTED_PUBLISHER_ID in body:
            count = body.count(EXPECTED_PUBLISHER_ID)
            print(f"  ✓ 找到 {count} 处 AdSense publisher ID")
        else:
            print(f"  ✗ 页面里没有 AdSense publisher ID")
            print(f"     页面长度: {len(body)}")
    else:
        print(f"  ✗ 站点不可达 (HTTP {code})")

    # 5. Workflow 最近一次运行
    hr("[5] Workflow 最近一次运行")
    code, body, _ = http("GET", f"https://github.com/{REPO_OWNER}/{REPO_NAME}/actions")
    if code == 200:
        runs = re.findall(r'href="/' + REPO_OWNER + r'/' + REPO_NAME + r'/actions/runs/(\d+)"', body)
        statuses = re.findall(r'class="d-block workflow-run-status"[^>]*?>\s*<svg[^>]*?aria-label="([^"]+)"', body)
        if runs:
            for i, run_id in enumerate(runs[:5]):
                label = statuses[i] if i < len(statuses) else "?"
                print(f"  Run #{run_id}: {label}")
        else:
            print("  ⚠ 找不到任何 workflow run（Actions 页可能没列出来或反爬）")
    else:
        print(f"  ? Actions 页不可访问 (HTTP {code})")

    # 6. 本地 git 状态
    hr("[6] 本地 git 状态")
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        branch = out.stdout.strip() if out.returncode == 0 else "?"
        out = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            capture_output=True, text=True, timeout=5,
        )
        commit = out.stdout.strip() if out.returncode == 0 else "?"
        out = subprocess.run(
            ["git", "ls-remote", "origin", "HEAD"],
            capture_output=True, text=True, timeout=15,
        )
        remote = out.stdout.split()[0] if out.stdout else "?"
        print(f"  本地分支 :  {branch}")
        print(f"  本地最新 :  {commit}")
        print(f"  远程最新 :  {remote}")
        if commit.startswith(remote[:7]):
            print("  ✓ 本地与远程一致")
        else:
            print(f"  ⚠ 本地与远程不一致（差 {remote[:7]} vs {commit[:7] if commit != '?' else '?'}）")
    except FileNotFoundError:
        print("  ✗ git 命令不存在")
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")

    # 7. 行动指引
    hr("行动指引")
    if "There isn't a GitHub Pages site here" in http("GET", SITE_URL)[1]:
        print("""
  现在确诊：项目 Pages 没启用。

  30 秒修好（推荐）：

  1. 浏览器打开这个链接（已登录 GitHub）：
     https://github.com/haine2024/Seasky6/settings/pages

  2. 在 'Build and deployment' 下面：
     Source:   选  "GitHub Actions"
     然后点 "Save" 按钮。

  3. 回到我对话窗口里说 "好了" 或 "跑 probe"，
     我会触发一次 push 让 workflow 自动部署，60 秒后你刷新：
     https://haine2024.github.io/Seasky6/

  4. 看到网站后，去 AdSense 后台把验证 URL 改成：
     https://haine2024.github.io/Seasky6/
     点 "Verify" 就能通过。
""")
    else:
        print("""
  站点已经在线！可以直接去 AdSense 后台验证。
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())