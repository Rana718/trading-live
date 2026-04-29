@echo off
setlocal

REM ============================================
REM 24時間配信システム 起動スクリプト (Windows)
REM - 仮想環境を作成/有効化
REM - 依存関係を同期
REM - uvで配信を起動
REM ============================================

cd /d %~dp0

REM uv が使えるか確認
where uv >nul 2>nul
if errorlevel 1 (
  echo [ERROR] uv が見つかりません。先に uv をインストールしてください。
  pause
  exit /b 1
)

REM .venv がなければ作成
if not exist ".venv" (
  echo [INFO] .venv を作成します...
  uv venv
)

REM 仮想環境を有効化
if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

REM 依存関係を同期
echo [INFO] 依存関係を同期します (uv sync)...
uv sync
if errorlevel 1 (
  echo [ERROR] uv sync に失敗しました。
  pause
  exit /b 1
)

REM 配信開始
echo [INFO] 配信を開始します (uv run python main.py)...
uv run python main.py

REM 終了時に画面を残す
pause
