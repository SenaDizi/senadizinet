# 🎬 SenaDizi – Profesyonel Dizi & Video Akış Platformu

SenaDizi, yayınlama hakkına sahip olunan veya lisanslı içerikler için geliştirilmiş, Netflix benzeri sinematik deneyim sunan modern ve profesyonel bir Full-Stack dizi/video akış platformudur.

---

## 🌟 Öne Çıkan Özellikler

- **Mobil Öncelikli & Sinematik Tasarım (Mobile-First UI)**:
  - Siyah + Kırmızı (#E50914) karanlık sinema teması.
  - Akıcı Hero slider, popüler dizi carouselleri, kategori bölümleri.
  - Telefonlar için özel alt navigasyon (Bottom Bar) ve dokunmatik kontroller.
- **Özel Gelişmiş Video Oynatıcı (Custom Video Player)**:
  - Oynat/Duraklat, ses, tam ekran, hız seçimi (0.5x, 1x, 1.25x, 1.5x, 2x).
  - 5 saniyede bir otomatik izleme süresini kaydetme ve **"Kaldığın Yerden Devam Et"** desteği.
  - Sonraki ve önceki bölüme tek tıkla geçiş, bölüm içi hızlı liste çekmecesi.
- **Kullanıcı & Üyelik Sistemi**:
  - Güvenli JWT & HttpOnly cookie tabanlı kimlik doğrulama, `bcrypt` parola şifreleme.
  - Favori listesi, izleme geçmişi ve video ilerleme takibi.
- **Abonelik & Webhook Altyapısı**:
  - Ücretsiz, Premium ve VIP paketleri.
  - Harici ödeme sistemleri (Stripe, Iyzico, PayTR) için webhook entegrasyonu.
  - Kilitli/VIP bölümlere abonelik kontrolü.
- **Kapsamlı Yönetim (Admin) Paneli (`/admin`)**:
  - Dashboard: Kullanıcı, dizi, bölüm sayıları, aktif abonelikler ve gelir analitiği.
  - Dizi CRUD: Yeni dizi ekleme, kapak, afiş, kategori ve oyuncu ilişkilendirme.
  - Sezon & Bölüm CRUD: Tek tek veya **Toplu Bölüm Oluşturucu (Bulk Episode Creator)** ile saniyeler içinde onlarca bölüm ekleme.
  - Kategori & Kullanıcı Yönetimi (Kullanıcı durumunu Aktif/Pasif yapma).
  - Site Ayarları (Başlık, logo metni, iletişim e-postası vb.).
- **SEO & Performans**:
  - Dinamik OpenGraph, Twitter Cards ve Canonical URL'ler.
  - Otomatik `/sitemap.xml` ve `/robots.txt`.
  - Özel 404, 403 ve 500 hata sayfaları.

---

## 🚀 Kurulum ve Çalıştırma

### 1. Gereksinimler
- Python 3.10 veya üzeri
- `pip` paket yöneticisi

### 2. Bağımlılıkları Yükleme
```bash
pip install -r requirements.txt
```

### 3. Uygulamayı Başlatma
```bash
python run.py
```
Sunucu başladığında terminalde yerel erişim adresi, **mobil ağ IP'si** ve telefon kamerasından okutabileceğiniz **QR Kod** görüntülenecektir.

---

## 🔑 Varsayılan Yönetici (Admin) Girişi

- **URL**: `http://localhost:8000/admin` veya `http://[YEREL-IP]:8000/admin`
- **E-Posta**: `admin@senadizinet.com`
- **Şifre**: `SenaDizi2026!`

> **ÖNEMLİ (Production Notu)**: Canlı ortama çıkmadan önce `.env` dosyasındaki `DEFAULT_ADMIN_PASSWORD` ve `SECRET_KEY` değerlerini güvenli şifrelerle güncelleyin.

---

## 📂 Proje Dizin Yapısı

```
SenaDizi/
├── app/
│   ├── config.py             # Konfigürasyon ve çevre değişkenleri
│   ├── database.py           # SQLAlchemy bağlantısı ve oturum yönetimi
│   ├── security.py           # JWT, şifre hashleme ve RBAC yetkilendirme
│   ├── seed.py               # Otomatik demo veri ve admin yükleyici
│   ├── main.py               # FastAPI uygulaması ve exception handler'lar
│   ├── models/               # Veritabanı modelleri (User, Series, Episode, Subscription vb.)
│   ├── schemas/              # Pydantic DTO veri doğrulama şemaları
│   └── routers/              # REST API & Web SSR View yönlendiricileri
├── static/
│   ├── css/custom.css        # Sinematik koyu tema ve efektler
│   ├── js/app.js             # Canlı arama, favori ve bildirim motoru
│   └── js/admin.js           # Admin paneli CRUD ve modal kontrolleri
├── templates/
│   ├── base.html             # Ortak düzen, mobil navigasyon ve footer
│   ├── index.html            # Hero slider, popüler ve kategorik diziler
│   ├── catalog.html          # Dizi kataloğu ve filtreleme
│   ├── detail.html           # Dizi detay ve sezon/bölüm listesi
│   ├── player.html           # Özel sinematik video oynatıcı
│   ├── admin/                # Yönetim paneli şablonları
│   └── errors/               # 404, 403, 500 hata sayfaları
├── .env                      # Ortam değişkenleri
├── requirements.txt          # Python bağımlılıkları
├── run.py                    # QR Kodlu sunucu başlatıcı
└── README.md
```

---

## 🌐 Production Dağıtımı (Deployment) & Video CDN

- **PostgreSQL**: `.env` içerisindeki `DATABASE_URL` değişkenine `postgresql://kullanici:sifre@host:5432/veritabani` yazarak PostgreSQL'e anında geçiş yapabilirsiniz.
- **Video Depolama & CDN**: Admin panelinden bölüm eklerken Cloudflare Stream, AWS CloudFront, BunnyCDN veya Vimeo Pro doğrudan video URL'lerini tanımlayabilirsiniz.
- **Ödeme Sağlayıcısı**: Stripe, Iyzico veya PayTR webhook'ları `/api/subscriptions/webhook` adresine bağlanabilir.
