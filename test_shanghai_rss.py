#!/usr/bin/env python3
"""
测试上海新闻 RSS 源
"""

import requests
import feedparser

# 上海新闻 RSS 候选源
SHANGHAI_RSS_SOURCES = [
    ("澎湃新闻", "https://feedx.net/rss/thepaper.xml"),
    ("澎湃新闻-备用", "https://rsshub.app/thepaper/featured"),
    ("上观新闻", "https://www.jfdaily.com/rss"),
    ("解放日报", "https://www.jfdaily.com/static/rss/jfdaily.xml"),
    ("新闻晨报", "https://rsshub.app/163/dy/2.xh"),
    ("东方网上海", "https://rsshub.app/eastday/sh"),
    ("新浪财经-上海", "https://rsshub.app/sina/finance"),
]

PROXY = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}

def test_rss(name, url):
    """测试 RSS 源是否可用"""
    try:
        print(f"\n📡 测试: {name}")
        print(f"   URL: {url}")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code != 200:
            print(f"   ❌ HTTP {response.status_code}")
            return False
        
        # 尝试解析
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print(f"   ⚠️  无内容 (可能是格式问题)")
            return False
        
        print(f"   ✅ 成功! {len(feed.entries)} 条内容")
        
        # 显示第一条作为示例
        if feed.entries:
            first = feed.entries[0]
            print(f"   📰 示例: {first.get('title', '无标题')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 错误: {str(e)[:60]}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🔍 测试上海新闻 RSS 源")
    print("="*60)
    
    working_sources = []
    
    for name, url in SHANGHAI_RSS_SOURCES:
        if test_rss(name, url):
            working_sources.append((name, url))
    
    print("\n" + "="*60)
    print(f"✅ 可用源: {len(working_sources)} 个")
    for name, url in working_sources:
        print(f"   • {name}")
        print(f"     {url}")
    
    if working_sources:
        print("\n💡 推荐使用:")
        for i, (name, url) in enumerate(working_sources[:3], 1):
            print(f"   {i}. {name}")
