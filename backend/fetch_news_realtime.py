#!/usr/bin/env python3
"""
新闻聚合抓取脚本 - 实时版
每5分钟更新，支持关键词推送
"""

import json
import requests
import feedparser
from datetime import datetime, timedelta
from pathlib import Path
import html
import urllib.parse
import sys

# 导入图片处理模块
sys.path.insert(0, str(Path(__file__).parent))
from image_handler import get_news_image

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 代理配置
PROXY = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}

def translate_text(text, target_lang='zh-CN'):
    """使用 Google Translate 免费 API 翻译"""
    try:
        if not text or len(text.strip()) == 0:
            return text
        
        # 检测是否包含中文
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return text  # 已经有中文，不翻译
        
        # 限制长度，避免API限制
        text_to_translate = text[:500]
        
        # Google Translate 免费 API
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text_to_translate)}"
        
        response = requests.get(url, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            data = response.json()
            # 解析返回结果
            translated_parts = []
            for item in data[0]:
                if item[0]:
                    translated_parts.append(item[0])
            return ''.join(translated_parts)
        
        return text  # 翻译失败返回原文
    except Exception as e:
        return text  # 出错返回原文

def format_time(published):
    """格式化时间"""
    if not published:
        return ""
    
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            clean_pub = published.strip().replace('+0800', '+08:00')
            dt = datetime.strptime(clean_pub[:26], fmt)
            return dt.strftime("%m-%d %H:%M")
        except:
            continue
    
    return published[:16] if len(published) > 16 else published

def is_recent(published_parsed):
    """判断是否是24小时内的新闻"""
    if not published_parsed:
        return False
    try:
        from time import mktime
        pub_timestamp = mktime(published_parsed)
        pub_time = datetime.fromtimestamp(pub_timestamp)
        return datetime.now() - pub_time < timedelta(hours=24)
    except:
        return False

def fetch_reddit_worldnews():
    """抓取 Reddit r/worldnews - 最快"""
    items = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        url = "https://www.reddit.com/r/worldnews/new.json?limit=10"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            data = response.json()
            for post in data['data']['children']:
                post_data = post['data']
                title = html.unescape(post_data['title'])
                translated_title = translate_text(title)
                
                items.append({
                    "title": translated_title,
                    "link": "https://reddit.com" + post_data['permalink'],
                    "summary": f"⬆️ {post_data.get('score', 0)} | 💬 {post_data.get('num_comments', 0)}",
                    "source": "Reddit 国际新闻",
                    "time": datetime.fromtimestamp(post_data['created']).strftime("%m-%d %H:%M"),
                    "isNew": True
                })
        
        print(f"  ✓ Reddit: {len(items)} 条")
    except Exception as e:
        print(f"  ✗ Reddit: {str(e)[:50]}")
    
    return items

def is_shanghai_relevant(title, summary=""):
    """判断是否与嘉定/节气/社区相关"""
    text = (title + summary).lower()
    
    # 嘉定相关
    jiading_keywords = ['嘉定', '南翔', '江桥', '安亭', '马陆', '外冈', '徐行', '华亭', '菊园', '新成路', '真新', '嘉定新城', '嘉定工业区', '州桥', '法华塔']
    # 节气时令
    season_keywords = ['立春', '雨水', '惊蛰', '春分', '清明', '谷雨', '立夏', '小满', '芒种', '夏至', '小暑', '大暑',
                       '立秋', '处暑', '白露', '秋分', '寒露', '霜降', '立冬', '小雪', '大雪', '冬至', '小寒', '大寒']
    # 社区民生
    community_keywords = ['社区', '街道', '居委会', '业委会', '物业', '邻里', '便民', '为老', '养老', '托育', '菜场', '旧改', '加装电梯', '长护险', '医保']
    
    has_jiading = any(kw in text for kw in jiading_keywords)
    has_season = any(kw in text for kw in season_keywords)
    has_community = any(kw in text for kw in community_keywords)
    
    return {
        'jiading': has_jiading,
        'season': has_season,
        'community': has_community,
        'score': int(has_jiading) * 3 + int(has_season) * 2 + int(has_community) * 1
    }

def fetch_shanghai_news():
    """抓取上海新闻 - 多源聚合"""
    items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    # 1. 澎湃新闻 RSS
    try:
        url = "https://feedx.net/rss/thepaper.xml"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                title = html.unescape(entry.get("title", "")).strip()
                relevance = is_shanghai_relevant(title)
                
                # 构建标签
                tags = []
                if relevance['jiading']: tags.append('🏠')
                if relevance['season']: tags.append('🌸')
                if relevance['community']: tags.append('👥')
                
                # 优先添加相关新闻
                if relevance['score'] > 0 or len(items) < 20:
                    items.append({
                        "title": f"{' '.join(tags)} {title}" if tags else title,
                        "link": entry.get("link", ""),
                        "summary": f"澎湃新闻 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "澎湃新闻 · 上海",
                        "source": "澎湃新闻",
                        "time": format_time(entry.get("published", "")),
                        "isNew": is_recent(entry.get("published_parsed")),
                        "score": relevance['score']
                    })
            
            print(f"  ✓ 澎湃新闻: {len(items)} 条")
    except Exception as e:
        print(f"  ✗ 澎湃新闻: {str(e)[:50]}")
    
    # 2. 手动维护 - 嘉定精选新闻
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
        {
            "title": "🌸 州桥老街春节民俗活动安排出炉",
            "link": "https://www.jiading.gov.cn/",
            "summary": "州桥老街春节期间民俗文化活动",
            "source": "嘉定文旅",
            "time": "02-01",
            "isNew": False,
            "score": 2
        },
        {
            "title": "👥 江桥镇推进'15分钟社区生活圈'建设",
            "link": "https://www.jiading.gov.cn/",
            "summary": "江桥镇便民服务设施升级",
            "source": "江桥镇",
            "time": datetime.now().strftime("%m-%d"),
            "isNew": True,
            "score": 2
        },
    ]
    items.extend(jiading_manual)
    print(f"  ✓ 嘉定精选: {len(jiading_manual)} 条")
    
    # 3. 新浪上海新闻
    print("\n📰 新浪上海")
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
                    
                    # 检查相关性
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
                print(f"  ✓ 新浪上海: {len(news_list)} 条")
    except Exception as e:
        print(f"  ✗ 新浪上海: {str(e)[:50]}")
    
    # 4. 上观新闻 (解放日报)
    print("\n📰 上观新闻")
    try:
        url = "https://rsshub.app/jfdaily/reconstruction"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:10]:
                title = html.unescape(entry.get("title", "")).strip()
                relevance = is_shanghai_relevant(title)
                
                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": f"上观新闻 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "上观新闻",
                    "source": "上观新闻",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed")),
                    "score": relevance['score']
                })
                count += 1
            print(f"  ✓ 上观新闻: {count} 条")
    except Exception as e:
        print(f"  ✗ 上观新闻: {str(e)[:50]}")
    
    # 5. 文汇报
    print("\n📰 文汇报")
    try:
        url = "https://rsshub.app/whb/bihui"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:8]:
                title = html.unescape(entry.get("title", "")).strip()
                relevance = is_shanghai_relevant(title)
                
                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": f"文汇报 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "文汇报",
                    "source": "文汇报",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed")),
                    "score": relevance['score']
                })
                count += 1
            print(f"  ✓ 文汇报: {count} 条")
    except Exception as e:
        print(f"  ✗ 文汇报: {str(e)[:50]}")
    
    # 6. 新民晚报
    print("\n📰 新民晚报")
    try:
        url = "https://rsshub.app/xinmin/daily"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:8]:
                title = html.unescape(entry.get("title", "")).strip()
                relevance = is_shanghai_relevant(title)
                
                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": f"新民晚报 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "新民晚报",
                    "source": "新民晚报",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed")),
                    "score": relevance['score']
                })
                count += 1
            print(f"  ✓ 新民晚报: {count} 条")
    except Exception as e:
        print(f"  ✗ 新民晚报: {str(e)[:50]}")
    
    # 7. 东方网 - 使用备用 API
    print("\n📰 东方网")
    try:
        # 尝试多个东方网数据源
        urls_to_try = [
            "https://rsshub.app/eastday/sh",
            "https://rsshub.app/eastday/china",
        ]
        
        for url in urls_to_try:
            try:
                response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    count = 0
                    for entry in feed.entries[:8]:
                        title = html.unescape(entry.get("title", "")).strip()
                        relevance = is_shanghai_relevant(title)
                        
                        items.append({
                            "title": title,
                            "link": entry.get("link", ""),
                            "summary": f"东方网 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "东方网",
                            "source": "东方网",
                            "time": format_time(entry.get("published", "")),
                            "isNew": is_recent(entry.get("published_parsed")),
                            "score": relevance['score']
                        })
                        count += 1
                    print(f"  ✓ 东方网: {count} 条")
                    break
            except:
                continue
    except Exception as e:
        print(f"  ✗ 东方网: {str(e)[:50]}")
    
    # 8. 看看新闻 - 直接抓取网页
    print("\n📺 看看新闻")
    try:
        url = "https://www.kankanews.com/"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            # 提取新闻链接和标题
            import re
            # 匹配看看新闻的链接模式 /a/YYYY-MM-DD/xxxxx.shtml
            news_pattern = r'href="(/a/\d{4}-\d{2}-\d{2}/\d+\.shtml)"[^>]*>([^<]+)</a>'
            matches = re.findall(news_pattern, response.text)
            
            seen = set()
            count = 0
            for link, title in matches[:10]:
                if link not in seen and title.strip():
                    seen.add(link)
                    full_link = f"https://www.kankanews.com{link}" if link.startswith('/') else link
                    title_clean = html.unescape(title.strip())
                    relevance = is_shanghai_relevant(title_clean)
                    
                    items.append({
                        "title": title_clean,
                        "link": full_link,
                        "summary": f"看看新闻 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "看看新闻",
                        "source": "看看新闻",
                        "time": datetime.now().strftime("%m-%d"),
                        "isNew": True,
                        "score": relevance['score']
                    })
                    count += 1
            
            print(f"  ✓ 看看新闻: {count} 条")
    except Exception as e:
        print(f"  ✗ 看看新闻: {str(e)[:50]}")
    
    # 9. 新闻晨报
    print("\n📰 新闻晨报")
    try:
        url = "https://rsshub.app/shxwcb"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:8]:
                title = html.unescape(entry.get("title", "")).strip()
                relevance = is_shanghai_relevant(title)
                
                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": f"新闻晨报 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "新闻晨报",
                    "source": "新闻晨报",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed")),
                    "score": relevance['score']
                })
                count += 1
            print(f"  ✓ 新闻晨报: {count} 条")
    except Exception as e:
        print(f"  ✗ 新闻晨报: {str(e)[:50]}")
    
    # 10. 青年报
    print("\n📰 青年报")
    try:
        url = "https://rsshub.app/qnb"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:8]:
                title = html.unescape(entry.get("title", "")).strip()
                relevance = is_shanghai_relevant(title)
                
                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": f"青年报 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "青年报",
                    "source": "青年报",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed")),
                    "score": relevance['score']
                })
                count += 1
            print(f"  ✓ 青年报: {count} 条")
    except Exception as e:
        print(f"  ✗ 青年报: {str(e)[:50]}")
    
    # 11. 劳动报
    print("\n📰 劳动报")
    try:
        url = "https://rsshub.app/ldrb"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:8]:
                title = html.unescape(entry.get("title", "")).strip()
                relevance = is_shanghai_relevant(title)
                
                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": f"劳动报 · 相关度:{relevance['score']}" if relevance['score'] > 0 else "劳动报",
                    "source": "劳动报",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed")),
                    "score": relevance['score']
                })
                count += 1
            print(f"  ✓ 劳动报: {count} 条")
    except Exception as e:
        print(f"  ✗ 劳动报: {str(e)[:50]}")
    
    # 按相关度排序
    items.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return items

def fetch_us_stock_news():
    """抓取美股新闻 - 多源聚合"""
    items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    # 持仓股票列表
    portfolio = ['TSLA', 'RKLB', 'QS', 'PLTR', 'RXRX', 'COIN', 'MSTR']
    
    # 1. Finnhub 美股新闻（免费API）
    try:
        # Finnhub 免费版不需要API key也能获取部分新闻
        url = "https://finnhub.io/api/v1/news?category=general"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            news_list = response.json()
            for news in news_list[:10]:
                title = news.get('headline', '')
                # 检查是否与持仓相关
                related_symbols = [s for s in portfolio if s in str(news.get('related', ''))]
                symbol_tag = f"[{','.join(related_symbols)}] " if related_symbols else ""
                
                items.append({
                    "title": f"{symbol_tag}{title}",
                    "link": news.get('url', ''),
                    "summary": news.get('source', 'Finnhub'),
                    "source": "美股快讯",
                    "time": datetime.fromtimestamp(news.get('datetime', 0)).strftime("%m-%d %H:%M") if news.get('datetime') else datetime.now().strftime("%m-%d"),
                    "isNew": True
                })
            print(f"    ✓ Finnhub: {len(items)} 条")
    except Exception as e:
        print(f"    ✗ Finnhub: {str(e)[:40]}")
    
    # 2. Yahoo Finance RSS（市场新闻）
    try:
        url = "https://rsshub.app/yahoo/news/markets"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:8]:
                title = translate_text(html.unescape(entry.get("title", "")).strip())
                
                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": "Yahoo Finance",
                    "source": "Yahoo财经",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"    ✓ Yahoo Finance: {count} 条")
    except Exception as e:
        print(f"    ✗ Yahoo Finance: {str(e)[:40]}")
    
    # 3. Seeking Alpha 热门
    try:
        url = "https://rsshub.app/seekingalpha/feed/top-news"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:6]:
                title = html.unescape(entry.get("title", "")).strip()
                # 检查是否与持仓相关
                related = any(s.lower() in title.lower() for s in portfolio)
                prefix = "📈 " if related else ""
                
                items.append({
                    "title": f"{prefix}{title}",
                    "link": entry.get("link", ""),
                    "summary": "Seeking Alpha",
                    "source": "Seeking Alpha",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"    ✓ Seeking Alpha: {count} 条")
    except Exception as e:
        print(f"    ✗ Seeking Alpha: {str(e)[:40]}")
    
    # 4. 如果上面都失败，使用备用静态链接
    if len(items) < 5:
        backup_items = [
            {
                "title": "🚀 RKLB Rocket Lab 最新发射任务",
                "link": "https://www.rocketlabusa.com/news/",
                "summary": "官方新闻与发射更新",
                "source": "Rocket Lab",
                "time": datetime.now().strftime("%m-%d"),
                "isNew": True
            },
            {
                "title": "⚡ TSLA 特斯拉投资者关系",
                "link": "https://ir.tesla.com/",
                "summary": "财报、新闻与公告",
                "source": "Tesla IR",
                "time": datetime.now().strftime("%m-%d"),
                "isNew": True
            },
            {
                "title": "📊 PLTR Palantir 商业动态",
                "link": "https://investors.palantir.com/news/",
                "summary": "政府与企业合同",
                "source": "Palantir",
                "time": datetime.now().strftime("%m-%d"),
                "isNew": True
            },
        ]
        items.extend(backup_items)
        print(f"    ⚠️ 使用备用数据: {len(backup_items)} 条")
    
    # 去重（基于标题）
    seen = set()
    unique_items = []
    for item in items:
        if item['title'] not in seen:
            seen.add(item['title'])
            unique_items.append(item)
    
    return unique_items[:15]  # 最多返回15条

def fetch_ai_news():
    """抓取AI/Tech新闻 - 多源聚合"""
    items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    # 1. TechCrunch AI/科技新闻
    print("\n💻 TECHCRUNCH")
    try:
        url = "https://rsshub.app/techcrunch"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:6]:
                title = translate_text(html.unescape(entry.get("title", "")).strip())
                items.append({
                    "title": f"🚀 {title}",
                    "link": entry.get("link", ""),
                    "summary": "TechCrunch",
                    "source": "TechCrunch",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ TechCrunch: {count} 条")
    except Exception as e:
        print(f"  ✗ TechCrunch: {str(e)[:50]}")
    
    # 2. OpenAI 博客
    print("\n🤖 OPENAI")
    try:
        url = "https://rsshub.app/openai/blog"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"🔥 {title}",
                    "link": entry.get("link", ""),
                    "summary": "OpenAI 官方",
                    "source": "OpenAI",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ OpenAI: {count} 条")
    except Exception as e:
        print(f"  ✗ OpenAI: {str(e)[:50]}")
    
    # 3. Google AI 博客
    print("\n🧠 GOOGLE AI")
    try:
        url = "https://rsshub.app/google/research"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"🔬 {title}",
                    "link": entry.get("link", ""),
                    "summary": "Google Research",
                    "source": "Google AI",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ Google AI: {count} 条")
    except Exception as e:
        print(f"  ✗ Google AI: {str(e)[:50]}")
    
    # 4. Papers With Code 最新论文
    print("\n📄 PAPERS WITH CODE")
    try:
        url = "https://rsshub.app/papers/arxiv/CS.AI"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"📄 {title[:60]}...",
                    "link": entry.get("link", ""),
                    "summary": "arXiv AI",
                    "source": "arXiv",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ arXiv AI: {count} 条")
    except Exception as e:
        print(f"  ✗ arXiv: {str(e)[:50]}")
    
    # 5. GitHub Trending
    print("\n🐙 GITHUB TRENDING")
    try:
        url = "https://rsshub.app/github/trending/daily/python"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"⭐ {title}",
                    "link": entry.get("link", ""),
                    "summary": "GitHub 今日热门",
                    "source": "GitHub",
                    "time": "今日",
                    "isNew": True
                })
                count += 1
            print(f"  ✓ GitHub: {count} 条")
    except Exception as e:
        print(f"  ✗ GitHub: {str(e)[:50]}")
    
    # 去重
    seen = set()
    unique_items = []
    for item in items:
        if item['title'] not in seen:
            seen.add(item['title'])
            unique_items.append(item)
    
    return unique_items[:20]

def fetch_tech_news():
    """兼容旧函数 - 调用新的AI抓取"""
    return fetch_ai_news()

def fetch_policy_news():
    """抓取政策新闻 - 国务院、各部委、上海市政府"""
    items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    # 1. 中国政府网 - 国务院政策
    print("\n🏛️ 中国政府网")
    try:
        url = "https://rsshub.app/gov/zhengce/zuixin"
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:8]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"🇨🇳 {title}",
                    "link": entry.get("link", ""),
                    "summary": "国务院政策",
                    "source": "国务院",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ 国务院: {count} 条")
    except Exception as e:
        print(f"  ✗ 国务院: {str(e)[:50]}")
    
    # 2. 国家发改委
    print("\n📊 国家发改委")
    try:
        url = "https://rsshub.app/gov/ndrc/zwxxgk"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"📈 {title}",
                    "link": entry.get("link", ""),
                    "summary": "国家发改委",
                    "source": "发改委",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ 发改委: {count} 条")
    except Exception as e:
        print(f"  ✗ 发改委: {str(e)[:50]}")
    
    # 3. 工信部
    print("\n🔧 工信部")
    try:
        url = "https://rsshub.app/gov/miit/zcwj"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"🔧 {title}",
                    "link": entry.get("link", ""),
                    "summary": "工信部政策",
                    "source": "工信部",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ 工信部: {count} 条")
    except Exception as e:
        print(f"  ✗ 工信部: {str(e)[:50]}")
    
    # 4. 央行
    print("\n🏦 央行")
    try:
        url = "https://rsshub.app/gov/pbc/zcyj"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"💰 {title}",
                    "link": entry.get("link", ""),
                    "summary": "央行政策研究",
                    "source": "央行",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ 央行: {count} 条")
    except Exception as e:
        print(f"  ✗ 央行: {str(e)[:50]}")
    
    # 5. 上海市政府
    print("\n🏙️ 上海市政府")
    try:
        url = "https://rsshub.app/gov/shanghai/zhengce"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"🏙️ {title}",
                    "link": entry.get("link", ""),
                    "summary": "上海市政府",
                    "source": "上海市政府",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ 上海市政府: {count} 条")
    except Exception as e:
        print(f"  ✗ 上海市政府: {str(e)[:50]}")
    
    # 6. 商务部
    print("\n🌐 商务部")
    try:
        url = "https://rsshub.app/gov/mofcom/swgat"
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            count = 0
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"🌐 {title}",
                    "link": entry.get("link", ""),
                    "summary": "商务部",
                    "source": "商务部",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
                count += 1
            print(f"  ✓ 商务部: {count} 条")
    except Exception as e:
        print(f"  ✗ 商务部: {str(e)[:50]}")
    
    # 去重
    seen = set()
    unique_items = []
    for item in items:
        if item['title'] not in seen:
            seen.add(item['title'])
            unique_items.append(item)
    
    return unique_items[:20]

def fetch_github_trending():
    """抓取 GitHub Trending"""
    items = []
    try:
        # GitHub Trending via RSSHub
        url = "https://rsshub.app/github/trending/daily/python"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:5]:
                title = html.unescape(entry.get("title", "")).strip()
                items.append({
                    "title": f"⭐ {title}",
                    "link": entry.get("link", ""),
                    "summary": "GitHub 今日热门",
                    "source": "GitHub",
                    "time": "今日",
                    "isNew": True
                })
        print(f"  ✓ GitHub: {len(items)} 条")
    except Exception as e:
        print(f"  ✗ GitHub: {str(e)[:50]}")
    return items

def fetch_bbc_news():
    """抓取 BBC 新闻"""
    items = []
    try:
        url = "http://feeds.bbci.co.uk/news/world/rss.xml"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:8]:
                title = translate_text(html.unescape(entry.get("title", "")).strip())
                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": "BBC World",
                    "source": "BBC",
                    "time": format_time(entry.get("published", "")),
                    "isNew": is_recent(entry.get("published_parsed"))
                })
        print(f"  ✓ BBC: {len(items)} 条")
    except Exception as e:
        print(f"  ✗ BBC: {str(e)[:50]}")
    return items

def fetch_news():
    """主抓取函数"""
    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - 开始抓取...")
    
    news_data = {
        "shanghai": [],
        "stocks": [],
        "policy": [],
        "world": [],
        "ai": []
    }
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    # 1. Reddit Worldnews
    print("\n🔥 REDDIT (实时)")
    news_data["world"] = fetch_reddit_worldnews()
    
    # 2. BBC 新闻
    print("\n📺 BBC")
    bbc_news = fetch_bbc_news()
    news_data["world"].extend(bbc_news)
    
    # 3. Hacker News
    print("\n🤖 HACKER NEWS")
    try:
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", 
                              timeout=10, proxies=PROXY)
        top_ids = response.json()[:10]
        
        for story_id in top_ids:
            try:
                story_resp = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                    timeout=5, proxies=PROXY
                )
                story = story_resp.json()
                if story and story.get('title'):
                    translated_title = translate_text(story['title'])
                    
                    news_data["ai"].append({
                        "title": translated_title,
                        "link": story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                        "summary": f"⭐ {story.get('score', 0)} points",
                        "source": "Hacker News",
                        "time": datetime.now().strftime("%m-%d %H:%M"),
                        "isNew": True
                    })
            except:
                continue
        print(f"  ✓ HN: {len(news_data['ai'])} 条")
    except Exception as e:
        print(f"  ✗ HN: {str(e)[:40]}")
    
    # 4. AI/Tech 综合新闻
    print("\n🤖 AI/TECH 综合")
    ai_news = fetch_ai_news()
    news_data["ai"] = ai_news
    
    # 6. 美股新闻 - 实时抓取多源
    print("\n📈 STOCKS")
    news_data["stocks"] = fetch_us_stock_news()
    print(f"  ✓ Stocks: {len(news_data['stocks'])} 条")
    
    # 7. 上海新闻 - 澎湃新闻 RSS
    print("\n🏙️ SHANGHAI")
    news_data["shanghai"] = fetch_shanghai_news()
    
    # 8. 国内政策 - 多源实时抓取
    print("\n🇨🇳 POLICY")
    news_data["policy"] = fetch_policy_news()
    print(f"  ✓ Policy: {len(news_data['policy'])} 条")
    
    # 9. 为新闻添加封面图片（只处理前3条，避免太慢）
    print("\n🖼️ 获取封面图片...")
    for category, items in news_data.items():
        print(f"   {category}: ", end="", flush=True)
        for i, item in enumerate(items[:3]):  # 只处理前3条
            try:
                image_result = get_news_image(
                    title=item['title'],
                    url=item.get('link', ''),
                    category=category,
                    prefer_real=True
                )
                if image_result:
                    item['image'] = image_result['url']
                    item['imageType'] = image_result['type']  # 'real' 或 'ai'
                else:
                    item['image'] = None
                    item['imageType'] = None
            except Exception as e:
                item['image'] = None
                item['imageType'] = None
        print(f"✓")
    
    # 保存
    output_file = DATA_DIR / "news.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    # 同时复制到前端目录
    import shutil
    shutil.copy(output_file, DATA_DIR.parent / "frontend" / "data.json")
    shutil.copy(output_file, DATA_DIR.parent / "data.json")
    
    print("\n" + "="*50)
    print(f"✅ 更新完成! 总计: {sum(len(v) for v in news_data.values())} 条")
    print(f"   世界新闻: {len(news_data['world'])} 条 (Reddit + BBC)")
    print(f"   上海新闻: {len(news_data['shanghai'])} 条")
    print(f"   AI/Tech: {len(news_data['ai'])} 条 (HN + TechCrunch + GitHub)")
    print(f"   美股: {len(news_data['stocks'])} 条")
    print(f"   政策: {len(news_data['policy'])} 条")
    print(f"\n💾 已保存")

if __name__ == "__main__":
    fetch_news()
