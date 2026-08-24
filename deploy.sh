#!/bin/bash
# SenaDizi – Production Otomatik Kurulum ve Dağıtım Betiği

set -e

echo "=================================================="
echo "🎬 SenaDizi Production Dağıtımı Başlatılıyor..."
echo "=================================================="

# 1. Docker & Docker Compose Kontrolü
if ! [ -x "$(command -v docker)" ]; then
  echo "📦 Docker kuruluyor..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  rm get-docker.sh
fi

# 2. .env Dosyası Kontrolü
if [ ! -f .env ]; then
  echo "⚙️  .env dosyası oluşturuluyor..."
  cp .env.example .env
  # Rastgele gizli anahtar üret
  SECRET=$(openssl rand -hex 32)
  sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET/" .env
fi

# 3. Docker Konteynerlerini Derle ve Başlat
echo "🚀 Servisler başlatılıyor..."
docker compose down || true
docker compose up -d --build

echo "=================================================="
echo "✅ SenaDizi başarıyla yayına alındı!"
echo "🌐 Tarayıcınızdan alan adınızı ziyaret edebilirsiniz."
echo "=================================================="
