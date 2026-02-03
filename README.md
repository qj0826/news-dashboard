# 新闻线索看板

## 🚀 快速开始

```bash
# 启动看板
bash start.sh
```

然后浏览器打开: http://localhost:8080

## 📁 项目结构

```
news-aggregator/
├── frontend/
│   └── index.html          # 前端页面
├── backend/
│   └── fetch_news.py       # 新闻抓取脚本
├── data/
│   └── news.json           # 新闻数据（自动生成）
└── start.sh                # 启动脚本
```

## 🔧 功能特性

- **五栏布局**: 上海新闻 | 美股持仓 | 国内政策 | 世界新闻 | AI前沿
- **自动刷新**: 前端每5分钟自动拉取最新数据
- **新内容标记**: 24小时内的新闻显示红点
- **响应式设计**: 手机、平板、电脑都适配
- **一键刷新**: 手动刷新按钮

## 📡 数据来源

| 类别 | 来源 |
|------|------|
| 上海新闻 | 澎湃新闻、上观新闻 |
| 美股持仓 | RKLB, TSLA, QS, PLTR 等 |
| 国内政策 | 新华社 |
| 世界新闻 | BBC, Reuters |
| AI前沿 | Hacker News |

## 📝 后续可添加

- [ ] 添加更多 RSS 源（解放日报、新民晚报等）
- [ ] 接入 Yahoo Finance API 获取真实美股新闻
- [ ] 添加 X(Twitter) AI 大 V 监控
- [ ] GitHub Trending 爬虫
- [ ] 邮件/通知推送
- [ ] 关键词过滤与搜索

## 🔄 自动更新

添加到 cron（每小时更新）：
```bash
0 * * * * cd /path/to/news-aggregator && python3 backend/fetch_news.py
```
