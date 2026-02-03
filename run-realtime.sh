#!/bin/bash
# 实时新闻抓取 - 每5分钟运行

echo "🚀 启动实时新闻抓取服务..."
echo "⏱️  更新频率: 每5分钟"
echo "📱 推送: 突发新闻自动推送到 Telegram"
echo ""

cd "$(dirname "$0")"

while true; do
    python3 backend/fetch_news_realtime.py
    echo ""
    echo "😴 休眠5分钟... $(date '+%H:%M:%S')"
    sleep 300
done
