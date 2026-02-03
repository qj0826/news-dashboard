#!/bin/bash
# 启动新闻聚合网站

cd "$(dirname "$0")"

echo "🚀 启动新闻聚合看板..."
echo ""

# 1. 先抓取新闻
echo "📡 正在抓取新闻..."
python3 backend/fetch_news.py

# 2. 启动本地服务器
echo ""
echo "🌐 启动本地服务器..."
echo ""
echo "网站地址: http://localhost:8080"
echo "按 Ctrl+C 停止"
echo ""

cd frontend
python3 -m http.server 8080
