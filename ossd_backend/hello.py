from app import create_app
import os

print("📡 正在加载环境变量...")
os.environ['FLASK_APP'] = 'hello.py'
os.environ['FLASK_ENV'] = 'development'

print("📡 正在创建应用...")
app = create_app('development')

print("📡 应用已创建，可用路由：")
for rule in app.url_map.iter_rules():
    print(f"  {rule.endpoint}: {rule.methods} {rule}")

if __name__ == '__main__':
    print("🚀 启动服务器...")
    app.run(host='0.0.0.0', port=8080, debug=True)