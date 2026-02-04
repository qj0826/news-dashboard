import json
import os
import re
import time
import random
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

# ================= 1. 深度定制新闻源 =================

# 模拟浏览器身份，防止被反爬虫拦截
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

RSS_SOURCES = {
    # 🏙️ 上海本地 (聚焦民生、本地政策)
    'shanghai': [
        'https://m.thepaper.cn/rss.jsp?nodeid=25635',  # 澎湃新闻-上海 (最权威)
        'https://www.shobserver.com/rss/index.html',    # 上观新闻 (官方党报)
    ],
    
    # 🤖 科技前沿 (AI、硬科技)
    'tech': [
        'https://www.36kr.com/feed',                    # 36氪 (创投第一线)
        'https://www.ifanr.com/feed',                   # 爱范儿 (产品与观点)
        'https://rss.cnbeta.com.tw/rss',                # cnBeta (硬核IT新闻)
    ],
    
    # 📈 美股与持仓 (替代 X：使用高频快讯源)
    # 这里选用了国内速度最快的美股资讯，专门覆盖机构持仓、盘前异动
    'us_stocks': [
        'https://feed.wallstreetcn.com/feed/live',      # 华尔街见闻-实时快讯 (最接近 Twitter 体验)
        'https://www.gelonghui.com/rss_feed.xml',       # 格隆汇-港美股 (专业的投资社区)
    ],
    
    # 🇨🇳 国内政策 (宏观经济、顶层设计)
    'policy': [
        'http://www.news.cn/politics/news.xml',         # 新华网-时政 (最官方)
        'https://m.thepaper.cn/rss.jsp?nodeid=25429',   # 澎湃新闻-时事 (解读较多)
        'http://www.chinanews.com/rss/gn.xml',          # 中国新闻网-国内
    ]
}

# ================= 2. 智能图库 (自动美化) =================
# 当新闻没有配图时，根据板块自动匹配一张高大上的背景图
DEFAULT_IMAGES = {
    'shanghai': [
        "https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=600&q=80", # 外滩
        "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=600&q=80", # 上海高楼
    ],
    'tech': [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&q=80", # 芯片
        "https://images.unsplash.com/photo-1531297420492-6029d146dc29?w=600&q=80", # 代码
    ],
    'us_stocks': [
        "https://images.unsplash.com/photo-1611974765270-ca1258822981?w=600&q=80", # 股市K线
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=600&q=80", # 华尔街牛
    ],
    'policy': [
        "https://images.unsplash.com/photo-1532375810709-75b1da00537c?w=600&q=80", # 严肃建筑
        "https://images.unsplash.com/photo-1529101091760-6149d4c46b27?w=600&q=80", # 笔与纸
    ]
}

# ================= 3. 核心抓取逻辑 =================

def parse_rss_feed(url, category):
    print(f"正在抓取 [{category}]: {url}")
    news_items = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.encoding = 'utf-8'
        
        # 处理 XML 解析
        try:
            root = ET.fromstring(response.content)
        except:
            # 容错处理：替换特殊字符
            content = response.text.replace('&', '&amp;')
            root = ET.fromstring(content)

        # 兼容 RSS 和 Atom 两种格式
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        
        for item in items[:20]: # 每个源多抓一点，取前20条
            try:
                # 1. 提取标题
                title = item.find('title').text if item.find('title') is not None else "最新资讯"
                
                # 2. 提取链接
                link = item.find('link').text if item.find('link') is not None else ""
                
                # 3. 提取简介
                description = ""
                desc_tag = item.find('description') or item.find('content:encoded')
                if desc_tag is not None and desc_tag.text:
                    # 去除 HTML 标签，只留纯文字
                    clean_text = re.sub(r'<[^>]+>', '', desc_tag.text)
                    description = clean_text[:120] + "..." if len(clean_text) > 120 else clean_text

                # 4. 提取时间
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                if pub_date:
                    # 简单截取时间字符串
                    pub_date = pub_date[:16]

                # 5. 智能提取图片
                image = ""
                if desc_tag is not None and desc_tag.text:
                    # 正则匹配 src="xxx.jpg"
                    img_match = re.search(r'src="(http[^"]+\.(jpg|png|jpeg|webp))"', desc_tag.text)
                    if img_match:
                        image = img_match.group(1)
                
                # 如果没图，从对应分类的图库里随机抽一张
                if not image:
                    image = random.choice(DEFAULT_IMAGES.get(category, DEFAULT_IMAGES['tech']))

                # 6. 来源标记
                source_name = "网络"
                if "thepaper" in url: source_name = "澎湃新闻"
                elif "shobserver" in url: source_name = "上观新闻"
                elif "36kr" in url: source_name = "36氪"
                elif "wallstreet" in url: source_name = "华尔街见闻"
                elif "gelonghui" in url: source_name = "格隆汇"
                elif "news.cn" in url: source_name = "新华网"
                elif "ifanr" in url: source_name = "爱范儿"

                # 存入列表
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
        print(f"❌ {url} 抓取出错: {e}")
        
    return news_items

def fetch_all_news():
    """主程序"""
    all_news = {
        "shanghai": [],
        "tech": [],
        "us_stocks": [],
        "policy": []
    }
    
    tasks = []
    # 开启5个线程并行抓取，速度更快
    with ThreadPoolExecutor(max_workers=5) as executor:
        for category, urls in RSS_SOURCES.items():
            for url in urls:
                tasks.append(executor.submit(parse_rss_feed, url, category))
    
    # 收集结果
    for future in tasks:
        items = future.result()
        if items:
            cat = items[0]['category']
            all_news[cat].extend(items)

    # 路径处理：保存到上级目录的 data.json
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 更新完成！总计获取新闻: {sum(len(v) for v in all_news.values())} 条")

if __name__ == "__main__":
    fetch_all_news()
