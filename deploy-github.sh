#!/bin/bash
# 部署到 GitHub Pages

REPO_NAME="news-aggregator"

echo "🚀 开始部署..."

# 创建 git 仓库
cd ~/.openclaw/workspace/news-aggregator
git init
git add .
git commit -m "Initial commit"

# 在 GitHub 创建仓库
echo "📦 创建 GitHub 仓库..."
gh repo create "$REPO_NAME" --public --source=. --push

# 启用 GitHub Pages
echo "🌐 启用 GitHub Pages..."
gh api repos/{owner}/"$REPO_NAME"/pages \
  --method POST \
  --input - <<< '{"source":{"branch":"main","path":"/frontend"}}'

echo ""
echo "✅ 部署完成!"
echo ""
echo "📱 手机访问地址:"
echo "   https://qj0826.github.io/news-aggregator/"
echo ""
echo "⏰ 自动更新: 每5分钟（通过 GitHub Actions）"
