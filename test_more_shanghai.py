#!/usr/bin/env python3
"""
测试更多上海新闻源 - 寻找可用源
"""

import requests
import feedparser

# 上海新闻源列表 - 多种尝试
SHANGHAI_SOURCES = [
    # 官方媒体
    ("澎湃新闻", "https://feedx.net/rss/thepaper.xml"),
    ("上观新闻", "https://rsshub.app/jfdaily/recommend"),
    ("界面新闻", "https://rsshub.app/jiemian/list/71"),  # 上海频道
    
    # 科技/创业
    ("36氪上海", "https://rsshub.app/36kr/search/articles/上海"),
    ("虎嗅", "https://rsshub.app/huxiu/article"),
    
    # 国际媒体上海频道
    ("路透上海", "https://rsshub.app/reuters/shanghai"),
    ("NYT上海", "https://cn.nytimes.com/rss/zh-hans/上海.xml"),
    
    # 社交媒体
    ("微博热搜上海", "https://rsshub.app/weibo/search/上海"),
    ("知乎上海", "https://rsshub.app/zhihu/zhuanlan/shanghai"),
    
    # 垂直媒体
    ("IT之家上海", "https://rsshub.app/ithome/it"),
    ("搜狐上海", "https://rsshub.app/sohu/mp/上海"),
    
    # 直接新闻源
    ("新浪上海", "https://news.sina.com.cn/roll/rss.xml"),
    ("网易上海", "https://news.163.com/special/00011K6L/rss_newstop.xml"),
    
    # 本地生活
    ("魔都吃货", "https://rsshub.app/wechat/mp/魔都吃货小分队"),
    ("上海发布", "https://rsshub.app/gov/shanghai/shipin"),
]

PROXY = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}

def test_source(name, url):
    """测试 RSS 源"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code != 200:
            return None
        
        feed = feedparser.parse(response.content)
        if not feed.entries:
            return None
        
        # 筛选上海相关内容
        shanghai_count = 0
        for entry in feed.entries[:15]:
            title = entry.get("title", "")
            if '上海' in title or '嘉定' in title or '徐汇' in title or '浦东' in title or '黄浦' in title:
                shanghai_count += 1
        
        return {
            'name': name,
            'url': url,
            'total': len(feed.entries),
            'shanghai': shanghai_count
        }
        
    except Exception as e:
        return None

if __name__ == "__main__":
    print("🔍 测试更多上海新闻源...\n")
    
    working = []
    for name, url in SHANGHAI_SOURCES:
        result = test_source(name, url)
        if result:
            working.append(result)
            print(f"✅ {result['name']}: {result['shanghai']}/{result['total']} 条上海相关")
        else:
            print(f"❌ {name}")
    
    print(f"\n🎯 找到 {len(working)} 个可用源")
    for src in working:
        print(f"   {src['name']}: {src['url']}")
