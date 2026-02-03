#!/usr/bin/env python3
"""
测试更多上海新闻源
"""

import requests
import feedparser
import re

SHANGHAI_SOURCES = [
    # 主要媒体
    ("澎湃新闻", "https://feedx.net/rss/thepaper.xml"),
    ("解放日报", "https://rsshub.app/wechat/mp/解放日报"),
    ("新民晚报", "https://rsshub.app/wechat/mp/新民晚报"),
    
    # 上海本地
    ("上海发布", "https://rsshub.app/wechat/mp/上海发布"),
    ("新闻晨报", "https://rsshub.app/wechat/mp/新闻晨报"),
    ("东方网", "https://rsshub.app/eastday/sh"),
    
    # 嘉定相关
    ("上海嘉定", "https://rsshub.app/wechat/mp/上海嘉定"),
    ("嘉定发布", "https://www.jiading.gov.cn/rss"),
    
    # 社区/民生
    ("周到上海", "https://rsshub.app/wechat/mp/周到上海"),
    ("上海观察", "https://rsshub.app/wechat/mp/上观新闻"),
]

# 关键词过滤器
JIADING_KEYWORDS = ['嘉定', '嘉定区', '南翔', '江桥', '安亭', '马陆', '外冈', '徐行', '华亭', '菊园', '新成路', '真新', '嘉定新城', '嘉定工业区']
SEASON_KEYWORDS = ['立春', '雨水', '惊蛰', '春分', '清明', '谷雨', '立夏', '小满', '芒种', '夏至', '小暑', '大暑',
                   '立秋', '处暑', '白露', '秋分', '寒露', '霜降', '立冬', '小雪', '大雪', '冬至', '小寒', '大寒',
                   '春节', '元宵', '清明', '端午', '中秋', '重阳', '冬至', '腊八', '小年', '除夕']
COMMUNITY_KEYWORDS = ['社区', '街道', '居委会', '业委会', '物业', '邻里', '便民服务', '为老服务', '养老', '托育', '菜场', '旧改', '加装电梯']

def is_relevant(title, summary=""):
    """判断是否与嘉定/节气/社区相关"""
    text = (title + summary).lower()
    
    # 检查各类关键词
    has_jiading = any(kw in text for kw in JIADING_KEYWORDS)
    has_season = any(kw in text for kw in SEASON_KEYWORDS)
    has_community = any(kw in text for kw in COMMUNITY_KEYWORDS)
    
    return {
        'jiading': has_jiading,
        'season': has_season,
        'community': has_community,
        'score': int(has_jiading) * 3 + int(has_season) * 2 + int(has_community) * 1
    }

def test_source(name, url):
    """测试 RSS 源"""
    try:
        print(f"\n📡 测试: {name}")
        print(f"   URL: {url[:60]}...")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        
        # 使用代理
        proxies = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}
        response = requests.get(url, headers=headers, timeout=15, proxies=proxies)
        
        if response.status_code != 200:
            print(f"   ❌ HTTP {response.status_code}")
            return None
        
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print(f"   ⚠️ 无内容")
            return None
        
        # 分析内容相关性
        relevant_count = 0
        sample_items = []
        
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            result = is_relevant(title)
            
            if result['score'] > 0:
                relevant_count += 1
                tags = []
                if result['jiading']: tags.append('🏠嘉定')
                if result['season']: tags.append('🌸节气')
                if result['community']: tags.append('👥社区')
                
                sample_items.append({
                    'title': title[:50],
                    'tags': tags,
                    'score': result['score']
                })
        
        print(f"   ✅ 成功! {len(feed.entries)} 条内容")
        print(f"   🎯 相关新闻: {relevant_count} 条")
        
        if sample_items[:3]:
            print(f"   📰 示例:")
            for item in sorted(sample_items, key=lambda x: x['score'], reverse=True)[:3]:
                print(f"      • {item['title']}... {' '.join(item['tags'])}")
        
        return {
            'name': name,
            'url': url,
            'total': len(feed.entries),
            'relevant': relevant_count
        }
        
    except Exception as e:
        print(f"   ❌ 错误: {str(e)[:60]}")
        return None

if __name__ == "__main__":
    print("="*70)
    print("🔍 测试上海新闻源 (带嘉定/节气/社区关键词过滤)")
    print("="*70)
    
    working_sources = []
    
    for name, url in SHANGHAI_SOURCES:
        result = test_source(name, url)
        if result:
            working_sources.append(result)
    
    print("\n" + "="*70)
    print(f"✅ 可用源: {len(working_sources)} 个")
    print("\n按相关新闻数量排序:")
    for src in sorted(working_sources, key=lambda x: x['relevant'], reverse=True):
        print(f"   • {src['name']}: {src['relevant']} 条相关 / {src['total']} 条总计")
    
    print("\n💡 推荐配置:")
    for src in working_sources[:5]:
        print(f"   {src['name']}: {src['url']}")
