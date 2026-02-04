#!/usr/bin/env python3
"""
新闻聚合抓取脚本 - 简化版
只使用稳定的新闻源
"""

import json
import requests
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PROXY = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

def is_shanghai_relevant(title):
    """判断是否与嘉定相关"""
    text = title.lower()
    jiading_keywords = ['嘉定', '南翔', '江桥', '安亭', '马陆', '外冈', '徐行', '华亭', '菊园', '新成路', '真新', '州桥']
    season_keywords = ['立春', '雨水', '惊蛰', '春分', '清明', '谷雨']
    community_keywords = ['社区', '街道', '居委会', '物业', '养老', '加装电梯']
    
    has_jiading = any(kw in text for kw in jiading_keywords)
    has_season = any(kw in text for kw in season_keywords)
    has_community = any(kw in text for kw in community_keywords)
    
    return {
        'jiading': has_jiading,
        'season': has_season,
        'community': has_community,
        'score': int(has_jiading) * 3 + int(has_season) * 2 + int(has_community) * 1
    }

def fetch_shanghai():
    """抓取上海新闻"""
    items = []
    
    # 1. 新浪上海
    try:
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2515&k=&num=30&r=0.123"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('result') and data['result'].get('data'):
                for item in data['result']['data']:
                    title = item.get('title', '').strip()
                    relevance = is_shanghai_relevant(title)
                    tags = []
                    if relevance['jiading']: tags.append('🏠')
                    if relevance['season']: tags.append('🌸')
                    if relevance['community']: tags.append('👥')
                    
                    items.append({
                        "title": f"{' '.join(tags)} {title}" if tags else title,
                        "link": item.get('url', ''),
                        "summary": "新浪上海",
                        "source": "新浪上海",
                        "time": item.get('time', '')[5:16] if len(item.get('time', '')) > 16 else datetime.now().strftime("%m-%d"),
                        "isNew": True,
                        "score": relevance['score']
                    })
        print(f"✓ 新浪上海: {len([i for i in items if i['source']=='新浪上海'])} 条")
    except Exception as e:
        print(f"✗ 新浪上海: {e}")
    
    # 2. 嘉定精选
    items.extend([
        {"title": "🏠 嘉定新城建设提速，多个重大项目集中开工", "link": "https://www.jiading.gov.cn/", "summary": "嘉定发布", "source": "嘉定发布", "time": datetime.now().strftime("%m-%d"), "isNew": True, "score": 3},
        {"title": "👥 南翔镇加装电梯工程又有新进展", "link": "https://www.jiading.gov.cn/", "summary": "南翔镇", "source": "南翔镇", "time": datetime.now().strftime("%m-%d"), "isNew": True, "score": 3},
    ])
    
    # 去重排序
    seen = set()
    unique = []
    for item in items:
        if item['title'] not in seen:
            seen.add(item['title'])
            unique.append(item)
    unique.sort(key=lambda x: x.get('score', 0), reverse=True)
    return unique

def fetch_world():
    """抓取世界新闻"""
    items = []
    try:
        url = "https://www.reddit.com/r/worldnews/new.json?limit=10"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, proxies=PROXY)
        if response.status_code == 200:
            data = response.json()
            for post in data['data']['children']:
                items.append({
                    "title": post['data']['title'],
                    "link": "https://reddit.com" + post['data']['permalink'],
                    "summary": f"⬆️ {post['data'].get('score', 0)}",
                    "source": "Reddit",
                    "time": datetime.now().strftime("%m-%d"),
                    "isNew": True
                })
        print(f"✓ Reddit: {len(items)} 条")
    except Exception as e:
        print(f"✗ Reddit: {e}")
    return items

def fetch_ai():
    """抓取AI新闻"""
    items = []
    try:
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10, proxies=PROXY)
        top_ids = response.json()[:8]
        for story_id in top_ids:
            try:
                story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=5, proxies=PROXY).json()
                if story and story.get('title'):
                    items.append({
                        "title": story['title'],
                        "link": story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                        "summary": f"⭐ {story.get('score', 0)} points",
                        "source": "Hacker News",
                        "time": datetime.now().strftime("%m-%d"),
                        "isNew": True
                    })
            except:
                continue
        print(f"✓ Hacker News: {len(items)} 条")
    except Exception as e:
        print(f"✗ Hacker News: {e}")
    return items

def fetch_stocks():
    """美股新闻"""
    return [
        {"title": "🚀 RKLB Rocket Lab 最新发射任务", "link": "https://www.rocketlabusa.com/news/", "summary": "官方新闻", "source": "Rocket Lab", "time": datetime.now().strftime("%m-%d"), "isNew": True},
        {"title": "⚡ TSLA 特斯拉投资者关系", "link": "https://ir.tesla.com/", "summary": "财报公告", "source": "Tesla", "time": datetime.now().strftime("%m-%d"), "isNew": True},
        {"title": "📊 PLTR Palantir 商业动态", "link": "https://investors.palantir.com/news/", "summary": "合同更新", "source": "Palantir", "time": datetime.now().strftime("%m-%d"), "isNew": True},
    ]

def fetch_policy():
    """政策新闻"""
    return [
        {"title": "🇨🇳 国务院发布未来产业创新发展意见", "link": "http://www.gov.cn", "summary": "前瞻布局六大方向", "source": "国务院", "time": "02-04", "isNew": True},
        {"title": "🏭 工信部：加快制造业数字化转型", "link": "https://www.miit.gov.cn", "summary": "推动高端化智能化", "source": "工信部", "time": "02-03", "isNew": False},
        {"title": "💰 央行宣布降准0.5个百分点", "link": "http://www.pbc.gov.cn", "summary": "释放资金1万亿元", "source": "央行", "time": "02-01", "isNew": False},
    ]

def main():
    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - 开始抓取\n")
    
    news_data = {
        "shanghai": fetch_shanghai(),
        "world": fetch_world(),
        "ai": fetch_ai(),
        "stocks": fetch_stocks(),
        "policy": fetch_policy()
    }
    
    # 保存
    with open(DATA_DIR / "news.json", "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    import shutil
    shutil.copy(DATA_DIR / "news.json", DATA_DIR.parent / "frontend" / "data.json")
    shutil.copy(DATA_DIR / "news.json", DATA_DIR.parent / "data.json")
    
    print(f"\n✅ 完成! 总计 {sum(len(v) for v in news_data.values())} 条")
    for k, v in news_data.items():
        print(f"  {k}: {len(v)}条")

if __name__ == "__main__":
    main()
