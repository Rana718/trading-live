"""
起動スクリプト — ダッシュボードを起動してブラウザを開きます。
配信の開始・停止はブラウザ画面から行えます。
"""
import subprocess
import sys
import time
import webbrowser
import os

BASE = os.path.dirname(__file__)
PYTHON = sys.executable

print("=" * 50)
print("  配信コントロールパネルを起動しています...")
print("  ブラウザが開いたら設定を確認して「配信開始」を押してください。")
print("=" * 50)

proc = subprocess.Popen(
    [PYTHON, os.path.join(BASE, "dashboard", "app.py")],
    cwd=BASE,
)

time.sleep(1.5)
webbrowser.open("http://localhost:5000")

try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
