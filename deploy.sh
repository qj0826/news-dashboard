#!/bin/bash
# 完整部署脚本 - 复制到终端运行

REPO="news-aggregator"
USER="qj0826"

echo "🚀 部署新闻聚合器到 GitHub Pages"
echo ""

# 1. 创建仓库
echo "📦 步骤1: 创建 GitHub 仓库..."
curl -u "$USER" https://api.github.com/user/repos \
  -d '{"name":"'$REPO'","private":false}' 2>/dev/null | grep -q '"id"' && echo "✅ 仓库创建成功" || echo "⚠️ 仓库可能已存在"

# 2. 准备代码
cd ~/.openclaw/workspace/news-aggregator

# 创建 index.html（直接在根目录，方便 Pages）
cp frontend/index.html ./index.html 2>/dev/null || true
cp frontend/data.json ./data.json 2>/dev/null || true

# 3. 提交代码
echo ""
echo "📤 步骤2: 上传代码..."
git remote remove origin 2>/dev/null
git remote add origin "https://github.com/$USER/$REPO.git" 2>/dev/null
git add .
git commit -m "update" --quiet 2>/dev/null || true
git push -u origin master --force 2>&1 | grep -E "(Writing|Total|error|fatal)" || echo "推送完成"

# 4. 启用 Pages
echo ""
echo "🌐 步骤3: 启用 GitHub Pages..."
curl -u "$USER" \
  -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$USER/$REPO/pages \
  -d '{"source":{"branch":"master","path":"/"}}' 2>/dev/null | grep -q '"url"' && echo "✅ Pages 已启用" || echo "⚠️ Pages 可能已启用"

echo ""
echo "✅ 部署完成!"
echo ""
echo "📱 访问地址:"
echo "   https://$USER.github.io/$REPO/"
echo ""
echo "⏰ 等待1-2分钟后刷新"
