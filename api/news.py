from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 读取本地数据文件（Vercel 部署时需要改用外部存储）
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'news.json')
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            # 返回示例数据
            data = {
                "shanghai": [{"title": "数据加载中...", "link": "#", "source": "系统", "time": ""}],
                "world": [],
                "ai": [],
                "stocks": [],
                "policy": []
            }
        
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        return
