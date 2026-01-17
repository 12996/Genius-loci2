@echo off
echo 检查 Python 语法...
python -m py_compile main.py
if %errorlevel% equ 0 (
    echo ✓ main.py 语法正确
) else (
    echo ✗ main.py 语法错误
)

python -m py_compile routers.py
if %errorlevel% equ 0 (
    echo ✓ routers.py 语法正确
) else (
    echo ✗ routers.py 语法错误
)

python -m py_compile schemas.py
if %errorlevel% equ 0 (
    echo ✓ schemas.py 语法正确
) else (
    echo ✗ schemas.py 语法错误
)

python -m py_compile service.py
if %errorlevel% equ 0 (
    echo ✓ service.py 语法正确
) else (
    echo ✗ service.py 语法错误
)

python -m py_compile database.py
if %errorlevel% equ 0 (
    echo ✓ database.py 语法正确
) else (
    echo ✗ database.py 语法错误
)

python -m py_compile oss_storage.py
if %errorlevel% equ 0 (
    echo ✓ oss_storage.py 语法正确
) else (
    echo ✗ oss_storage.py 语法错误
)

python -m py_compile emotion_analyzer.py
if %errorlevel% equ 0 (
    echo ✓ emotion_analyzer.py 语法正确
) else (
    echo ✗ emotion_analyzer.py 语法错误
)

echo.
echo 语法检查完成!
pause
