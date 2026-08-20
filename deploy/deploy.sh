#!/bin/bash
# ============================================================
# 배포 스크립트 — 코드 업데이트 후 재시작
# 사용법: bash deploy.sh
# ============================================================
set -e

REPO_DIR="/opt/workflow-map"

echo "=== [1/3] 최신 코드 Pull ==="
cd "$REPO_DIR"
git pull origin master

echo "=== [2/3] 이미지 빌드 + 마이그레이션 + 재시작 ==="
docker compose up -d --build

echo "=== [3/3] 상태 확인 ==="
docker compose ps
echo ""
echo "로그 확인: docker compose logs -f backend"
echo "API 주소:  http://$(curl -s ifconfig.me):8000/docs"
