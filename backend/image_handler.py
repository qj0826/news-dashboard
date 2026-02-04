#!/usr/bin/env python3
"""
新闻封面图片处理模块
- 抓取真实 og:image
- 无图时用 AI 生成
"""

import requests
import re
import urllib.parse
from pathlib import Path
import hashlib

# 代理配置
PROXY = {'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}

# Pollinations.ai API Key
POLLINATIONS_API_KEY = 'pk_AwoOxyA1F7BjqSCq'

# 分类对应的 AI 生成提示词
CATEGORY_PROMPTS = {
    'shanghai': '上海城市风光，现代建筑，暖色调，新闻配图风格，简洁大气',
    'world': '国际新闻，地球，全球视野，蓝色调，专业新闻配图',
    'ai': '人工智能，科技感，蓝色紫色渐变，未来感，AI新闻配图',
    'stocks': '金融股票，上升曲线，金色绿色，商务专业风格',
    'policy': '中国政府建筑，红色元素，庄重正式，政策新闻配图'
}

def fetch_og_image(url):
    """从网页抓取 og:image"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 限制页面大小，避免下载大文件
        response = requests.get(url, headers=headers, timeout=10, proxies=PROXY, stream=True)
        response.raise_for_status()
        
        # 只读取前 100KB（足够找到 meta 标签）
        content = b''
        for chunk in response.iter_content(chunk_size=1024):
            content += chunk
            if len(content) > 100000:
                break
        
        html = content.decode('utf-8', errors='ignore')
        
        # 查找 og:image
        patterns = [
            r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"',
            r'<meta[^>]*content="([^"]+)"[^>]*property="og:image"',
            r'<meta[^>]*name="twitter:image"[^>]*content="([^"]+)"',
            r'<meta[^>]*property="og:image:url"[^>]*content="([^"]+)"',
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
                
                # 验证图片 URL 是否可访问
                if validate_image_url(image_url):
                    return image_url
        
        return None
    except Exception as e:
        return None

def validate_image_url(url):
    """验证图片 URL 是否有效"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.head(url, headers=headers, timeout=5, proxies=PROXY, allow_redirects=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            return 'image' in content_type
        return False
    except:
        return False

def generate_ai_image(title, category='general'):
    """使用 Pollinations.ai 生成封面图片（使用 API Key 获得更快更稳定的服务）"""
    try:
        # 构建提示词
        base_prompt = CATEGORY_PROMPTS.get(category, '新闻配图，专业摄影风格，高质量')

        # 简化标题，去除特殊字符
        clean_title = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', title)[:30]

        # 组合提示词
        prompt = f"{base_prompt}，主题：{clean_title}，专业摄影，高清"

        # 使用 seed 确保相同标题生成相同图片（可缓存）
        seed = int(hashlib.md5(title.encode()).hexdigest(), 16) % 10000

        # Pollinations.ai API（带 key 获得更快生成速度）
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=600&height=750&seed={seed}&nologo=true&token={POLLINATIONS_API_KEY}"

        return image_url
    except Exception as e:
        return None

def get_news_image(title, url, category='general', prefer_real=False):
    """
    获取新闻封面图片
    
    Args:
        title: 新闻标题
        url: 新闻链接
        category: 分类
        prefer_real: 优先使用真实图片（默认False，因为抓取较慢）
    
    Returns:
        图片 URL 或 None
    """
    # 直接使用 AI 生成，速度更快
    image_url = generate_ai_image(title, category)
    if image_url:
        return {'url': image_url, 'type': 'ai'}
    
    return None

if __name__ == '__main__':
    # 测试
    test_cases = [
        ('上海发布新一轮优化营商环境方案', 'https://www.shanghai.gov.cn', 'shanghai'),
        ('SpaceX 星舰最新发射', 'https://www.spacex.com', 'world'),
        ('OpenAI 发布 GPT-5', 'https://openai.com', 'ai'),
    ]
    
    for title, url, cat in test_cases:
        print(f"\n📝 {title}")
        result = get_news_image(title, url, cat)
        if result:
            print(f"   {'📷' if result['type']=='real' else '🎨'} {result['type'].upper()}: {result['url'][:80]}...")
        else:
            print("   ❌ 无图片")
