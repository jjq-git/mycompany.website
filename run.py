"""开发服务器入口: python run.py

环境变量:
  FLASK_DEBUG  默认 0 (生产). 本地开发开 debug 可设 FLASK_DEBUG=1
  FLASK_HOST   默认 127.0.0.1 (仅本机). 局域网联调设 0.0.0.0
  FLASK_PORT   默认 5000

局域网联调(FLASK_HOST=0.0.0.0)时 FLASK_DEBUG=1 依然可用: 交互式调试器会被
自动关掉, 模板热重载保留。

生产环境请使用 gunicorn / waitress / uWSGI 等 WSGI 服务器, 不要用 app.run。
"""
import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    # #10: 默认关 debug(与 docstring 一致)。debug=True 会开 Werkzeug 交互式调试器
    # (PIN 多次被绕过, 等同 RCE 入口), 本地调试要显式设 FLASK_DEBUG=1。
    debug = os.environ.get('FLASK_DEBUG', '0').strip() in ('1', 'true', 'True')
    host = os.environ.get('FLASK_HOST', '127.0.0.1').strip()
    port = int(os.environ.get('FLASK_PORT', '5000'))
    # 对外暴露(0.0.0.0 等)时只关掉 Werkzeug 交互式调试器, 不再整个拒绝启动。
    # FLASK_DEBUG 原先一个开关管着两件事: 交互式调试器(PIN 多次被绕过, 等同 RCE 入口)
    # 和模板热重载(TEMPLATES_AUTO_RELOAD, 见 app/__init__.py, 纯开发便利、无安全风险)。
    # 一律拒绝会逼得局域网联调只能关掉热重载、改模板不生效 —— 这里把两者解耦:
    # 调试器在对外暴露时永远关闭, 热重载照常保留。
    run_debug = debug
    if debug and host not in ('127.0.0.1', 'localhost'):
        print(f'提示: host={host} 对外暴露, 已自动关闭 Werkzeug 调试器(RCE 风险); 模板热重载仍生效。')
        run_debug = False
    app.run(debug=run_debug, host=host, port=port)
