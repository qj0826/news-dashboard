#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻抓取脚本 - 专为 News Dashboard 前端设计
解决：RSS抓取失败、无图片、编码乱码问题
"""

import feedparser
import requests
import json
import os
import re
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

# 配置路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'data.json')  # 注意前端读取的是 data.json

# 浏览器伪装头（关键！没这个会被网站拒绝）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# RSS 源配置（匹配你前端的5个分类）
RSS_SOURCES = {
    "shanghai": [  # 上海新闻
        {"name": "界面新闻", "url": "https://a.jiemian.com/rss/"},
        {"name": "上观新闻", "url": "https://www.shobserver.com/rss.xml"},
        {"name": "澎湃新闻", "url": "https://www.thepaper.cn/rss.xml"},  # 可能不稳定，有备用
    ],
    "policy": [  # 国内政策
        {"name": "人民网时政", "url": "http://rss.people.com.cn/rss/politics.xml"},
        {"name": "新华网时政", "url": "http://www.xinhuanet.com/rss/politics.xml"},
    ],
    "world": [  # 国际新闻
        {"name": "BBC中文", "url": "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml"},
        {"name": "FT中文网", "url": "https://www.ftchinese.com/rss/news"},
        {"name": "联合早报", "url": "https://www.zaobao.com/rss.xml"},
    ],
    "tech": [  # AI前沿/科技
        {"name": "Solidot", "url": "https://www.solidot.org/index.rss"},
        {"name": "Hacker News", "url": "https://news.ycombinator.com/rss"},
        {"name": "TechCrunch中文", "url": "https://techcrunch.cn/rss/"},
    ],
    "us_stocks": [  # 美股（先提供财经新闻，如需股价可后续添加）
        {"name": "新浪财经美股", "url": "https://rss.sina.com.cn/finance/usstock.xml"},
        {"name": "华尔街日报", "url": "https://cn.wsj.com/zh-hans/rss/markets.xml"},
    ]
}

def extract_image_from_entry(entry, source_url):
    """
    从RSS条目中提取图片（多种策略）
    """
    # 策略1：检查 media:content (最常见)
    if 'media_content' in entry and entry.media_content:
        for media in entry.media_content:
            if media.get('medium') == 'image' or media.get('type', '').startswith('image'):
                return media.get('url', '')
    
    # 策略2：检查 enclosures
    if 'enclosures' in entry and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'):
                return enc.get('href', '')
    
    # 策略3：检查 summary/description 中的 img 标签
    summary = entry.get('summary', entry.get('description', ''))
    if summary:
        img_match = re.search(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', summary)
        if img_match:
            return img_match.group(1)
    
    # 策略4：访问原网页抓取（比较慢，只抓前几条时可用）
    # 为了速度，这里暂不实现，如需可开启
    return ""

def fetch_rss_feed(source_name, feed_url, limit=8):
    """
    抓取单个RSS源
    """
    news_list = []
    
    try:
        print(f"📡 正在抓取: {source_name}...")
        
        # 下载RSS内容（带重试）
        for attempt in range(3):
            try:
                resp = requests.get(feed_url, headers=HEADERS, timeout=15)
                resp.encoding = resp.apparent_encoding  # 自动识别中文编码
                break
            except Exception as e:
                if attempt == 2:
                    print(f"   ❌ {source_name} 请求失败: {e}")
                    return []
                time.sleep(1)
        
        # 解析RSS
        feed = feedparser.parse(resp.text)
        
        for i, entry in enumerate(feed.entries[:limit]):
            try:
                # 提取发布时间
                published = ""
                if hasattr(entry, 'published'):
                    published = entry.published
                elif hasattr(entry, 'updated'):
                    published = entry.updated
                else:
                    published = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # 标准化时间格式（前端期望 2024-01-15 12:30 这种格式）
                try:
                    if 'T' in published:
                        # ISO格式 2024-01-15T12:30:00Z
                        dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        published = dt.strftime("%Y-%m-%d %H:%M")
                    else:
                        # 其他格式尝试解析
                        dt = datetime.strptime(published[:16], "%Y-%m-%d %H:%M")
                        published = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass  # 保持原样
                
                # 提取摘要（去除HTML标签）
                summary = entry.get('summary', entry.get('description', ''))
                if summary:
                    # 清理HTML标签
                    summary = re.sub(r'<[^>]+>', '', summary)
                    # 清理多余空白
                    summary = re.sub(r'\s+', ' ', summary).strip()
                    # 限制长度
                    if len(summary) > 200:
                        summary = summary[:200] + "..."
                else:
                    summary = "点击查看详情..."
                
                # 提取图片
                image_url = extract_image_from_entry(entry, entry.get('link', ''))
                
                # 如果没图，使用默认占位图（可选：你也可以准备几张默认图轮换）
                if not image_url:
                    # 使用picsum随机图作为占位，或留空让前端处理
                    image_url = f"https://picsum.photos/seed/{hash(entry.title) % 1000}/400/300"
                
                news_item = {
                    "title": entry.get('title', '无标题').strip(),
                    "link": entry.get('link', ''),
                    "summary": summary,
                    "source": source_name,
                    "time": published,
                    "image": image_url,
                    "category": ""  # 会在外层填充
                }
                
                news_list.append(news_item)
                
            except Exception as e:
                print(f"   ⚠️ 解析单条失败: {e}")
                continue
        
        print(f"   ✅ 成功获取 {len(news_list)} 条")
        
    except Exception as e:
        print(f"   ❌ {source_name} 出错: {e}")
    
    return news_list

def fetch_all_news():
    """
    抓取所有分类新闻
    """
    all_data = {
        "shanghai": [],
        "policy": [],
        "world": [],
        "tech": [],
        "us_stocks": []
    }
    
    # 抓取每个分类
    for category, sources in RSS_SOURCES.items():
        print(f"\n📂 分类: {category}")
        category_news = []
        
        for source in sources:
            news = fetch_rss_feed(source["name"], source["url"], limit=6)
            # 给每条新闻打上分类标签
            for item in news:
                item["category"] = category
            category_news.extend(news)
            time.sleep(0.5)  # 礼貌延迟，避免被封
        
        # 去重（按标题）
        seen_titles = set()
        unique_news = []
        for item in category_news:
            if item["title"] not in seen_titles:
                seen_titles.add(item["title"])
                unique_news.append(item)
        
        all_data[category] = unique_news
    
    # 确保 data 目录存在
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    # 保存为JSON（前端直接读取这个文件）
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 数据已保存: {DATA_FILE}")
    print(f"📊 总计: {sum(len(v) for v in all_data.values())} 条新闻")
    return all_data

if __name__ == "__main__":
    print("🚀 开始抓取新闻...")
    print("=" * 50)
    fetch_all_news()
    print("=" * 50)
    print("✅ 完成！")
