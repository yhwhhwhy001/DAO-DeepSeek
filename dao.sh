#!/bin/bash
# DAO Genesis 一键启动

DIR="$(cd "$(dirname "$0")" && pwd)"

# 杀掉旧进程
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null

echo "=== DAO Genesis ==="
echo "后端: http://localhost:8000"
echo "前端: http://localhost:5173"
echo ""

# 启动后端
cd "$DIR" && python3 run_web.py &
BACKEND_PID=$!

# 启动前端
cd "$DIR/client" && npm run dev -- --host &
FRONTEND_PID=$!

# 等待启动
sleep 3

# 打开浏览器
open http://localhost:5173

echo ""
echo "已启动！按 Ctrl+C 停止所有服务"

# 捕获退出信号
cleanup() {
    echo "正在停止..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# 等待
wait
