import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ossd_backend'))

from app import create_app

# 创建 Flask 应用（使用 development 配置）
app = create_app('development')

# 启动服务
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
