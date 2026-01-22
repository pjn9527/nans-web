# 1. 选择基础镜像：基于 Python 3.12 的轻量级版本
FROM python:3.12-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 复制依赖清单并安装
# 技巧：先复制 requirements.txt 再 pip install，利用 Docker 缓存加速构建
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# 4. 复制项目所有代码到容器里
COPY app app
COPY migrations migrations
COPY microblog.py config.py boot.sh ./

# 5. 给启动脚本赋予“可执行权限”
RUN chmod +x boot.sh

# 6. 设置环境变量
ENV FLASK_APP=microblog.py

# 7. 暴露端口 (虽然我们后面用 Docker Compose 内部通讯，但这行是好习惯)
EXPOSE 5000

# 8. 容器启动时执行的命令
ENTRYPOINT ["./boot.sh"]