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

# 主题关键词图片库 - 根据标题内容匹配
TOPIC_IMAGES = {
    # 城市建设
    '城市': [
        'https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1514565131-fce0801e5785?w=600&h=750&fit=crop',
    ],
    # 科技/AI
    '科技': [
        'https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=600&h=750&fit=crop',
    ],
    'AI': [
        'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=600&h=750&fit=crop',
    ],
    # 金融/股票
    '金融': [
        'https://images.unsplash.com/photo-1611974765270-ca1258634369?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=600&h=750&fit=crop',
    ],
    '股票': [
        'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1468259943503-0c1955f43448?w=600&h=750&fit=crop',
    ],
    # 健康/医疗
    '医疗': [
        'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1584515933487-779824d29309?w=600&h=750&fit=crop',
    ],
    '健康': [
        'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&h=750&fit=crop',
    ],
    # 教育
    '教育': [
        'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=600&h=750&fit=crop',
    ],
    '学校': [
        'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1562774053-701939374585?w=600&h=750&fit=crop',
    ],
    # 环境/自然
    '环境': [
        'https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&h=750&fit=crop',
    ],
    '气候': [
        'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?w=600&h=750&fit=crop',
    ],
    # 交通/出行
    '交通': [
        'https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1494515843206-f3117d3f51b7?w=600&h=750&fit=crop',
    ],
    '地铁': [
        'https://images.unsplash.com/photo-1566737236500-c8ac43014a67?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1515165562839-978bbcf18277?w=600&h=750&fit=crop',
    ],
    # 商业/企业
    '企业': [
        'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&h=750&fit=crop',
    ],
    '商业': [
        'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&h=750&fit=crop',
    ],
    # 政策/政府
    '政策': [
        'https://images.unsplash.com/photo-1577495508048-b635879837f1?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=600&h=750&fit=crop',
    ],
    # 国际/地球
    '国际': [
        'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1524661135-423995f22d0b?w=600&h=750&fit=crop',
    ],
    # 社会/民生
    '社区': [
        'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1577563908411-5077b6dc7624?w=600&h=750&fit=crop',
    ],
    '养老': [
        'https://images.unsplash.com/photo-1576765608535-5f04d1e3f289?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1581579438747-1dc8d17bbce4?w=600&h=750&fit=crop',
    ],
    # 默认分类备用
    'default': [
        'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&h=750&fit=crop',
        'https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=600&h=750&fit=crop',
    ]
}

import hashlib

def match_topic(title):
    """根据标题匹配主题关键词"""
    # 定义关键词映射
    keywords_map = {
        '城市': ['城市', '建设', '规划', '新城', '嘉定', '南翔', '江桥', '安亭', '建筑', '楼盘'],
        '科技': ['科技', '技术', '创新', '研发', '智能', '数字化', '互联网'],
        'AI': ['AI', '人工智能', '大模型', 'ChatGPT', '机器学习', '算法', '神经网络'],
        '金融': ['金融', '银行', '投资', '理财', '基金', '证券', '经济'],
        '股票': ['股票', '股市', '股价', '涨跌', '特斯拉', 'TSLA', 'RKLB', 'PLTR'],
        '医疗': ['医疗', '医院', '医生', '药物', '疫苗', '疾病', '健康', '医保'],
        '健康': ['健康', '养生', '运动', '健身', '饮食', '营养'],
        '教育': ['教育', '学校', '大学', '中学', '小学', '学生', '教师', '课程', '培训'],
        '环境': ['环境', '生态', '绿色', '环保', '污染', '保护'],
        '气候': ['气候', '天气', '气温', '降雨', '台风', '寒潮', '雾霾'],
        '交通': ['交通', '出行', '公路', '高速', '道路', '驾驶', '车辆'],
        '地铁': ['地铁', '轻轨', '轨道交通', '地铁线路'],
        '企业': ['企业', '公司', '集团', '创业', '商业', 'vivo', '特斯拉', 'SpaceX'],
        '商业': ['商业', '市场', '消费', '零售', '电商', '销售', '品牌'],
        '政策': ['政策', '政府', '国务院', '工信部', '央行', '法规', '规定'],
        '国际': ['国际', '全球', '世界', '美国', '欧洲', '日本', '联合国', '外交'],
        '社区': ['社区', '街道', '居委会', '物业', '小区', '邻里', '便民'],
        '养老': ['养老', '老人', '老龄化', '敬老院', '养老院', '长护险'],
    }
    
    title_lower = title.lower()
    for topic, keywords in keywords_map.items():
        for keyword in keywords:
            if keyword in title_lower:
                return topic
    return 'default'

def get_topic_image(title):
    """根据标题主题获取匹配的图片"""
    topic = match_topic(title)
    images = TOPIC_IMAGES.get(topic, TOPIC_IMAGES['default'])
    # 使用标题hash确保同一新闻总是同一图片
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
    1. 根据标题主题关键词匹配图片
    2. 同一主题的新闻有不同的图片（基于标题hash）
    """
    # 根据标题主题匹配图片
    image_url = get_topic_image(title)
    return {'url': image_url, 'type': 'topic'}

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
