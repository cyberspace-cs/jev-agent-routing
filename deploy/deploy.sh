#!/bin/bash
# ============================================================
# Jev Agent Routing - 一键部署脚本
# 用法：在服务器上执行
#   chmod +x deploy.sh
#   ./deploy.sh
# ============================================================

set -e

REPO_URL="https://github.com/cyberspace-cs/jev-agent-routing.git"
INSTALL_DIR="/root/jev-agent-routing"
PORT=8000

echo "=========================================="
echo "  Jev Agent Routing 一键部署"
echo "=========================================="
echo ""

# 1. 检查依赖
echo "📦 1/6 检查依赖..."
if ! command -v git &> /dev/null; then
    echo "   安装 git..."
    apt-get update && apt-get install -y git
fi

if ! command -v python3 &> /dev/null; then
    echo "   安装 python3..."
    apt-get update && apt-get install -y python3 python3-pip python3-venv
fi

if ! command -v nginx &> /dev/null; then
    echo "   安装 nginx..."
    apt-get update && apt-get install -y nginx
fi

echo "   ✅ 依赖就绪"
echo ""

# 2. 拉取代码
echo "📥 2/6 拉取代码..."
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
echo "   ✅ 代码就绪"
echo ""

# 3. 安装 Python 依赖
echo "🐍 3/6 安装 Python 依赖..."
cd "$INSTALL_DIR"
pip3 install -r requirements.txt
echo "   ✅ Python 依赖就绪"
echo ""

# 4. 配置 JEV_API_KEY
echo "🔑 4/6 配置环境变量..."
read -p "   请输入 JEV_API_KEY（直接回车跳过，用 mock 模式）：" JEV_KEY
if [ -n "$JEV_KEY" ]; then
    echo "export JEV_API_KEY=$JEV_KEY" > /etc/profile.d/jev.sh
    export JEV_API_KEY=$JEV_KEY
    echo "   ✅ JEV_API_KEY 已配置"
else
    echo "   ⚠️ 未配置 API Key，将使用 mock 模式"
fi
echo ""

# 5. 配置 systemd 服务
echo "⚙️ 5/6 配置 systemd 服务..."
cat > /etc/systemd/system/jev-web.service << EOF
[Unit]
Description=Jev Agent Routing Web Demo
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/webapp
Environment="JEV_API_KEY=${JEV_API_KEY:-}"
ExecStart=$(which python3) -m uvicorn server:app --host 0.0.0.0 --port $PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable jev-web
systemctl restart jev-web
echo "   ✅ 服务已启动"
echo ""

# 6. 配置 Nginx 反向代理
echo "🌐 6/6 配置 Nginx 反向代理..."
read -p "   请输入域名（直接回车用 IP）：" DOMAIN
if [ -z "$DOMAIN" ]; then
    DOMAIN="_"
fi

cat > /etc/nginx/conf.d/jev.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

nginx -t && systemctl reload nginx
echo "   ✅ Nginx 配置完成"
echo ""

# 完成
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  http://43.143.231.106"
echo "  http://taoxie.vip"
echo ""
echo "常用命令："
echo "  查看状态：systemctl status jev-web"
echo "  查看日志：journalctl -u jev-web -f"
echo "  重启服务：systemctl restart jev-web"
echo "=========================================="
