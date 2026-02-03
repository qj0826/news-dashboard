#!/usr/bin/env python3
"""
测试国内政策 RSS 源
"""

import requests
import feedparser

POLICY_RSS_SOURCES = [
    ("新华社", "http://www.news.cn/rss/world.xml"),
    ("中国政府网-政策", "https://rsshub.app/gov/zhengce"),
    ("中国政府网-最新", "https://rsshub.app/gov/zhengce/zuixin"),
    ("国务院", "https://rsshub.app/gov/guowuyuan"),
    ("发改委", "https://rsshub.app/gov/ndrc"),
    ("财政部", "https://rsshub.app/gov/mof"),
    ("商务部", "https://rsshub.app/gov/mofcom"),
]

PROXY = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}

def test_rss(name, url):
    try:
        print(f"\n📡 测试: {name}")
        print(f"   URL: {url}")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code != 200:
            print(f"   ❌ HTTP {response.status_code}")
            return False
        
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print(f"   ⚠️  无内容")
            return False
        
        print(f"   ✅ 成功! {len(feed.entries)} 条")
        if feed.entries:
            first = feed.entries[0]
            print(f"   📰 示例: {first.get('title', '无标题')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 错误: {str(e)[:60]}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🔍 测试国内政策 RSS 源")
    print("="*60)
    
    working_sources = []
    
    for name, url in POLICY_RSS_SOURCES:
        if test_rss(name, url):
            working_sources.append((name, url))
    
    print("\n" + "="*60)
    print(f"✅ 可用源: {len(working_sources)} 个")
    for name, url in working_sources:
        print(f"   • {name}: {url}")
