import json
import os
import re
import time
import random  # 新增：用于随机抽图
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

# ================= 配置区域 =================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

RSS_SOURCES = {
    'shanghai': [
        'https://m.thepaper.cn/rss.jsp?nodeid=25635',
        'https://www.shobserver.com/rss/index.html',
    ],
    'world': [
        'https://rss.huanqiu.com/hq/world.xml',
        'http://www.ftchinese.com/rss/news',
    ],
    'ai': [
        'https://www.36kr.com/feed',
        'https://www.ifanr.com/feed',
    ],
    'stocks': [
        'https://feed.wallstreetcn.com/feed/live',
        'https://www.gelonghui.com/rss_feed.xml',
    ],
    'policy': [
        'http://www.news.cn/politics/news.xml',
        'https://m.thepaper.cn/rss.jsp?nodeid=25429',
    ]
}

# 🖼️ 默认图库（当新闻没图时，随机从这里选一张，看起来更丰富）
DEFAULT_IMAGES = [
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&q=80", # 新闻纸
    "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600&q=80", # 报纸堆
    "https://images.unsplash.com/photo-1557683316-973673baf926?w=600&q=80",   # 抽象渐变
    "https://images.unsplash.com/photo-1526304640156-00011457838e?w=600&q=80", # 科技感
    "https://images.unsplash.com/photo-1503694987629-9479c8d9e918?w=600&q=80", # 办公桌
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&q=80", # 城市建筑
    "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&q=80", # 芯片科技
    "https://images.unsplash.com/photo-1611974765270-ca1258822981?w=600&q=80", # 股市K线
]

def parse_rss_feed(url, category):
    print(f"正在抓取 [{category}]: {url}")
    news_items = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        
        try:
            root = ET.fromstring(response.content)
        except:
            content = response.text.replace('&', '&amp;')
            root = ET.fromstring(content)

        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        
        for item in items[:15]:
            try:
                title = item.find('title').text if item.find('title') is not None else "无标题"
                link = item.find('link').text if item.find('link') is not None else ""
                
                description = ""
                desc_tag = item.find('description') or item.find('content:encoded')
                if desc_tag is not None and desc_tag.text:
                    description = re.sub(r'<[^>]+>', '', desc_tag.text)[:100] + "..."

                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                if pub_date:
                    try:
                        pub_date = pub_date[:16] 
                    except:
                        pass
                
                # 1. 优先尝试从内容里找图片
                image = ""
                if desc_tag is not None and desc_tag.text:
                    img_match = re.search(r'src="(http[^"]+\.(jpg|png|jpeg))"', desc_tag.text)
                    if img_match:
                        image = img_match.group(1)
                
                # 2. 如果没找到，随机分配一张好看的图
                if not image:
                    image = random.choice(DEFAULT_IMAGES)

                source_name = "网络新闻"
                if "thepaper" in url: source_name = "澎湃新闻"
                elif "36kr" in url: source_name = "36氪"
                elif "huanqiu" in url: source_name = "环球网"
                elif "wallstreet" in url: source_name = "华尔街见闻"
                elif "news.cn" in url: source_name = "新华网"
                elif "shobserver" in url: source_name = "上观新闻"
                elif "ftchinese" in url: source_name = "FT中文"

                news_items.append({
                    "title": title.strip(),
                    "link": link,
                    "time": pub_date,
                    "source": source_name,
                    "image": image,
                    "summary": description,
                    "category": category
                })
            except Exception:
                continue
                
    except Exception as e:
        print(f"❌ 抓取失败 {url}: {e}")
        
    return news_items

def fetch_all_news():
    all_news = {"shanghai":[], "world":[], "ai":[], "stocks":[], "policy":[]}
    
    tasks = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for category, urls in RSS_SOURCES.items():
            for url in urls:
                tasks.append(executor.submit(parse_rss_feed, url, category))
    
    for future in tasks:
        items = future.result()
        if items:
            cat = items[0]['category']
            all_news[cat].extend(items)

    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 更新完成！共获取新闻：{sum(len(v) for v in all_news.values())} 条")

if __name__ == "__main__":
    fetch_all_news()
