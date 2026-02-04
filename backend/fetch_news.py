#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import feedparser
import requests
import json
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

# 存放新闻数据的文件夹
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# RSS源配置（你可以在这里添加/修改新闻源）
RSS_SOURCES = {
    "上海新闻": [
        {"name": "澎湃新闻", "url": "https://www.thepaper.cn/rss.xml"},
        {"name": "上观新闻", "url": "https://www.jfdaily.com/rss"},
    ],
    "国内政策": [
        {"name": "新华社", "url": "http://www.xinhuanet.com/rss/xinhuanet_news.xml"},
    ],
    "世界新闻": [
        {"name": "BBC中文", "url": "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml"},
        {"name": "Reuters", "url": "https://www.reuters.com/rssFeed/worldNews"},
    ],
    "AI前沿": [
        {"name": "Hacker News", "url": "https://news.ycombinator.com/rss"},
    ]
}

# 假装是浏览器访问（这是关键！）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def fetch_image_from_url(url):
    """去原网页抓第一张图作为封面"""
    try:
        # 只尝试抓，不保证成功，超时10秒放弃
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 先找Open Graph图片（微信、知乎、新闻网站常用）
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content'):
            return og_img['content']
        
        # 再找第一张文章图片
        img = soup.find('img')
        if img and img.get('src'):
            img_url = img['src']
            # 如果是相对路径（如 /uploads/1.jpg），补全成完整URL
            if img_url.startswith('/'):
                from urllib.parse import urljoin
                img_url = urljoin(url, img_url)
            return img_url
            
    except Exception as e:
        print(f"抓图片失败 {url}: {e}")
    
    # 默认返回空，前端会显示占位图
    return ""

def parse_rss(source_name, feed_url):
    """解析单个RSS源"""
    news_list = []
    
    try:
        print(f"正在抓取: {source_name}...")
        
        # 下载RSS内容
        response = requests.get(feed_url, headers=HEADERS, timeout=15)
        response.encoding = response.apparent_encoding  # 自动识别中文编码
        
        # 解析RSS
        feed = feedparser.parse(response.text)
        
        for entry in feed.entries[:10]:  # 只取前10条，避免太多
            try:
                # 获取发布时间
                published = entry.get('published', entry.get('updated', ''))
                if not published:
                    published = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # 获取图片：先检查RSS里有没有，没有去网页抓
                image_url = ""
                # 方式1：RSS自带的媒体标签
                if 'media_content' in entry:
                    image_url = entry.media_content[0].get('url', '')
                elif 'enclosures' in entry and entry.enclosures:
                    image_url = entry.enclosures[0].get('href', '')
                
                # 方式2：如果RSS里没有，去原网页抓（慢一些，所以只抓前3条）
                if not image_url and news_list.index == 0:
                    image_url = fetch_image_from_url(entry.link)
                
                # 清理摘要（去掉HTML标签，限制长度）
                summary = entry.get('summary', entry.get('description', ''))
                if summary:
                    summary = re.sub(r'<[^>]+>', '', summary)  # 删除HTML标签
                    summary = summary[:150] + '...' if len(summary) > 150 else summary
                
                news_item = {
                    "title": entry.get('title', '无标题'),
                    "link": entry.get('link', ''),
                    "summary": summary,
                    "published": published,
                    "source": source_name,
                    "image": image_url
                }
                
                news_list.append(news_item)
                
            except Exception as e:
                print(f"解析单条新闻出错: {e}")
                continue
                
        print(f"✅ {source_name} 成功获取 {len(news_list)} 条")
        
    except Exception as e:
        print(f"❌ {source_name} 抓取失败: {e}")
    
    return news_list

def main():
    """主函数：抓取所有新闻并保存"""
    all_news = {
        "上海新闻": [],
        "国内政策": [],
        "世界新闻": [],
        "AI前沿": [],
        "美股持仓": []  # 这个需要另外处理，先留空
    }
    
    # 抓取配置好的RSS源
    for category, sources in RSS_SOURCES.items():
        for source in sources:
            news = parse_rss(source["name"], source["url"])
            if category in all_news:
                all_news[category].extend(news)
            time.sleep(1)  # 礼貌性等待1秒，避免被封
    
    # 保存到JSON文件
    output_file = os.path.join(DATA_DIR, 'news.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 全部完成！共保存到 {output_file}")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__
