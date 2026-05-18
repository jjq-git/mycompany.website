"""开发服务器入口: python run.py

环境变量:
  FLASK_DEBUG  默认 0 (生产). 本地开发开 debug 可设 FLASK_DEBUG=1
  FLASK_HOST   默认 127.0.0.1 (仅本机). 局域网联调可设 0.0.0.0
  FLASK_PORT   默认 5000

生产环境请使用 gunicorn / waitress / uWSGI 等 WSGI 服务器, 不要用 app.run。
"""
import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0').strip() in ('1', 'true', 'True')
    host = os.environ.get('FLASK_HOST', '127.0.0.1').strip()
    port = int(os.environ.get('FLASK_PORT', '5000'))
    app.run(debug=debug, host=host, port=port)
