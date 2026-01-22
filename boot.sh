#!/bin/bash
# 遇到错误立即停止
set -e

# 尝试更新数据库结构
flask db upgrade

# 启动 Gunicorn
# -b :5000  -> 监听 5000 端口
# --access-logfile - -> 把日志打印到屏幕上，方便 Docker 查看
# --error-logfile - -> 把错误日志也打印到屏幕上
exec gunicorn -b :5000 --access-logfile - --error-logfile - microblog:app