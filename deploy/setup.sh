#!/bin/bash
# ============================================================
# GCP Compute Engine 최초 1회 서버 세팅 스크립트
# Ubuntu 22.04 LTS 기준
# 사용법: bash setup.sh
# ============================================================
set -e

echo "=== [1/5] 시스템 패키지 업데이트 ==="
sudo apt-get update && sudo apt-get upgrade -y

echo "=== [2/5] Docker 설치 ==="
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# sudo 없이 docker 사용
sudo usermod -aG docker $USER

echo "=== [3/5] Git 설치 ==="
sudo apt-get install -y git

echo "=== [4/5] 레포 클론 ==="
REPO_DIR="/opt/workflow-map"
if [ -d "$REPO_DIR" ]; then
  echo "  이미 존재 — git pull로 업데이트"
  cd "$REPO_DIR" && git pull origin master
else
  sudo git clone https://github.com/joycityDSBI/workflow-map.git "$REPO_DIR"
  sudo chown -R $USER:$USER "$REPO_DIR"
fi

echo "=== [5/5] .env 파일 생성 안내 ==="
ENV_FILE="$REPO_DIR/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
  cp "$REPO_DIR/backend/.env.example" "$ENV_FILE"
  SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  sed -i "s/change-me-generate-with-openssl-rand-hex-32/$SECRET_KEY/" "$ENV_FILE"
  echo ""
  echo "  ✅ .env 파일 생성됨: $ENV_FILE"
  echo "  ⚠️  다음 값을 직접 채워주세요:"
  echo "     ANTHROPIC_API_KEY=sk-ant-..."
  echo "     NOTION_TOKEN=secret_..."
  echo ""
  echo "  수정: nano $ENV_FILE"
else
  echo "  .env 이미 존재 — 건너뜀"
fi

echo ""
echo "=============================="
echo "  설치 완료!"
echo "  다음 명령으로 서버 실행:"
echo "  cd $REPO_DIR && docker compose up -d --build"
echo "=============================="
echo ""
echo "  ⚠️  docker 그룹 반영을 위해 다시 로그인하거나:"
echo "  newgrp docker"
