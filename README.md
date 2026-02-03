# OnlineContestFetcher

定时抓取各大 OJ 比赛信息并生成 `contests.json`，同时提供纯静态前端（位于 `docs/`）以便直接部署到 GitHub Pages。

## 功能

- 抓取 Codeforces / 牛客 / AtCoder / 洛谷 / 力扣的近期比赛
- 定时更新 `contests.json`（GitHub Actions 定时任务）
- 纯静态页面（`docs/index.html`、`docs/calendar.html`、`docs/about.html`）读取 `contests.json`
- 适配 GitHub Pages

## 目录结构

- `contest_task.py`：抓取脚本
- `contests.json`：最新比赛数据（Actions 会定时更新）
- `docs/`：静态站点（GitHub Pages 从此目录发布）

## 本地运行

1. 安装依赖：
   ```bash
   pip install requests beautifulsoup4
   ```

2. 运行抓取脚本：
   ```bash
   python contest_task.py
   ```

3. 同步数据到静态站点目录：
   ```bash
   copy contests.json docs\contests.json
   ```

4. 本地预览静态站点：
   ```bash
   cd docs
   python -m http.server 8000
   ```
   浏览器访问 `http://localhost:8000/index.html`

## GitHub Actions

仓库已配置定时任务，会自动更新 `contests.json` 并同步到 `docs/contests.json`。

配置文件：` .github/workflows/contests.yml `

## GitHub Pages 部署

在仓库 Settings → Pages 中设置：

- Source: Deploy from a branch
- Branch: `main`
- Folder: `/docs`

保存后即可访问静态站点。

## 注意

- 直接双击 `docs/index.html` 会因为浏览器安全策略导致 `fetch` 被拦截，请使用本地静态服务器或 GitHub Pages 访问。
