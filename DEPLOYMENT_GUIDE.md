# 🌐 SenaDizi – İnternette Yayınlama & Canlıya Alma Rehberi

Bu rehber, **SenaDizi** platformunu yerel bilgisayarınızdan çıkarıp, tüm dünyanın 7/24 kesintisiz erişebileceği şekilde bir sunucuda yayınlamanızı ve **özel alan adınızı (Domain - Örn: `senadizinet.com`)** bağlamanızı adım adım anlatır.

---

## 📋 İÇİNDEKİLER
1. [Hangi Barındırma (Hosting/Sunucu) Hizmetini Seçmelisiniz?](#1-barındırma-hizmeti-seçimi)
2. [Adım 1: Alan Adı (Domain) Satın Alma & DNS Ayarları](#2-alan-adı-ve-dns-ayarları)
3. [Adım 2: Sunucu (VPS) Satın Alma ve Hazırlama](#3-sunucu-hazırlama)
4. [Adım 3: Projeyi Sunucuya Yükleme](#4-projeyi-sunucuya-yükleme)
5. [Adım 4: SSL (HTTPS) Sertifikası Kurma (Ücretsiz)](#5-ssl-https-sertifikası)
6. [Adım 5: Alternatif Kolay Platformlar (Render / Railway)](#6-alternatif-kolay-platformlar)

---

## 1. Barındırma Hizmeti Seçimi

Video ve dizi akış platformları için en verimli ve ekonomik barındırma seçenekleri:

| Sağlayıcı | Tip | Aylık Maliyet | Tavsiye Edilen Kullanım |
|---|---|---|---|
| **Hetzner Cloud** (CPX11/CPX21) | VPS (Ubuntu) | ~4€ - 8€ | 🥇 **En Çok Tavsiye Edilen** (Yüksek hız, düşük maliyet, tam kontrol) |
| **DigitalOcean / Linode** | VPS (Droplet) | ~$6 - $12 | Kolay arayüz, güvenilir global ağ |
| **Render.com / Railway.app** | PaaS (Bulut) | ~$7 - $15 | Sunucu yönetimiyle uğraşmak istemeyenler için tek tıkla yayınlama |
| **Cloudflare** | DNS / CDN / WAF | **Ücretsiz** | Hızlandırma, DDoS koruması ve ücretsiz SSL |

> **Önemli İpucu (Video Depolama):** Videolar sunucu diskini doldurmasın diye harici depolama/CDN (**Cloudflare Stream, Bunny.net CDN, AWS S3 veya Vimeo**) kullanılması önerilir. Admin panelinden video linkini doğrudan bu CDN'lerden girebilirsiniz.

---

## 2. Alan Adı ve DNS Ayarları

1. **Domain Satın Alın:**
   - [Namecheap](https://www.namecheap.com), [GoDaddy](https://www.godaddy.com) veya [Turhost](https://www.turhost.com) gibi bir firmadan alan adınızı (Örn: `senadizinet.com`) alın.
2. **Cloudflare Entegrasyonu (Şiddetle Tavsiye Edilir - Ücretsiz):**
   - [Cloudflare.com](https://www.cloudflare.com)'a ücretsiz üye olun ve sitenizi ekleyin.
   - Alan adı firmanızın panelinden DNS sunucularını (Nameservers) Cloudflare'in verdikleriyle değiştirin.
3. **DNS Kayıtlarını Ekleyin:**
   - Cloudflare DNS paneline gidin ve sunucunuzun IP adresini (`123.45.67.89`) bağlayın:
     - **Tip:** `A` | **İsim:** `@` | **İçerik:** `SUNUCU_IP_ADRESINIZ` | **Proxy:** Aktif (Turuncu Bulut)
     - **Tip:** `CNAME` | **İsim:** `www` | **İçerik:** `senadizinet.com` | **Proxy:** Aktif (Turuncu Bulut)

---

## 3. Sunucu (VPS) Hazırlama

Hetzner veya DigitalOcean'dan bir **Ubuntu 24.04 / 22.04 LTS** sunucu oluşturduktan sonra:

1. **SSH ile Sunucuya Bağlanın:**
   ```bash
   ssh root@SUNUCU_IP_ADRESINIZ
   ```
2. **Sistemi Güncelleyin & Gerekli Araçları Yükleyin:**
   ```bash
   apt update && apt upgrade -y
   apt install -y git curl ufw
   ```
3. **Güvenlik Duvarını (UFW) Yapılandırın:**
   ```bash
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

---

## 4. Projeyi Sunucuya Yükleme & Docker ile Başlatma

1. **Projeyi Sunucuya Kopyalayın:**
   - Git kullanarak veya bilgisayarınızdan SCP ile:
   ```bash
   git clone <SENIN_GITHUB_REPOM> /var/www/senadizinet
   cd /var/www/senadizinet
   ```
2. **.env Dosyasını Düzenleyin:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   - `DOMAIN=senadizinet.com`
   - `BASE_URL=https://senadizinet.com`
   - `DEFAULT_ADMIN_PASSWORD=GucluBirAdminSifresi2026!`
   - `SECRET_KEY=CokGizliRastgeleMetinBuraya`
3. **Otomatik Dağıtım Betiğini Çalıştırın:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
Bu komut PostgreSQL veritabanını, Gunicorn çoklu iş parçacıklı FastAPI motorunu ve Nginx sunucusunu otomatik olarak kurup ayağa kaldıracaktır.

---

## 5. SSL (HTTPS) Kurulumu

Eğer **Cloudflare** kullanıyorsanız:
- Cloudflare Panelinde **SSL/TLS** menüsüne gidin -> Modu **Full (Strict)** veya **Flexible** yapın. Anında yeşil kilit (HTTPS) aktif olur!

Eğer doğrudan **Let's Encrypt Certbot** kullanmak isterseniz:
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d senadizinet.com -d www.senadizinet.com
```

---

## 6. Alternatif: Render.com ile Tek Tıkla Dağıtım (VPS İstemeyenler İçin)

Eğer sunucu komutlarıyla uğraşmak istemiyorsanız:
1. Kodlarınızı GitHub'a yükleyin.
2. [Render.com](https://render.com)'a girip **New Web Service** seçin.
3. GitHub deponuzu bağlayın.
4. **Environment:** `Docker` seçin.
5. **Settings -> Custom Domains** kısmından `senadizinet.com` alan adınızı ekleyin.
6. Render size otomatik ücretsiz SSL ve 7/24 barındırma sağlayacaktır!
