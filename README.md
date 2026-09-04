# Auto Money Agent — 工具站自动赚钱智能体

> 把"公众号文章里的方法论"变成可执行的代码：7 步流水线，从关键词到合规 AdSense。

## 这是什么

基于那篇"不写文章不投广告，一个工具站靠 AdSense 月入 $1500"的方法论，
构建的端到端可执行智能体。它做了文章里所有该做的事：

1. 选题 — 按 RPM × 难度把赛道排序
2. 关键词 — 长尾、有意图、词值不坑
3. 写代码 — 单文件 HTML + JS，零依赖、零后端
4. SEO — meta / OG / JSON-LD / 暗色模式全配齐
5. AdSense 合规 — 关于 / 隐私 / 联系全自动生成
6. 部署 — sitemap / robots / 部署 manifest 一次生成
7. 监控 — 7 天模拟数据 + 仪表盘

## 目录

```
auto-money-agent/
├── main.py                # 入口，跑完整 7 步
├── build_dashboard.py     # 把 reports/ 转成可看的 HTML
├── serve.py               # 本地静态服务器 (端口默认 8765)
├── config.yaml            # 赛道 / 关键词种子 / 合规阈值
├── agent/                 # 7 个模块
│   ├── niche.py           # 赛道评分
│   ├── keywords.py        # 关键词研究
│   ├── code_gen.py        # 单文件 HTML 工具生成器
│   ├── seo.py             # 12 项被动 SEO 检查
│   ├── compliance.py      # AdSense 合规页 + 检查表
│   ├── deploy.py          # sitemap / robots / 部署清单
│   └── monitor.py         # 指标写入 + 聚合 + 模拟器
├── tools_output/          # 实际可部署的静态站点
├── reports/               # 跑完生成的 Markdown + JSON + CSV
└── dashboard/             # 监控仪表盘
```

## 快速跑一遍

```bash
cd auto-money-agent
python main.py             # 跑 7 步流水线
python build_dashboard.py  # 把 metrics.csv 转 dashboard/index.html
python serve.py 8765       # 本地预览（http://127.0.0.1:8765）
```

跑完会自动产生：

| 产物 | 路径 |
|------|------|
| 3 个单文件工具页 | `tools_output/*.html`（每个 6-8 KB） |
| 首页索引 | `tools_output/index.html` |
| 关于 / 隐私 / 联系 | `tools_output/{about,privacy,contact}.html` |
| sitemap / robots | `tools_output/{sitemap.xml,robots.txt}` |
| 部署清单 | `tools_output/deploy.json` |
| 监控数据 | `reports/metrics.csv` |
| 监控仪表盘 | `dashboard/index.html` |

## Demo 结果（本次跑出的数字）

- 工具数：3
- 每个工具的 SEO 评分：12 / 12（满分）
- AdSense 合规：✅ True
- 模拟 7 天 PV：4,620，click 380，营收 $34.65，RPM $7.5

> 真实流量 1-3 个月内是谷歌沙盒期，会远低于这个数字，但所生成的结构、SEO、合规页、sitemap 都和真站没区别。

## 怎么从 Demo 跑到真站（10 分钟）

```bash
cd tools_output
git init
git add .
git commit -m "tool station seed"
# 1. 在 github 建一个 repo（比如 tool-station）
git remote add origin git@github.com:YOUR_NAME/tool-station.git
git push -u origin main
# 2. 仓库 Settings → Pages → Source: main / root
# 3. 60 秒后访问 https://YOUR_NAME.github.io/tool-station/
```

> 也可以直接拖到 Cloudflare Pages / Netlify / Vercel，都是零配置。

## AdSense 提交流程（不需要科技含量）

1. 准备一个 gmail，登录 https://www.google.com/adsense
2. 填网址（比如 `https://YOUR_NAME.github.io/tool-station/`）
3. 选账户类型（个人）
4. 等待审核（一般 1-3 天首次）

**通过率的关键**（文章里强调，代码已经做掉）：
- ✅ 至少 3 个工具页（已生成 3 个）
- ✅ Privacy policy（已生成）
- ✅ About page（已生成）
- ✅ Contact page（已生成）
- ✅ 没有违规词（已校验）

## 怎么规模化

工具站的杠杆是"工具数量 × 单工具流量 × 词的价值"。扩到 30-50 个工具就是文章说的 $1300/月 量级。

### A. 横向扩赛道（推荐先用）

打开 `agent/code_gen.py`，照 `spec_for_mortgage_calc` / `spec_for_text_case` / `spec_for_password_gen` 写更多 spec：

```python
def spec_for_json_formatter() -> ToolSpec:
    return ToolSpec(
        name="JSON formatter & validator",
        slug="json-formatter-validator",
        niche_id="text_processor",
        keyword="json formatter validator online",
        description="...",
        inputs=[...],
        output="result",
        template="text_processor",   # ← 已经支持的口味
        extra_copy="...",
    )
```

当前支持的 `template` 三种：calculator / text_processor / generator。
新建 spec → 加进 `main.py` 的 specs 列表 → 重跑 `python main.py`。
每加一个，工具站就多 6-8 KB 静态页和一个长尾关键词入口。

### B. 真实关键词数据流

目前 `agent/keywords.py` 用关键词种子 + 启发式打分。
替换为真实信号：

1. **Google Suggest** — `http://suggestqueries.google.com/complete/search?q=KEYWORD&client=firefox`，免费 scrape。
2. **GSC 数据**（自己有站后）：导出 query → clicks → position，反向定位下一个工具。
3. **低价关键词 API**：比如 Keywords Everywhere、Ahrefs 残值 API。

替换 `harvest(config_path)` 函数即可，下游无需改动。

### C. 真实流量监控

`agent/monitor.py` 现在是模拟器。要接真实数据：

1. **Cloudflare Analytics API**（如果你用 CF）— 直接拿 impressions/clicks。
2. **Google Search Console API** — 拿真实 impressions/position/ctr。
3. **AdSense Management API** — 拿真实 earnings。

`append_metric` 接口是写入点，把脚本改成定时拉真实 API 即可。

### D. 自动部署

`tools_output/deploy.json` 已经准备好对接 GitHub Actions：

```yaml
# .github/workflows/deploy.yml
name: deploy
on: { push: { branches: [main] } }
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Publish to GitHub Pages
        uses: actions/deploy-pages@v4
```

把这个文件拷到仓库根目录即可全自动部署。

## 90% 的人栽在的 3 个坑（代码已经规避）

1. **想做"大而全"** — 做 1 个工具顶 100 个烂尾。代码每次只产小工具，不鼓励超大件。
2. **只看流量不看 RPM** — `niche.py` 用 `mid_rpm × diff_mult` 评分，自动偏向高 RPM 赛道。
3. **没起色就放弃** — `monitor.py` 默认 7 天模拟，让你提前看到"沙盒期数据"长什么样，不会因为前 1-2 个月没流量而判项目死刑。

## 进阶：用 LLM 替换内置模板

当前内置 3 种 HTML 模板（calculator / text_processor / generator），覆盖 80% 的工具场景。
要拓展到检测器、图表、PDF 类工具，只需：

1. 在 `code_gen.py` 加一个新 `Template` 字符串，比如 `CHART_JS = Template(...)`
2. 加一个 `spec_for_xxx()` 函数
3. 在 `render_tool()` 的 if-elif 链里挂上新分支

未来要把这个升级成"LLM 生成模板"，只需要替换 `render_tool` 为：

```python
def render_tool(spec, base_url):
    prompt = f"Generate a single-file HTML/JS tool: {spec.name}. Description: {spec.description}..."
    return llm_call(prompt)
```

但**先用内置模板跑通 5-10 个工具**，再上 LLM，因为人的反馈比模型更准。
