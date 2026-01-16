# ContestScraper

这是一个定时抓取编程比赛信息的脚本，支持抓取多个在线编程平台的比赛信息，并将比赛数据保存在一个 JSON 文件中。

## 功能

- 支持抓取多个编程平台（如 Codeforces、牛客、AtCoder、洛谷、力扣）的竞赛数据。
- 定时任务，每隔 2 小时抓取一次比赛数据并更新输出文件。
- 结果保存为 JSON 格式，方便后续处理和展示。

## 使用方法

1. 克隆这个仓库到本地：
    ```bash
    git clone https://github.com/b8l8u8e8/OnlineContestFetcher.git
    ```

2. 修改脚本中的输出文件路径：
    - 打开 `contest_task.py`，找到 `OUTPUT_FILE`，将其修改为你的实际路径。

3. 运行脚本：
    ```bash
    python contest_task.py
    ```

4. 结果会保存在指定的 `OUTPUT_FILE` 路径中，文件格式为 JSON。

## GitHub Actions 设置

你可以设置 GitHub Actions 来定时执行这个脚本，具体请参考以下 `.github/workflows` 配置：

```yaml
name: Contest Scraper

on:
  schedule:
    - cron: '0 */2 * * *'  # 每 2 小时执行一次
  push:
    branches:
      - main

jobs:
  run-scraper:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run the script
      run: python contest_task.py
