@echo off
chcp 65001 >nul
echo ========================================
echo MecAgent Docker 重新构建脚本
echo ========================================
echo.
echo 端口配置:
echo   - 前端: http://localhost:3008
echo   - 后端: http://localhost:8008
echo.

echo [1/5] 停止并删除旧容器...
docker-compose down
if %errorlevel% neq 0 (
    echo ⚠️ 停止容器失败（可能没有运行中的容器）
) else (
    echo ✅ 完成
)

echo.
echo [2/5] 删除旧镜像...
docker rmi assembly-manual-backend assembly-manual-frontend 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ 删除镜像失败（可能镜像不存在）
) else (
    echo ✅ 完成
)

echo.
echo [3/5] 构建新镜像（这可能需要几分钟）...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo ❌ 构建失败
    pause
    exit /b 1
)
echo ✅ 完成

echo.
echo [4/5] 启动容器...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ 启动失败
    pause
    exit /b 1
)
echo ✅ 完成

echo.
echo [5/5] 等待服务启动...
timeout /t 10 /nobreak >nul
echo ✅ 完成

echo.
echo ========================================
echo ✅ Docker 重新构建完成！
echo ========================================
echo.
echo 服务地址:
echo   - 前端: http://localhost:3008
echo   - 后端: http://localhost:8008
echo   - 后端健康检查: http://localhost:8008/api/health
echo.
echo 查看日志:
echo   docker-compose logs -f
echo.
echo 查看容器状态:
echo   docker-compose ps
echo.
echo 停止服务:
echo   docker-compose down
echo.
pause

