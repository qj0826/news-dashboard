#!/usr/bin/env python3
"""
新闻封面图片获取 - 可靠方案
1. 尝试抓取新闻网页的 og:image
2. 失败时使用 Unsplash 随机图片（按分类）
"""

import requests
import re
import urllib.parse
from pathlib import Path

# 代理配置
PROXY = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}

# Unsplash 分类图片集（高质量、免版权）
UNSPLASH_IMAGES = {
    'shanghai': [
        'https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1505164294036-303dcdf97f8b?w=600&h=750&fit=crop',
    ],
    'world': [
        'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1524661135-423995f22d0b?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1517976487492-5750f3195933?w=600&h=750&fit=crop',
    ],
    'ai': [
        'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=600&h=750&fit=crop',
    ],
    'stocks': [
        'https://images.unsplash.com/photo-1611974765270-ca1258634369?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1468259943503-0c1955f43448?w=600&h=750&fit=crop',
    ],
    'policy': [
        'https://images.unsplash.com/photo-1577495508048-b635879837f1?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1555848962-6e79363ec58f?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1578393091816-a949886a18c7?w=600&h=750&fit=crop',
    ]
}

import hashlib

def get_unsplash_image(category, title):
    """根据分类获取 Unsplash 图片（使用标题hash确保一致性）"""
    images = UNSPLASH_IMAGES.get(category, UNSPLASH_IMAGES['world'])
    # 使用标题hash选择图片，确保相同标题总是得到相同图片
    index = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(images)
    return images[index]

def fetch_og_image(url):
    """从网页抓取 og:image（带缓存和超时）"""
    if not url or not url.startswith('http'):
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # 限制时间和大小
        response = requests.get(
            url, 
            headers=headers, 
            timeout=5,  # 5秒超时
            proxies=PROXY,
            stream=True
        )
        
        # 只读前50KB
        content = b''
        for chunk in response.iter_content(chunk_size=1024):
            content += chunk
            if len(content) > 50000:
                break
        
        html = content.decode('utf-8', errors='ignore')
        
        # 查找 og:image
        patterns = [
            r'<meta[^\u003e]*property="og:image"[^\u003e]*content="([^"]+)"',
            r'<meta[^\u003e]*content="([^"]+)"[^\u003e]*property="og:image"',
            r'<meta[^\u003e]*name="twitter:image"[^\u003e]*content="([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                image_url = match.group(1).strip()
                # 处理相对路径
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    parsed = urllib.parse.urlparse(url)
                    image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"
                
                # 验证是合法URL
                if image_url.startswith('http'):
                    return image_url
        
        return None
    except Exception as e:
        return None

def get_news_image(title, url, category='general'):
    """
    获取新闻封面图片
    1. 尝试抓取原网页 og:image
    2. 失败时使用 Unsplash 分类图片
    """
    # 1. 尝试抓取真实图片（对某些域名有效）
    if url and ('thepaper.cn' in url or 'sina.com.cn' in url or 'jiading' in url):
        real_image = fetch_og_image(url)
        if real_image:
            return {'url': real_image, 'type': 'real'}
    
    # 2. 使用 Unsplash 图片
    unsplash_url = get_unsplash_image(category, title)
    return {'url': unsplash_url, 'type': 'unsplash'}

if __name__ == '__main__':
    # 测试
    test_cases = [
        ('嘉定新城建设提速', 'https://www.jiading.gov.cn/', 'shanghai'),
        ('SpaceX 发射成功', 'https://www.spacex.com', 'world'),
        ('OpenAI GPT-5 发布', 'https://openai.com', 'ai'),
    ]
    
    for title, url, cat in test_cases:
        result = get_news_image(title, url, cat)
        print(f"\n📝 {title[:20]}...")
        print(f"   📷 {result['type']}: {result['url'][:60]}...")
