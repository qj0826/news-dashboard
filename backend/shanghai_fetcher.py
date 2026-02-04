#!/usr/bin/env python3
"""
上海新闻抓取 - 直接抓取官网（绕过RSSHub）
"""

import requests
import re
import json
from datetime import datetime
from html import unescape

PROXY = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

def is_shanghai_relevant(title, summary=""):
    """判断是否与嘉定/节气/社区相关"""
    text = (title + summary).lower()
    
    jiading_keywords = ['嘉定', '南翔', '江桥', '安亭', '马陆', '外冈', '徐行', '华亭', '菊园', '新成路', '真新', '嘉定新城', '州桥', '法华塔']
    season_keywords = ['立春', '雨水', '惊蛰', '春分', '清明', '谷雨', '立夏', '小满', '芒种', '夏至', '小暑', '大暑',
                       '立秋', '处暑', '白露', '秋分', '寒露', '霜降', '立冬', '小雪', '大雪', '冬至', '小寒', '大寒']
    community_keywords = ['社区', '街道', '居委会', '业委会', '物业', '邻里', '便民', '养老', '托育', '菜场', '旧改', '加装电梯']
    
    has_jiading = any(kw in text for kw in jiading_keywords)
    has_season = any(kw in text for kw in season_keywords)
    has_community = any(kw in text for kw in community_keywords)
    
    return {
        'jiading': has_jiading,
        'season': has_season,
        'community': has_community,
        'score': int(has_jiading) * 3 + int(has_season) * 2 + int(has_community) * 1
    }

def fetch_thepaper():
    """抓取澎湃新闻官网"""
    items = []
    try:
        # 直接抓首页热门新闻
        url = "https://www.thepaper.cn/"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            html = response.text
            # 尝试多种匹配模式
            patterns = [
                r'href="(/newsDetail_forward_\d+)"[^>]*>[^<]*<[^>]*>([^<]{10,100})</',
                r'href="(/newsDetail_forward_\d+)"[^>]*>\s*([^<]{10,100})',
            ]
            
            seen = set()
            for pattern in patterns:
                matches = re.findall(pattern, html)
                for link, title in matches[:15]:
                    if link not in seen and title.strip() and len(title.strip()) > 10:
                        seen.add(link)
                        title_clean = unescape(title.strip())
                        relevance = is_shanghai_relevant(title_clean)
                        
                        tags = []
                        if relevance['jiading']: tags.append('🏠')
                        if relevance['season']: tags.append('🌸')
                        if relevance['community']: tags.append('👥')
                        
                        items.append({
                            "title": f"{' '.join(tags)} {title_clean}" if tags else title_clean,
                            "link": f"https://www.thepaper.cn{link}",
                            "summary": "澎湃新闻",
                            "source": "澎湃新闻",
                            "time": datetime.now().strftime("%m-%d"),
                            "isNew": True,
                            "score": relevance['score']
                        })
                if len(items) > 0:
                    break
        
        print(f"  ✓ 澎湃新闻: {len(items)} 条")
    except Exception as e:
        print(f"  ✗ 澎湃新闻: {str(e)[:50]}")
    
    return items

def fetch_eastday():
    """抓取东方网"""
    items = []
    try:
        url = "https://www.eastday.com/"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            html = response.text
            # 匹配新闻标题和链接
            pattern = r'href="(https?://[^"]*eastday[^"]*/[\d/]+[^"]*)"[^>]*>([^<]{10,})<'
            matches = re.findall(pattern, html)
            
            seen = set()
            for link, title in matches[:10]:
                if link not in seen and title.strip():
                    seen.add(link)
                    title_clean = unescape(title.strip())
                    relevance = is_shanghai_relevant(title_clean)
                    
                    items.append({
                        "title": title_clean,
                        "link": link,
                        "summary": f"东方网 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "东方网",
                        "source": "东方网",
                        "time": datetime.now().strftime("%m-%d"),
                        "isNew": True,
                        "score": relevance['score']
                    })
        
        print(f"  ✓ 东方网: {len(items)} 条")
    except Exception as e:
        print(f"  ✗ 东方网: {str(e)[:50]}")
    
    return items

def fetch_sina_shanghai():
    """抓取新浪上海新闻"""
    items = []
    try:
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2515&k=&num=20&r=0.123"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('result') and data['result'].get('data'):
                news_list = data['result']['data']
                for item in news_list:
                    title = item.get('title', '').strip()
                    url = item.get('url', '')
                    time_str = item.get('time', '')
                    
                    relevance = is_shanghai_relevant(title)
                    tags = []
                    if relevance['jiading']: tags.append('🏠')
                    if relevance['season']: tags.append('🌸')
                    if relevance['community']: tags.append('👥')
                    
                    items.append({
                        "title": f"{' '.join(tags)} {title}" if tags else title,
                        "link": url,
                        "summary": f"新浪上海 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "新浪上海",
                        "source": "新浪上海",
                        "time": time_str[5:16] if len(time_str) > 16 else time_str,
                        "isNew": True,
                        "score": relevance['score']
                    })
        
        print(f"  ✓ 新浪上海: {len(items)} 条")
    except Exception as e:
        print(f"  ✗ 新浪上海: {str(e)[:50]}")
    
    return items

def fetch_shanghai_news():
    """主抓取函数"""
    items = []
    
    print("\n=== 抓取上海新闻 ===")
    
    # 1. 澎湃新闻（官网抓取）
    items.extend(fetch_thepaper())
    
    # 2. 东方网
    items.extend(fetch_eastday())
    
    # 3. 新浪上海
    items.extend(fetch_sina_shanghai())
    
    # 4. 嘉定精选（手动维护）
    print("\n🏠 嘉定精选")
    jiading_manual = [
        {
            "title": "🏠 嘉定新城建设提速，多个重大项目集中开工",
            "link": "https://www.jiading.gov.cn/",
            "summary": "嘉定区推动新城建设，聚焦科技创新",
            "source": "嘉定发布",
            "time": datetime.now().strftime("%m-%d"),
            "isNew": True,
            "score": 3
        },
        {
            "title": "👥 南翔镇加装电梯工程又有新进展，多个小区完成签约",
            "link": "https://www.jiading.gov.cn/",
            "summary": "南翔镇推进老旧小区加装电梯",
            "source": "南翔镇",
            "time": datetime.now().strftime("%m-%d"),
            "isNew": True,
            "score": 3
        },
    ]
    items.extend(jiading_manual)
    print(f"  ✓ 嘉定精选: {len(jiading_manual)} 条")
    
    # 去重
    seen = set()
    unique_items = []
    for item in items:
        if item['title'] not in seen:
            seen.add(item['title'])
            unique_items.append(item)
    
    # 按相关度排序
    unique_items.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    print(f"\n✅ 上海新闻总计: {len(unique_items)} 条")
    return unique_items

if __name__ == '__main__':
    news = fetch_shanghai_news()
    print(f"\n来源统计:")
    sources = {}
    for item in news:
        src = item['source']
        sources[src] = sources.get(src, 0) + 1
    for src, count in sources.items():
        print(f"  {src}: {count}条")
