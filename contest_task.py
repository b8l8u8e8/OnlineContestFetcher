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
OUTPUT_FILE = Path('contests.json')   # <-- 文件生成在根目录
# ====================================

TZ_CN = timezone(timedelta(hours=8))
HEADERS = {"User-Agent": "ContestCrawler (+https://example.com/)"}
LIMITS = {"cf": 6, "nk": 6, "ac": 5, "lg": 5, "lc": 3}
CONNECT_TIMEOUT, READ_TIMEOUT = 5, 15

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在

session = requests.Session()
session.headers.update(HEADERS)
session.mount(
    "https://",
    HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1,
                                  status_forcelist=[429,500,502,503,504],
                                  allowed_methods=["GET","POST"])) )

def safe_get(url:str,**kw):
    try:
        return session.get(url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT), **kw)
    except requests.RequestException:
        return None

def safe_post(url:str,**kw):
    try:
        return session.post(url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT), **kw)
    except requests.RequestException:
        return None

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

def fetch_nk(lim: int):
    now = datetime.now(TZ_CN)
    r = safe_get('https://ac.nowcoder.com/acm/contest/vip-index')
    if not (r and r.ok): return []
    soup = BeautifulSoup(r.text, 'html.parser')
    res = []
    for h4 in soup.find_all('h4'):
        txt = h4.get_text(strip=True)
        if '报名中' not in txt and '距比赛' not in (h4.find_next_sibling(text=True) or ''): continue
        name = re.split(r'原创', txt)[0]
        name = re.sub(r'(报名中|距比赛.*)$', '', name).strip('· ').strip()
        ul = h4.find_next_sibling('ul') or h4.find_next_sibling('div')
        if not ul: continue
        li = ul.find(lambda t: t.name in ('li', 'p') and '比赛时间' in t.get_text())
        if not li: continue
        m = re.search(r'比赛时间[：:]\s*([\d-]+\s+[\d:]+)', li.get_text())
        if not m: continue
        try:
            dt = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M').replace(tzinfo=TZ_CN)
        except:
            continue
        if dt < now: continue
        res.append({'name': name, 'start': dt})
        if len(res) >= lim: break
    res.sort(key=lambda x: x['start'])
    return res

def fetch_ac(lim: int):
    r = safe_get('https://atcoder.jp/contests/')
    if not (r and r.ok): return []
    soup = BeautifulSoup(r.text, 'html.parser')
    head = soup.find(lambda t: t.name in ('h2', 'h3') and 'Upcoming Contests' in t.get_text())
    table = head.find_next('table') if head else None
    if not table: return []
    res = []
    for row in table.find('tbody').find_all('tr'):
        cols = row.find_all('td')
        if len(cols) < 2: continue
        try:
            dt = datetime.strptime(cols[0].get_text(strip=True), '%Y-%m-%d %H:%M:%S%z').astimezone(timezone.utc)
        except:
            continue
        if dt < datetime.now(timezone.utc): continue
        name = re.sub(r'^[^\w\d]+', '', cols[1].get_text(strip=True))
        res.append({'name': name, 'start': dt})
        if len(res) >= lim: break
    return res

def fetch_lg(lim: int):
    now = datetime.now(TZ_CN)
    r = safe_get('https://www.luogu.com.cn/contest/list?_contentOnly=1',
               headers={**HEADERS, 'Referer': 'https://www.luogu.com.cn/contest/list'})
    if not (r and r.ok): return []
    try:
        data = r.json()
    except:
        return []
    raw = data.get('currentData', {}).get('contests', {}).get('result', [])
    res = []
    for c in raw:
        name = (c.get('name') or '').strip()
        ts = c.get('startTime')
        if not name or ts is None: continue
        if isinstance(ts, (int, float)):
            if ts > 1e12: ts /= 1000
            dt = datetime.fromtimestamp(ts, TZ_CN)
        else:
            continue
        if dt < now: continue
        res.append({'name': name, 'start': dt})
    res.sort(key=lambda x: x['start'])
    return res[:lim]

def fetch_lc(lim: int):
    res = []
    gql_cn = {'operationName': None, 'variables': {}, 'query': 'query { contestUpcoming { title startTime } }'}
    j = safe_post('https://leetcode.cn/graphql/', json=gql_cn, headers={**HEADERS, 'Referer': 'https://leetcode.cn/contest/'})
    if j and j.ok:
        try:
            for itm in j.json().get('data', {}).get('contestUpcoming', []):
                ts = itm.get('startTime')
                if isinstance(ts, (int, float)):
                    res.append({'name': itm.get('title', '').strip(), 'start': datetime.fromtimestamp(ts, TZ_CN)})
        except:
            pass
    if not res:
        gql_en = {'operationName': None, 'variables': {}, 'query': 'query { upcomingContests { title startTime } }'}
        j2 = safe_post('https://leetcode.com/graphql/', json=gql_en, headers={**HEADERS, 'Referer': 'https://leetcode.com/contest/'})
        if j2 and j2.ok:
            try:
                for itm in j2.json().get('data', {}).get('upcomingContests', []):
                    ts = itm.get('startTime')
                    if isinstance(ts, (int, float)):
                        res.append({'name': itm.get('title', '').strip(), 'start': datetime.fromtimestamp(ts, timezone.utc)})
            except:
                pass
    res.sort(key=lambda x: x['start'])
    return res[:lim]

FETCHERS = [('Codeforces', fetch_cf, 'cf'), ('\u725b\u5ba2', fetch_nk, 'nk'), ('AtCoder', fetch_ac, 'ac'),
          ('\u6d1b\u8c37', fetch_lg, 'lg'), ('\u529b\u6263', fetch_lc, 'lc')]

def get_contests():
    contests = []
    for site, fetcher, key in FETCHERS:
        try:
            data = fetcher(LIMITS[key])
        except Exception as e:
            print(f'[{site}] 抓取失败：{e}', file=sys.stderr)
            data = []
        for d in data:
            contests.append({'site': site, 'name': d['name'], 'start': d['start']})
    contests.sort(key=lambda x: x['start'])
    return contests

# ---------- 主程序 ----------
if __name__ == '__main__':
    contests = get_contests()  # <-- 确保调用 get_contests 函数
    payload = {'generated_at': datetime.now(timezone.utc).isoformat(),
               'contests': [{'site': c['site'], 'name': c['name'], 'start': c['start'].astimezone(timezone.utc).isoformat()}
                            for c in contests]}
    tmp = OUTPUT_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(OUTPUT_FILE)
    print(f'✓ 抓取完成，共 {len(contests)} 场')
    print(f'输出文件：{OUTPUT_FILE}')
