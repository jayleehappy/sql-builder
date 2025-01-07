@echo off
echo 正在检查环境...
python -c "import pandas" 2>nul
if errorlevel 1 (
    echo 正在安装必要的依赖...
    pip install pandas openpyxl
)

echo 正在检查 PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

echo 正在清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo 正在打包应用程序...
pyinstaller --clean pyinstaller.spec

if errorlevel 1 (
    echo 打包失败！
    pause
    exit /b 1
)

echo 打包完成！
echo 程序位于 dist/SQL构建器 目录中
pause 