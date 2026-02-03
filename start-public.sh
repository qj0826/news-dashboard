#!/bin/bash
# 启动新闻聚合器 + Cloudflare 公网隧道

echo "🚀 启动新闻聚合器公网访问..."

# 1. 启动本地服务器
cd ~/.openclaw/workspace/news-aggregator/frontend
pkill -f "http.server 8888" 2>/dev/null
sleep 1
python3 -m http.server 8888 --bind 0.0.0.0 > /tmp/server.log 2>&1 &
echo "✅ 本地服务器: http://localhost:8888"

# 2. 启动 Cloudflare Tunnel
echo "🌐 启动公网隧道..."
cloudflared tunnel --url http://localhost:8888 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' &

sleep 5

# 3. 获取公网地址
URL=$(ps aux | grep cloudflared | grep -v grep | head -1 | xargs -0 2>/dev/null)

echo ""
echo "✅ 部署完成!"
echo ""
echo "📱 公网访问地址:"
ps aux | grep cloudflared | grep -v grep | head -1 2>/dev/null || echo "   等待生成中... (5秒后刷新)"
echo ""
echo "⏰ 保持此窗口运行，关闭后公网失效"
echo "🔄 每5分钟自动更新新闻"

# 保持运行
wait
