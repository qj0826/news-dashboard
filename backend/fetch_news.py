import json
import os
import re
import random
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

# ================= 配置区域 =================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

RSS_SOURCES = {
    # 🏙️ 上海本地 (换成了更稳定的“中新网-上海”和“东方网”)
    'shanghai': [
        'http://www.sh.chinanews.com/rss/scroll-news.xml',  # 中新网上海 (非常稳定)
        'https://www.shobserver.com/rss/index.html',         # 上观新闻
    ],
    # 🤖 科技
    'tech': [
        'https://www.36kr.com/feed',
        'https://www.ifanr.com/feed',
    ],
    # 📈 美股
    'us_stocks': [
        'https://feed.wallstreetcn.com/feed/live',
        'https://www.gelonghui.com/rss_feed.xml',
    ],
    # 🇨🇳 政策
    'policy': [
        'http://www.news.cn/politics/news.xml',
        'http://www.chinanews.com/rss/gn.xml',
    ]
}

DEFAULT_IMAGES = {
    'shanghai': ["https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=600&q=80"],
    'tech': ["https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&q=80"],
    'us_stocks': ["https://images.unsplash.com/photo-1611974765270-ca1258822981?w=600&q=80"],
    'policy': ["https://images.unsplash.com/photo-1532375810709-75b1da00537c?w=600&q=80"]
}

def parse_rss_feed(url, category):
    print(f"正在抓取 [{category}]: {url}")
    news_items = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        # 自动检测编码，或者直接用 content (二进制) 交给 XML 解析器处理，防止 GBK 乱码
        content = response.content
        
        try:
            root = ET.fromstring(content)
        except:
            # 如果标准解析失败，尝试解码后手动修复
            try:
                text = response.content.decode('utf-8')
            except:
                try:
                    text = response.content.decode('gbk') # 尝试 GBK
                except:
                    text = response.text
            
            # 移除可能导致报错的特殊符号
            text = text.replace('&', '&amp;')
            root = ET.fromstring(text)

        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        
        for item in items[:20]:
            try:
                title = item.find('title').text if item.find('title') is not None else "无标题"
                link = item.find('link').text if item.find('link') is not None else ""
                
                # 描述处理
                description = ""
                desc_tag = item.find('description') or item.find('content:encoded')
                if desc_tag is not None and desc_tag.text:
                    clean_text = re.sub(r'<[^>]+>', '', desc_tag.text)
                    description = clean_text[:100] + "..."

                # 时间处理
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                if pub_date: pub_date = pub_date[:16]

                # 图片提取
                image = ""
                if desc_tag is not None and desc_tag.text:
                    img_match = re.search(r'src="(http[^"]+\.(jpg|png|jpeg|webp))"', desc_tag.text)
                    if img_match: image = img_match.group(1)
                
                if not image:
                    image = random.choice(DEFAULT_IMAGES.get(category, DEFAULT_IMAGES['tech']))

                # 来源标记
                source_name = "网络新闻"
                if "chinanews" in url: source_name = "中国新闻网"
                elif "shobserver" in url: source_name = "上观新闻"
                elif "36kr" in url: source_name = "36氪"
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
            except:
                continue
    except Exception as e:
        print(f"❌ {url} 出错: {e}")
        
    return news_items

def fetch_all_news():
    all_news = {"shanghai":[], "tech":[], "us_stocks":[], "policy":[]}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [executor.submit(parse_rss_feed, url, cat) for cat, urls in RSS_SOURCES.items() for url in urls]
        for future in tasks:
            items = future.result()
            if items:
                all_news[items[0]['category']].extend(items)

    # === 兜底机制：如果某个分类是空的，加一条“假新闻”提示 ===
    for cat in all_news:
        if not all_news[cat]:
            all_news[cat].append({
                "title": "正在获取最新资讯...",
                "link": "#",
                "time": "刚刚",
                "source": "系统提示",
                "image": random.choice(DEFAULT_IMAGES.get(cat, DEFAULT_IMAGES['tech'])),
                "summary": "该板块的新闻源正在更新中，请稍后刷新页面查看。",
                "category": cat
            })

    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    print("✅ 更新完成")

if __name__ == "__main__":
    fetch_all_news()
