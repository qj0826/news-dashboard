#!/usr/bin/env python3
"""
测试替代上海新闻源 - 直接 API/网页
"""

import requests
import json

PROXY = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}

def test_sina_shanghai():
    """测试新浪上海新闻"""
    try:
        # 新浪新闻 API
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2515&k=&num=20&r=0.123"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('result') and data['result'].get('data'):
                items = data['result']['data']
                print(f"✅ 新浪上海: {len(items)} 条")
                for item in items[:3]:
                    print(f"   • {item.get('title', '')[:40]}...")
                return True
    except Exception as e:
        print(f"❌ 新浪上海: {e}")
    return False

def test_toutiao_api():
    """测试今日头条"""
    try:
        url = "https://www.toutiao.com/api/pc/feed/?category=news_local"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Referer': 'https://www.toutiao.com/'
        }
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            print(f"✅ 今日头条: {len(response.text)} bytes")
            return True
    except Exception as e:
        print(f"❌ 今日头条: {e}")
    return False

def test_baidu_news():
    """测试百度新闻"""
    try:
        url = "https://news.baidu.com/ns?word=上海&tn=newsrss&cl=2&rn=20&ct=0"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            print(f"✅ 百度新闻上海: {len(response.text)} bytes")
            return True
    except Exception as e:
        print(f"❌ 百度新闻: {e}")
    return False

def test_so_news():
    """测试360新闻"""
    try:
        url = "https://news.so.com/ns?word=上海&tn=news&rank=pdate&size=20"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=15, proxies=PROXY)
        
        if response.status_code == 200:
            print(f"✅ 360新闻上海: {len(response.text)} bytes")
            return True
    except Exception as e:
        print(f"❌ 360新闻: {e}")
    return False

if __name__ == "__main__":
    print("🔍 测试替代方案...\n")
    
    test_sina_shanghai()
    test_toutiao_api()
    test_baidu_news()
    test_so_news()
