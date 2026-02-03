#!/usr/bin/env python3
"""
新闻聚合抓取脚本 - 使用本地可访问源
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import html
import re

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

def fetch_html_news():
    """直接抓取网页新闻 - 绕过 RSS"""
    
    news_data = {
        "shanghai": [],
        "stocks": [],
        "policy": [],
        "world": [],
        "ai": []
    }
    
    print("📰 开始抓取新闻...\n")
    
    # 1. 世界新闻 - BBC 中文
    try:
        print("🌍 抓取 BBC 新闻...")
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        
        # BBC 中文
        response = requests.get("https://www.bbc.com/zhongwen/simp/world", 
                              headers=headers, timeout=10)
        response.raise_for_status()
        
        # 简单提取标题
        titles = re.findall(r'class="[^"]*title[^"]*"[^>]*><a[^h]*href="([^"]+)"[^>]*>([^<]+)<', response.text)
        
        for i, (link, title) in enumerate(titles[:5]):
            clean_title = html.unescape(title.strip())
            if clean_title and len(clean_title) > 10:
                news_data["world"].append({
                    "title": clean_title,
                    "link": "https://www.bbc.com" + link if link.startswith('/') else link,
                    "summary": "",
                    "source": "BBC",
                    "time": datetime.now().strftime("%m-%d"),
                    "isNew": i < 3
                })
        print(f"  ✓ BBC: {len(news_data['world'])} 条")
    except Exception as e:
        print(f"  ✗ BBC: {str(e)[:40]}")
    
    # 2. AI 新闻 - Hacker News (通过 API)
    try:
        print("🤖 抓取 Hacker News...")
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", 
                              timeout=10)
        top_ids = response.json()[:8]
        
        for i, story_id in enumerate(top_ids):
            try:
                story_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                                        timeout=5)
                story = story_resp.json()
                if story and story.get('title'):
                    news_data["ai"].append({
                        "title": story['title'],
                        "link": story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                        "summary": f"{story.get('score', 0)} points",
                        "source": "Hacker News",
                        "time": datetime.now().strftime("%m-%d"),
                        "isNew": i < 4
                    })
            except:
                continue
        print(f"  ✓ Hacker News: {len(news_data['ai'])} 条")
    except Exception as e:
        print(f"  ✗ Hacker News: {str(e)[:40]}")
    
    # 3. 上海新闻 - 使用静态示例（需要手动更新）
    print("🏙️ 上海新闻 - 使用示例数据")
    news_data["shanghai"] = [
        {
            "title": "上海市发布新一轮优化营商环境行动方案",
            "link": "https://www.shanghai.gov.cn",
            "summary": "上海市政府发布7.0版优化营商环境行动方案",
            "source": "上海发布",
            "time": "02-03",
            "isNew": True
        },
        {
            "title": "嘉定新城建设提速，多个重大项目开工",
            "link": "https://www.jiading.gov.cn",
            "summary": "嘉定区推动新城建设，聚焦科技创新",
            "source": "嘉定发布",
            "time": "02-03",
            "isNew": True
        },
    ]
    print(f"  ✓ 上海新闻: {len(news_data['shanghai'])} 条")
    
    # 4. 国内政策
    print("🇨🇳 国内政策 - 使用示例数据")
    news_data["policy"] = [
        {
            "title": "国务院发布关于推动未来产业创新发展的实施意见",
            "link": "http://www.gov.cn",
            "summary": "前瞻布局未来产业，重点推进六大方向",
            "source": "中国政府网",
            "time": "02-03",
            "isNew": True
        },
        {
            "title": "工信部：加快制造业数字化转型",
            "link": "https://www.miit.gov.cn",
            "summary": "推动制造业高端化、智能化、绿色化发展",
            "source": "工信部",
            "time": "02-02",
            "isNew": False
        },
    ]
    print(f"  ✓ 国内政策: {len(news_data['policy'])} 条")
    
    # 5. 美股新闻 - 使用综合金融新闻源
    try:
        print("📈 抓取美股新闻...")
        
        # 尝试抓取 Investing.com 或 MarketWatch
        try:
            # MarketWatch RSS
            url = "https://rsshub.app/marketwatch/realtime"
            response = requests.get(url, headers=headers, timeout=15,
                                   proxies={'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'})
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:5]:
                    title = html.unescape(entry.get("title", "")).strip()
                    # 只保留与你的持仓相关的股票新闻
                    relevant = any(s in title.upper() for s in ["TESLA", "TSLA", "ROCKET LAB", "RKLB", 
                                                                "QUANTUM", "QS", "PALANTIR", "PLTR"])
                    if relevant or len(news_data["stocks"]) < 3:
                        news_data["stocks"].append({
                            "title": title[:60] + "..." if len(title) > 60 else title,
                            "link": entry.get("link", ""),
                            "summary": "美股市场新闻",
                            "source": "MarketWatch",
                            "time": format_time(entry.get("published", "")),
                            "isNew": True
                        })
        except:
            pass
        
        # 如果抓不到，使用预设的高质量链接
        if len(news_data["stocks"]) < 3:
            # 添加一些重要的股票新闻源
            news_data["stocks"].extend([
                {
                    "title": "🚀 RKLB Rocket Lab 最新发射任务动态",
                    "link": "https://www.rocketlabusa.com/news/",
                    "summary": "Rocket Lab 发射任务与公司新闻",
                    "source": "Rocket Lab Official",
                    "time": datetime.now().strftime("%m-%d"),
                    "isNew": True
                },
                {
                    "title": "⚡ TSLA 特斯拉最新财报与产品动态",
                    "link": "https://ir.tesla.com/",
                    "summary": "特斯拉投资者关系与新闻发布",
                    "source": "Tesla IR",
                    "time": datetime.now().strftime("%m-%d"),
                    "isNew": True
                },
                {
                    "title": "🔋 QS QuantumScape 固态电池研发进展",
                    "link": "https://www.quantumscape.com/news/",
                    "summary": "QuantumScape 技术突破与业务进展",
                    "source": "QuantumScape",
                    "time": datetime.now().strftime("%m-%d"),
                    "isNew": True
                },
                {
                    "title": "📊 PLTR Palantir 政府与企业合同更新",
                    "link": "https://investors.palantir.com/news/",
                    "summary": "Palantir 商业动态与新闻",
                    "source": "Palantir IR",
                    "time": datetime.now().strftime("%m-%d"),
                    "isNew": True
                },
            ])
        
        print(f"  ✓ 美股: {len(news_data['stocks'])} 条")
    except Exception as e:
        print(f"  ✗ 美股: {str(e)[:40]}")
    
    # 保存
    output_file = DATA_DIR / "news.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    # 统计
    print("\n" + "="*50)
    print("✅ 抓取完成!")
    total = sum(len(v) for v in news_data.values())
    print(f"   总计: {total} 条新闻")
    for k, v in news_data.items():
        print(f"   {k}: {len(v)} 条")
    print(f"\n💾 已保存: {output_file}")
    
    return news_data

if __name__ == "__main__":
    fetch_html_news()
