# -*- coding: utf-8 -*-
r"""
浏览器端自测：验证 data.json 能被网页直接读取，且时钟/冲突算法在浏览器里算得对。

跑法：
    python "D:\qoder cn\heikeson\Qoder参赛包\脚本\浏览器自测.py"

它会在本包目录起一个临时 HTTP 服务（随机端口），用本机 Chrome 无头打开
`参考实现.html`，把里面 20 项断言的结果读出来，然后关掉服务。
全部 PASS 才算过。需要本机有 Playwright + Chrome（本机已装）。
"""
import http.server
import os
import socketserver
import sys
import threading
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, ".."))
PAGE = "参考实现.html"


def serve():
    """在本包目录起一个静态服务，返回 (httpd, port)"""
    os.chdir(PKG)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass        # 不要在控制台刷 HTTP 访问日志

    httpd = socketserver.TCPServer(("127.0.0.1", 0), Quiet)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def main():
    from playwright.sync_api import sync_playwright

    httpd, port = serve()
    url = f"http://127.0.0.1:{port}/{urllib.parse.quote(PAGE)}"
    print("服务：", url)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True,
                                        args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)

            # 等脚本跑完（结果框不再是省略号）
            page.wait_for_function(
                "() => { const t = document.querySelector('#result').textContent;"
                " return t && !t.includes('…') && !t.includes('加载中'); }",
                timeout=20000,
            )
            result = page.inner_text("#result").strip()
            table = page.inner_text("#out").strip()
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()

    print("\n--- 逐项 ---")
    print(table)
    print("\n--- 结论 ---")
    print(result)

    ok = result.startswith("ALL PASS")
    print("\n" + ("✅ 浏览器端全部通过" if ok else "❌ 浏览器端有失败项"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
