import json
import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ================= 配置区域 =================

# 模拟浏览器身份，防止被拦截
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# RSS 数据源配置 (最稳定的获取方式)
RSS_SOURCES = {
    # 🏙️ 上海本地
    'shanghai': [
        'https://m.thepaper.cn/rss.jsp?nodeid=25635',  # 澎湃新闻-上海
        'https://www.shobserver.com/rss/index.html',    # 上观新闻
    ],
    # 🌍 国际新闻
    'world': [
        'https://rss.huanqiu.com/hq/world.xml',         # 环球网-国际
        'http://www.ftchinese.com/rss/news',            # FT中文网
    ],
    # 🤖 AI与科技
    'ai': [
        'https://www.36kr.com/feed',                    # 36氪 (科技创投)
        'https://www.ifanr.com/feed',                   # 爱范儿
    ],
    # 📈 美股与财经
    'stocks': [
        'https://feed.wallstreetcn.com/feed/live',      # 华尔街见闻
        'https://www.gelonghui.com/rss_feed.xml',       # 格隆汇
    ],
    # 🇨🇳 政策解读
    'policy': [
        'http://www.news.cn/politics/news.xml',         # 新华网-时政
        'https://m.thepaper.cn/rss.jsp?nodeid=25429',   # 澎湃新闻-时事
    ]
}

# 默认占位图（当新闻没有图片时使用）
DEFAULT_IMAGES = [
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=500&q=80",
    "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=500&q=80",
    "https://images.unsplash.com/photo-1557683316-973673baf926?w=500&q=80",
    "https://images.unsplash.com/photo-1526304640156-00011457838e?w=500&q=80",
]

# ================= 核心功能 =================

def parse_rss_feed(url, category):
    """解析单个 RSS 源"""
    print(f"正在抓取 [{category}]: {url}")
    news_items = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8' # 强制utf-8
        
        # 简单的XML解析
        try:
            root = ET.fromstring(response.content)
        except:
            # 尝试修复一些常见的XML格式错误
            content = response.text.replace('&', '&amp;')
            root = ET.fromstring(content)

        # 遍历新闻条目 (适配 RSS 2.0 和 Atom)
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        
        for item in items[:15]: # 每个源只取前15条
            try:
                # 获取标题
                title = item.find('title').text if item.find('title') is not None else "无标题"
                
                # 获取链接
                link = item.find('link').text if item.find('link') is not None else ""
                
                # 获取描述/摘要
                description = ""
                desc_tag = item.find('description') or item.find('content:encoded')
                if desc_tag is not None and desc_tag.text:
                    # 去除HTML标签，只留纯文本
                    description = re.sub(r'<[^>]+>', '', desc_tag.text)[:100] + "..."

                # 获取时间
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                # 简单格式化时间
                if pub_date:
                    try:
                        # 尝试将 UTC 格式转为简单格式
                        pub_date = pub_date[:16] 
                    except:
                        pass
                
                # 尝试提取图片 (从描述中找 img 标签)
                image = ""
                if desc_tag is not None and desc_tag.text:
                    img_match = re.search(r'src="(http[^"]+\.(jpg|png|jpeg))"', desc_tag.text)
                    if img_match:
                        image = img_match.group(1)
                
                # 如果没找到图片，给一个随机占位图，或者根据分类给特定图
                if not image:
                    # 这里你可以加逻辑，现在先留空，前端可以用CSS生成渐变
                    image = "" 

                # 来源识别
                source_name = "网络新闻"
                if "thepaper" in url: source_name = "澎湃新闻"
                elif "36kr" in url: source_name = "36氪"
                elif "huanqiu" in url: source_name = "环球网"
                elif "wallstreet" in url: source_name = "华尔街见闻"
                elif "news.cn" in url: source_name = "新华网"

                news_items.append({
                    "title": title.strip(),
                    "link": link,
                    "time": pub_date,
                    "source": source_name,
                    "image": image,
                    "summary": description,
                    "category": category
                })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"❌ 抓取失败 {url}: {e}")
        
    return news_items

def fetch_all_news():
    """主程序：并行抓取所有新闻"""
    all_news = {
        "shanghai": [],
        "world": [],
        "ai": [],
        "stocks": [],
        "policy": []
    }
    
    tasks = []
    # 使用线程池加快速度
    with ThreadPoolExecutor(max_workers=5) as executor:
        for category, urls in RSS_SOURCES.items():
            for url in urls:
                tasks.append(executor.submit(parse_rss_feed, url, category))
    
    # 收集结果
    for future in tasks:
        items = future.result()
        if items:
            # 拿到结果后，放入对应的分类
            cat = items[0]['category']
            all_news[cat].extend(items)

    # 保存到上一级目录的 data.json
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 更新完成！共获取新闻：{sum(len(v) for v in all_news.values())} 条")

if __name__ == "__main__":
    fetch_all_news()
