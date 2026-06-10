#!/bin/bash
# ============================================================
# 智能排课系统 - 宝塔面板一键部署脚本
# 使用方法: bash install.sh
# ============================================================

set -e

echo "========================================="
echo "  智能排课系统 - 一键部署脚本"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "请使用root用户运行此脚本"
    exit 1
fi

# -----------------------------------------------------------
# 配置项
# -----------------------------------------------------------
APP_DIR="/www/wwwroot/smart-schedule"
PYTHON_VERSION="3.10"
MYSQL_DB="smart_schedule"
MYSQL_USER="smart_schedule"
MYSQL_PASS=$(openssl rand -hex 12)
BACKEND_PORT=8000
SQL_DIR="$(cd "$(dirname "$0")/../sql" && pwd)"

# -----------------------------------------------------------
# 1. 检查并安装 Python 3.10
# -----------------------------------------------------------
echo ">>> 检查Python环境..."
if ! command -v python3.10 &> /dev/null; then
    echo ">>> 安装Python 3.10..."
    if command -v yum &> /dev/null; then
        yum install -y python3.10 python3.10-pip python3.10-devel 2>/dev/null || {
            echo "yum安装失败，尝试从源码编译..."
            yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel
            cd /tmp
            curl -O https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tgz
            tar -xzf Python-3.10.13.tgz
            cd Python-3.10.13
            ./configure --enable-optimizations
            make altinstall
            cd /
            rm -rf /tmp/Python-3.10.13 /tmp/Python-3.10.13.tgz
        }
    elif command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3.10 python3.10-pip python3.10-dev python3.10-venv 2>/dev/null || {
            echo "apt安装失败，尝试从deadsnakes PPA安装..."
            apt-get install -y software-properties-common
            add-apt-repository -y ppa:deadsnakes/ppa
            apt-get update
            apt-get install -y python3.10 python3.10-pip python3.10-dev python3.10-venv
        }
    else
        echo "不支持的操作系统，请手动安装Python 3.10"
        exit 1
    fi
fi

# 验证Python版本
PY_VERSION=$(python3.10 --version 2>&1)
echo "    Python版本: $PY_VERSION"

# -----------------------------------------------------------
# 2. 创建应用目录
# -----------------------------------------------------------
echo ">>> 创建应用目录..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/backups
mkdir -p $APP_DIR/logs

# -----------------------------------------------------------
# 3. 复制应用文件
# -----------------------------------------------------------
echo ">>> 复制应用文件..."
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -d "$SCRIPT_DIR/backend" ]; then
    cp -r $SCRIPT_DIR/backend $APP_DIR/
    echo "    后端代码已复制"
else
    echo "    警告: 未找到backend目录，请确认项目结构"
fi

if [ -d "$SCRIPT_DIR/frontend/dist" ]; then
    mkdir -p $APP_DIR/frontend
    cp -r $SCRIPT_DIR/frontend/dist $APP_DIR/frontend/
    echo "    前端代码已复制"
else
    echo "    警告: 未找到frontend/dist目录，请先构建前端"
    mkdir -p $APP_DIR/frontend
fi

# -----------------------------------------------------------
# 4. 安装Python依赖
# -----------------------------------------------------------
echo ">>> 安装Python依赖..."
if [ -f "$APP_DIR/backend/requirements.txt" ]; then
    python3.10 -m pip install --upgrade pip -q
    pip3.10 install -r $APP_DIR/backend/requirements.txt -q
    echo "    Python依赖安装完成"
else
    echo "    警告: 未找到requirements.txt，跳过依赖安装"
    # 安装常用依赖
    pip3.10 install fastapi uvicorn sqlalchemy pymysql bcrypt python-jose python-multipart redis aiofiles -q 2>/dev/null || true
fi

# -----------------------------------------------------------
# 5. 创建MySQL数据库
# -----------------------------------------------------------
echo ">>> 创建MySQL数据库..."
if command -v mysql &> /dev/null; then
    mysql -u root -e "CREATE DATABASE IF NOT EXISTS $MYSQL_DB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || {
        echo "    创建数据库失败，请检查MySQL是否运行以及root密码"
        echo "    您可以手动执行以下命令："
        echo "    mysql -u root -p -e \"CREATE DATABASE IF NOT EXISTS $MYSQL_DB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\""
        read -p "    MySQL root密码: " MYSQL_ROOT_PASS
        mysql -u root -p"$MYSQL_ROOT_PASS" -e "CREATE DATABASE IF NOT EXISTS $MYSQL_DB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    }

    mysql -u root -e "CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASS';" 2>/dev/null || true
    mysql -u root -e "GRANT ALL PRIVILEGES ON $MYSQL_DB.* TO '$MYSQL_USER'@'localhost';" 2>/dev/null || true
    mysql -u root -e "FLUSH PRIVILEGES;" 2>/dev/null || true
    echo "    数据库创建完成"
else
    echo "    警告: 未找到mysql命令，请确保MySQL已安装"
    MYSQL_PASS="请手动设置"
fi

# -----------------------------------------------------------
# 6. 导入数据库结构
# -----------------------------------------------------------
echo ">>> 导入数据库结构..."
if [ -f "$SQL_DIR/init_schema.sql" ]; then
    mysql -u root $MYSQL_DB < $SQL_DIR/init_schema.sql 2>/dev/null && echo "    数据库结构导入完成" || echo "    数据库结构导入失败，请手动导入"
else
    echo "    警告: 未找到init_schema.sql"
fi

if [ -f "$SQL_DIR/init_data.sql" ]; then
    mysql -u root $MYSQL_DB < $SQL_DIR/init_data.sql 2>/dev/null && echo "    初始数据导入完成" || echo "    初始数据导入失败，请手动导入"
else
    echo "    警告: 未找到init_data.sql"
fi

# -----------------------------------------------------------
# 7. 生成配置文件
# -----------------------------------------------------------
echo ">>> 生成配置文件..."
cat > $APP_DIR/backend/.env << EOF
# 数据库配置
DATABASE_URL=mysql+pymysql://$MYSQL_USER:$MYSQL_PASS@localhost:3306/$MYSQL_DB

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全密钥
SECRET_KEY=$(openssl rand -hex 32)

# 备份目录
BACKUP_DIR=$APP_DIR/backups

# 日志目录
LOG_DIR=$APP_DIR/logs

# 服务端口
PORT=$BACKEND_PORT

# 运行环境
ENVIRONMENT=production
EOF
chmod 600 $APP_DIR/backend/.env
echo "    配置文件已生成: $APP_DIR/backend/.env"

# -----------------------------------------------------------
# 8. 创建systemd服务
# -----------------------------------------------------------
echo ">>> 创建系统服务..."
cat > /etc/systemd/system/smart-schedule.service << EOF
[Unit]
Description=Smart Schedule System - 智能排课系统
After=network.target mysql.service redis.service
Wants=mysql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR/backend
ExecStart=/usr/bin/python3.10 -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --workers 4
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable smart-schedule
systemctl start smart-schedule
echo "    系统服务已创建并启动"

# 等待服务启动
sleep 3
if systemctl is-active --quiet smart-schedule; then
    echo "    服务运行正常"
else
    echo "    警告: 服务可能未正常启动，请检查日志: journalctl -u smart-schedule"
fi

# -----------------------------------------------------------
# 9. 配置Nginx
# -----------------------------------------------------------
echo ">>> 配置Nginx..."
NGINX_CONF_DIR=""
if [ -d "/www/server/panel/vhost/nginx" ]; then
    NGINX_CONF_DIR="/www/server/panel/vhost/nginx"
elif [ -d "/etc/nginx/conf.d" ]; then
    NGINX_CONF_DIR="/etc/nginx/conf.d"
elif [ -d "/etc/nginx/sites-available" ]; then
    NGINX_CONF_DIR="/etc/nginx/sites-available"
fi

if [ -n "$NGINX_CONF_DIR" ]; then
    cat > $NGINX_CONF_DIR/smart-schedule.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    # 前端静态文件
    location / {
        root /www/wwwroot/smart-schedule/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;

        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;

        # 请求体大小限制（用于数据导入）
        client_max_body_size 50m;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400s;
    }

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
    }
}
NGINX_EOF

    # 重载Nginx
    if [ -f /www/server/nginx/sbin/nginx ]; then
        /www/server/nginx/sbin/nginx -t && /www/server/nginx/sbin/nginx -s reload && echo "    Nginx配置已重载(宝塔)" || echo "    Nginx重载失败"
    elif command -v nginx &> /dev/null; then
        nginx -t && nginx -s reload && echo "    Nginx配置已重载" || echo "    Nginx重载失败"
    else
        echo "    警告: 未找到Nginx，请手动配置"
    fi
else
    echo "    警告: 未找到Nginx配置目录，请手动配置"
fi

# -----------------------------------------------------------
# 10. 设置自动备份
# -----------------------------------------------------------
echo ">>> 设置自动备份..."
(crontab -l 2>/dev/null | grep -v "smart-schedule.*auto_backup"; echo "0 2 * * * cd $APP_DIR/backend && /usr/bin/python3.10 -c \"from app.services.backup_service import auto_backup; auto_backup()\" >> $APP_DIR/logs/backup.log 2>&1") | crontab -
echo "    自动备份已设置（每天凌晨2点）"

# -----------------------------------------------------------
# 11. 配置防火墙
# -----------------------------------------------------------
echo ">>> 配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
    echo "    防火墙已放行HTTP"
elif command -v ufw &> /dev/null; then
    ufw allow 80/tcp 2>/dev/null || true
    echo "    防火墙已放行HTTP"
fi

# -----------------------------------------------------------
# 完成
# -----------------------------------------------------------
echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "  访问地址: http://你的服务器IP"
echo "  管理员账号: admin"
echo "  管理员密码: admin123"
echo "  数据库名:   $MYSQL_DB"
echo "  数据库用户: $MYSQL_USER"
echo "  数据库密码: $MYSQL_PASS"
echo "  配置文件:   $APP_DIR/backend/.env"
echo "  日志目录:   $APP_DIR/logs"
echo "  备份目录:   $APP_DIR/backups"
echo ""
echo "  常用命令:"
echo "    查看服务状态: systemctl status smart-schedule"
echo "    重启服务:     systemctl restart smart-schedule"
echo "    查看日志:     journalctl -u smart-schedule -f"
echo ""
echo "  ⚠️  重要：请及时修改管理员密码！"
echo "========================================="

# 保存部署信息
cat > $APP_DIR/deploy_info.txt << EOF
部署时间: $(date '+%Y-%m-%d %H:%M:%S')
数据库: $MYSQL_DB
数据库用户: $MYSQL_USER
数据库密码: $MYSQL_PASS
应用目录: $APP_DIR
后端端口: $BACKEND_PORT
EOF
chmod 600 $APP_DIR/deploy_info.txt
