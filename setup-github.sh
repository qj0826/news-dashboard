#!/bin/bash
# GitHub 一键部署脚本

echo "🚀 新闻聚合器 GitHub 部署"
echo ""

# 检查 git
if ! command -v git &> /dev/null; then
    echo "❌ 请先安装 Git"
    exit 1
fi

# 检查 gh CLI
if ! command -v gh &> /dev/null; then
    echo "📦 安装 GitHub CLI..."
    brew install gh
fi

# 登录 GitHub
echo ""
echo "🔑 登录 GitHub..."
gh auth login --web

echo ""
echo "✅ 登录成功后，运行:"
echo "   cd ~/.openclaw/workspace/news-aggregator"
echo "   ./deploy-github.sh"
