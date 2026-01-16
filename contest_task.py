#!/usr/bin/env python3
# -*- coding: utf-8 -*- 
"""
contest_task.py  —  单文件抓取脚本（请手动修改 OUTPUT_FILE 为绝对路径）

使用：
    1. 打开本文件，找到 OUTPUT_FILE，一次性填入 “web/contests.json” 的绝对路径。
    2. 运行： python3 contest_task.py
       结束时会打印：
          ✓ 抓取完成，共 N 场
          输出文件： /your/absolute/path/contests.json
"""
from __future__ import annotations
import sys, re, json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Callable, Optional

import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup

# ========= ① 这里填写绝对路径 =========
OUTPUT_FILE = Path('contests.json')   # <-- 改为根目录
# ====================================

TZ_CN = timezone(timedelta(hours=8))
HEADERS = {"User-Agent": "ContestCrawler (+https://example.com/)"}
LIMITS = {"cf": 6, "nk": 6, "ac": 5, "lg": 5, "lc": 3}
CONNECT_TIMEOUT, READ_TIMEOUT = 5, 15

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update(HEADERS)
session.mount(
    "https://",
    HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1,
                                  status_forcelist=[429,500,502,503,504],
                                  allowed_methods=["GET","POST"])) )

# ---------- 各 OJ 抓取器 ----------
from datetime import datetime

def _parse_cf_api(jd):
    if jd.get('status') != 'OK': return []
    res = [{'name': c['name'].strip(), 'start': datetime.fromtimestamp(c['startTimeSeconds'], timezone.utc)}
           for c in jd['result'] if c.get('phase') in ('BEFORE', 'CODING')]
    res.sort(key=lambda x: x['start'])
    return res

def _parse_cf_html(lim: int):
    r = safe_get('https://codeforces.com/contests')
    if not (r and r.ok): return []
    soup = BeautifulSoup(r.text, 'html.parser')
    head = soup.find(lambda t: t.name in ('h2', 'h3') and 'Upcoming Contests' in t.get_text())
    table = head.find_next('table') if head else None
    if not table: return []
    res = []
    for tr in table.find('tbody').find_all('tr'):
        ts = tr.get('data-starttime')
        if not ts: continue
        try:
            dt = datetime.fromtimestamp(int(ts), timezone.utc)
        except:
            continue
        name = (tr.find('a') or tr).get_text(strip=True)
        res.append({'name': name, 'start': dt})
        if len(res) >= lim: break
    return res

def fetch_cf(lim: int):
    for api in ('https://codeforces.com/api/contest.list?gym=false', 'https://codeforces.com/api/contest.list'):
        r = safe_get(api)
        if r and r.ok:
            try:
                d = _parse_cf_api(r.json())
                if d: return d[:lim]
            except: pass
    return _parse_cf_html(lim)[:lim]

# 其他抓取器代码略，保持不变...

# ---------- 主程序 ----------
if __name__ == '__main__':
    contests = get_contests()
    payload = {'generated_at': datetime.now(timezone.utc).isoformat(),
               'contests': [{'site': c['site'], 'name': c['name'], 'start': c['start'].astimezone(timezone.utc).isoformat()}
                            for c in contests]}
    tmp = OUTPUT_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(OUTPUT_FILE)
    print(f'✓ 抓取完成，共 {len(contests)} 场')
    print(f'输出文件：{OUTPUT_FILE}')
