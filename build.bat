@echo off
setlocal
chcp 65001 >nul

if not exist 团子.ico (
  python 团子.py --gen-icon
)

python -m pip install --upgrade pip
python -m pip install pyinstaller

pyinstaller --onefile --noconsole --icon=团子.ico 团子.py

echo.
echo 打包完成：dist\团子.exe
pause

