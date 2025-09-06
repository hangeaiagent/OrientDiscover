#!/bin/bash

# OrientDirector 生产环境启动脚本
# 用于在AWS服务器上后台启动前端和后端服务

# 获取当前时间戳
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "🚀 启动 OrientDirector 生产环境服务"
echo "=================================="
echo "启动时间: $TIMESTAMP"
echo "服务器时间: $(date)"
echo ""

# 激活Conda环境
echo "🐍 激活Conda环境..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate orient

# 设置工作目录
cd /home/ec2-user/OrientDirector

# 检查Python版本
python --version

# 创建日志目录
mkdir -p logs

# 清空之前的日志文件
echo "🧹 清理旧日志文件..."
> logs/backend.log
> logs/frontend.log
echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务启动开始" >> logs/backend.log
echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务启动开始" >> logs/frontend.log

# 检查.env文件
if [ -f ".env" ]; then
    echo "✅ 找到.env配置文件"
    echo "🔑 检查环境变量..."
    if grep -q "GEMINI_API_KEY" .env; then
        echo "✅ GEMINI_API_KEY已配置"
    else
        echo "❌ 警告: .env文件中未找到GEMINI_API_KEY"
    fi
else
    echo "❌ 警告: 未找到.env文件"
fi

# 安装依赖
echo "📦 检查Python依赖..."
pip install -r requirements.txt

# 停止可能正在运行的服务
echo "🛑 停止现有服务..."
pkill -f "uvicorn.*main:app" || true
pkill -f "python.*start_frontend.py" || true
pkill -f "python.*start_backend.py" || true

# 等待端口释放
sleep 3

# 使用通用日志文件名
BACKEND_LOG="logs/backend.log"
FRONTEND_LOG="logs/frontend.log"

# 清空现有日志文件并添加启动时间戳
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "========================================" > "${BACKEND_LOG}"
echo "OrientDirector 后端服务启动" >> "${BACKEND_LOG}"
echo "启动时间: ${CURRENT_TIME}" >> "${BACKEND_LOG}"
echo "========================================" >> "${BACKEND_LOG}"
echo "" >> "${BACKEND_LOG}"

echo "========================================" > "${FRONTEND_LOG}"
echo "OrientDirector 前端服务启动" >> "${FRONTEND_LOG}"
echo "启动时间: ${CURRENT_TIME}" >> "${FRONTEND_LOG}"
echo "========================================" >> "${FRONTEND_LOG}"
echo "" >> "${FRONTEND_LOG}"

echo "📝 日志文件: ${BACKEND_LOG}, ${FRONTEND_LOG}"

# 启动后端服务（后台运行）
echo "🔧 启动后端服务 (端口 8001)..."
cd backend
# 确保在conda环境中启动
nohup bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate orient && python -m uvicorn main:app --host 0.0.0.0 --port 8001" >> "../logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
echo "后端服务PID: $BACKEND_PID"
cd ..

# 等待后端启动
sleep 5

# 启动前端服务（后台运行）
echo "🌐 启动前端服务 (端口 3001)..."
# 确保在conda环境中启动
nohup bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate orient && python start_frontend.py" >> "logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > logs/frontend.pid
echo "前端服务PID: $FRONTEND_PID"

# 等待服务启动
sleep 2

# 检查服务状态
echo ""
echo "📊 检查服务状态..."
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ 后端服务运行正常 (PID: $BACKEND_PID)"
else
    echo "❌ 后端服务启动失败"
    echo "📋 后端日志:"
    tail -10 logs/backend.log
fi

if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ 前端服务运行正常 (PID: $FRONTEND_PID)"
else
    echo "❌ 前端服务启动失败"
    echo "📋 前端日志:"
    tail -10 logs/frontend.log
fi

# 测试API连接
echo ""
echo "🔍 测试API连接..."
sleep 3
if curl -s https://spot.gitagent.io/api/health > /dev/null; then
    echo "✅ 后端API响应正常"
else
    echo "❌ 后端API无响应"
fi

echo ""
echo "✅ 服务启动完成！"
echo "启动完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "后端服务: https://spot.gitagent.io"
echo "前端服务: https://spot.gitagent.io"
echo "API文档: https://spot.gitagent.io/docs"
echo ""
echo "查看日志:"
echo "  后端: tail -f logs/backend.log"
echo "  前端: tail -f logs/frontend.log"
echo ""
echo "停止服务: ./stop_production.sh"