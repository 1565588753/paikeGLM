#!/bin/bash
# ============================================================
# 智能排课系统 - 更新部署脚本
# 使用方法: bash update.sh [版本号]
# 示例:     bash update.sh v1.2.0
# ============================================================

set -e

# -----------------------------------------------------------
# 配置项
# -----------------------------------------------------------
APP_DIR="/www/wwwroot/smart-schedule"
BACKUP_DIR="$APP_DIR/backups"
LOG_FILE="$APP_DIR/logs/update.log"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
VERSION="${1:-latest}"

# -----------------------------------------------------------
# 工具函数
# -----------------------------------------------------------
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_service() {
    if systemctl is-active --quiet smart-schedule; then
        return 0
    else
        return 1
    fi
}

# -----------------------------------------------------------
# 前置检查
# -----------------------------------------------------------
log "========================================="
log "  智能排课系统 - 开始更新 (版本: $VERSION)"
log "========================================="

if [ "$EUID" -ne 0 ]; then
    log "错误: 请使用root用户运行此脚本"
    exit 1
fi

if [ ! -d "$APP_DIR" ]; then
    log "错误: 应用目录不存在: $APP_DIR"
    log "请先运行 install.sh 进行初始部署"
    exit 1
fi

# 检查当前服务状态
if check_service; then
    log "当前服务状态: 运行中"
else
    log "警告: 当前服务未运行"
fi

# -----------------------------------------------------------
# 1. 备份当前版本
# -----------------------------------------------------------
log ">>> 步骤1: 备份当前版本..."

BACKUP_NAME="smart-schedule_backup_${TIMESTAMP}"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

mkdir -p "$BACKUP_PATH"

# 备份后端代码
if [ -d "$APP_DIR/backend" ]; then
    cp -r "$APP_DIR/backend" "$BACKUP_PATH/backend"
    log "    后端代码已备份"
fi

# 备份前端代码
if [ -d "$APP_DIR/frontend" ]; then
    cp -r "$APP_DIR/frontend" "$BACKUP_PATH/frontend"
    log "    前端代码已备份"
fi

# 备份配置文件
if [ -f "$APP_DIR/backend/.env" ]; then
    cp "$APP_DIR/backend/.env" "$BACKUP_PATH/.env.backup"
    log "    配置文件已备份"
fi

# 备份数据库
if command -v mysqldump &> /dev/null; then
    DB_NAME=$(grep "DATABASE_URL" "$APP_DIR/backend/.env" 2>/dev/null | sed 's/.*:\/\/[^:]*:[^@]*@[^\/]*\/\([^?]*\).*/\1/' || echo "smart_schedule")
    mysqldump -u root "$DB_NAME" > "$BACKUP_PATH/database_backup.sql" 2>/dev/null && log "    数据库已备份" || log "    警告: 数据库备份失败"
else
    log "    警告: 未找到mysqldump，跳过数据库备份"
fi

# 记录备份信息
cat > "$BACKUP_PATH/backup_info.txt" << EOF
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份版本: $VERSION
备份原因: 系统更新
应用目录: $APP_DIR
EOF

log "    备份完成: $BACKUP_PATH"

# 清理30天前的备份
find "$BACKUP_DIR" -maxdepth 1 -name "smart-schedule_backup_*" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
log "    已清理30天前的旧备份"

# -----------------------------------------------------------
# 2. 停止服务
# -----------------------------------------------------------
log ">>> 步骤2: 停止服务..."
if check_service; then
    systemctl stop smart-schedule
    sleep 2
    if check_service; then
        log "    警告: 服务未能正常停止，强制终止..."
        systemctl kill smart-schedule
        sleep 2
    fi
    log "    服务已停止"
else
    log "    服务未在运行，跳过停止步骤"
fi

# -----------------------------------------------------------
# 3. 更新代码
# -----------------------------------------------------------
log ">>> 步骤3: 更新代码..."

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 更新后端代码
if [ -d "$SCRIPT_DIR/backend" ]; then
    # 保留配置文件
    ENV_BACKUP="$APP_DIR/backend/.env"
    cp "$ENV_BACKUP" "/tmp/smart-schedule-env-backup" 2>/dev/null || true

    # 同步后端代码
    rsync -av --delete \
        --exclude='.env' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='*.pyc' \
        "$SCRIPT_DIR/backend/" "$APP_DIR/backend/" 2>/dev/null || {
        # rsync不可用时使用cp
        rm -rf "$APP_DIR/backend/app"
        rm -rf "$APP_DIR/backend/requirements.txt"
        cp -r "$SCRIPT_DIR/backend/app" "$APP_DIR/backend/" 2>/dev/null || true
        cp "$SCRIPT_DIR/backend/requirements.txt" "$APP_DIR/backend/" 2>/dev/null || true
    }

    # 恢复配置文件
    cp "/tmp/smart-schedule-env-backup" "$ENV_BACKUP" 2>/dev/null || true
    rm -f "/tmp/smart-schedule-env-backup"

    log "    后端代码已更新"
else
    log "    警告: 未找到新版本后端代码，跳过更新"
fi

# 更新前端代码
if [ -d "$SCRIPT_DIR/frontend/dist" ]; then
    rm -rf "$APP_DIR/frontend/dist"
    cp -r "$SCRIPT_DIR/frontend/dist" "$APP_DIR/frontend/"
    log "    前端代码已更新"
else
    log "    警告: 未找到新版本前端代码，跳过更新"
fi

# -----------------------------------------------------------
# 4. 更新依赖
# -----------------------------------------------------------
log ">>> 步骤4: 更新Python依赖..."
if [ -f "$APP_DIR/backend/requirements.txt" ]; then
    pip3.10 install -r "$APP_DIR/backend/requirements.txt" -q 2>/dev/null && log "    依赖更新完成" || log "    警告: 部分依赖更新失败"
else
    log "    跳过依赖更新（未找到requirements.txt）"
fi

# -----------------------------------------------------------
# 5. 数据库迁移
# -----------------------------------------------------------
log ">>> 步骤5: 检查数据库迁移..."
SQL_DIR="$SCRIPT_DIR/sql"

if [ -f "$SQL_DIR/migration.sql" ]; then
    log "    发现数据库迁移脚本，执行迁移..."
    DB_NAME=$(grep "DATABASE_URL" "$APP_DIR/backend/.env" 2>/dev/null | sed 's/.*:\/\/[^:]*:[^@]*@[^\/]*\/\([^?]*\).*/\1/' || echo "smart_schedule")
    mysql -u root "$DB_NAME" < "$SQL_DIR/migration.sql" 2>/dev/null && log "    数据库迁移完成" || log "    警告: 数据库迁移失败，请手动执行"
else
    log "    无数据库迁移脚本，跳过"
fi

# -----------------------------------------------------------
# 6. 启动服务
# -----------------------------------------------------------
log ">>> 步骤6: 启动服务..."
systemctl start smart-schedule
sleep 3

if check_service; then
    log "    服务启动成功"
else
    log "    错误: 服务启动失败！"
    log "    正在回滚..."

    # 回滚代码
    if [ -d "$BACKUP_PATH/backend" ]; then
        rm -rf "$APP_DIR/backend/app"
        cp -r "$BACKUP_PATH/backend/app" "$APP_DIR/backend/" 2>/dev/null || true
        log "    后端代码已回滚"
    fi
    if [ -d "$BACKUP_PATH/frontend" ]; then
        rm -rf "$APP_DIR/frontend/dist"
        cp -r "$BACKUP_PATH/frontend/dist" "$APP_DIR/frontend/" 2>/dev/null || true
        log "    前端代码已回滚"
    fi
    if [ -f "$BACKUP_PATH/.env.backup" ]; then
        cp "$BACKUP_PATH/.env.backup" "$APP_DIR/backend/.env"
        log "    配置文件已回滚"
    fi

    # 回滚数据库
    if [ -f "$BACKUP_PATH/database_backup.sql" ]; then
        DB_NAME=$(grep "DATABASE_URL" "$APP_DIR/backend/.env" 2>/dev/null | sed 's/.*:\/\/[^:]*:[^@]*@[^\/]*\/\([^?]*\).*/\1/' || echo "smart_schedule")
        mysql -u root "$DB_NAME" < "$BACKUP_PATH/database_backup.sql" 2>/dev/null && log "    数据库已回滚" || log "    警告: 数据库回滚失败"
    fi

    # 尝试重启
    systemctl start smart-schedule
    sleep 3
    if check_service; then
        log "    回滚后服务启动成功"
    else
        log "    错误: 回滚后服务仍无法启动，请手动检查"
    fi
    exit 1
fi

# -----------------------------------------------------------
# 7. 验证更新
# -----------------------------------------------------------
log ">>> 步骤7: 验证更新..."

# 检查API是否响应
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health 2>/dev/null || echo "000")

if [ "$HEALTH_CHECK" = "200" ]; then
    log "    API健康检查通过 (HTTP $HEALTH_CHECK)"
elif [ "$HEALTH_CHECK" = "000" ]; then
    log "    警告: 无法连接API服务"
else
    log "    警告: API返回异常状态码: HTTP $HEALTH_CHECK"
fi

# 检查前端是否可访问
FRONTEND_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ 2>/dev/null || echo "000")

if [ "$FRONTEND_CHECK" = "200" ]; then
    log "    前端页面可访问 (HTTP $FRONTEND_CHECK)"
else
    log "    警告: 前端页面不可访问 (HTTP $FRONTEND_CHECK)"
fi

# 检查数据库连接
DB_CHECK=$(mysql -u root -e "SELECT 1 FROM users LIMIT 1;" 2>/dev/null && echo "OK" || echo "FAIL")
if [ "$DB_CHECK" = "OK" ]; then
    log "    数据库连接正常"
else
    log "    警告: 数据库连接异常"
fi

# -----------------------------------------------------------
# 完成
# -----------------------------------------------------------
log "========================================="
log "  更新完成！"
log "========================================="
log ""
log "  更新版本: $VERSION"
log "  更新时间: $(date '+%Y-%m-%d %H:%M:%S')"
log "  备份位置: $BACKUP_PATH"
log ""
log "  如遇问题，可使用以下命令回滚:"
log "    bash $0 --rollback $BACKUP_PATH"
log ""
log "  查看服务状态: systemctl status smart-schedule"
log "  查看服务日志: journalctl -u smart-schedule -f"
log "========================================="
