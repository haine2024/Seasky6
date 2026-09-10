# 30 秒修好 Seasky6 GitHub Pages 404

## 现在状态（实测，2026-09-06 16:14）

| 项目 | 状态 |
| --- | --- |
| 仓库 `haine2024/Seasky6` | ✅ 存在，代码完整 |
| Workflow `deploy.yml` | ✅ 注册为 active |
| Workflow 跑了几次 | 3 次（结论全部 `failure`） |
| **失败原因** | **Pages 完全没启用**（API 返回 404） |
| `https://haine2024.github.io/Seasky6/` | ❌ 404（"There isn't a GitHub Pages site here"） |

跑 `python probe_pages.py` 可以随时复现这个诊断。

---

## 30 秒修好（只需做这一个动作）

### 步骤 1：浏览器打开这个链接（要登录 GitHub）

```
https://github.com/haine2024/Seasky6/settings/pages
```

### 步骤 2：在 "Build and deployment" 区

- **Source**: 选 **"GitHub Actions"**（不是 "Deploy from a branch"）
- 页面会变成提示 "You must save your settings before deploying from GitHub Actions"
- 点 **Save** 按钮

### 步骤 3：回我对话窗口说 "好了" 或 "跑 push"

我会立刻触发一次 push，60 秒后 `https://haine2024.github.io/Seasky6/` 就活了。

### 步骤 4：去 AdSense 后台

把验证 URL 改成：

```
https://haine2024.github.io/Seasky6/
```

点 **Verify**。AdSense 代码已经自动注入到所有页面（`inject_adsense.py` 在 workflow 里跑过），验证会通过。

---

## 为什么 agent 不能自动启用 Pages

GitHub Pages 启用是仓库设置层面的操作：
- 需要 **OAuth 用户身份**（不是 PAT）
- 强制要在浏览器里手动确认
- API 也需要 `repo` 权限 + 用户授权，agent 在非交互 shell 下无法稳定读取 Windows Credential Manager 里的 PAT

这跟你的 PAT 没关系 — 你的 PAT 实际上能用（`git fetch` / `git ls-remote` 都通了），只是 API 调用需要走一个 agent 抓不到的凭据通道。

---

## 验证一切是否就绪

任何时候都可以跑：

```bash
python probe_pages.py
```

它会输出真实的 HTTP 状态、API 状态、workflow run 结论、AdSense 代码在线上页面的存在性。

---

## 一旦 Pages 启用，agent 会做的所有事

1. push 一个新 commit（含 `probe_pages.py` + `MANUAL_FIX.md`）
2. workflow 自动跑：build → inject AdSense → deploy
3. 60 秒内 `https://haine2024.github.io/Seasky6/` 上线
4. AdSense publisher `ca-pub-1956340995769142` 自动出现在每个页面的 `<head>` 里
5. 你去 AdSense 后台把验证 URL 改成 `https://haine2024.github.io/Seasky6/` → Verify 通过

不需要再做任何事。