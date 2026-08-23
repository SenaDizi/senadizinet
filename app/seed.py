import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app.config import settings
from app.models.user import User, UserRole
from app.models.subscription import SubscriptionPlan, Subscription
from app.models.content import Category, Actor, Series, Season, Episode
from app.models.system import SiteSetting
from app.security import get_password_hash

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Admin Kullanıcısı
        admin = db.query(User).filter(User.email == settings.DEFAULT_ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                username="admin",
                email=settings.DEFAULT_ADMIN_EMAIL,
                full_name=settings.DEFAULT_ADMIN_NAME,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"[OK] Admin hesabı oluşturuldu: {settings.DEFAULT_ADMIN_EMAIL}")

        # 2. Demo Kullanıcı
        demo_user = db.query(User).filter(User.email == "kullanici@senadizinet.com").first()
        if not demo_user:
            demo_user = User(
                username="demo_izleyici",
                email="kullanici@senadizinet.com",
                full_name="Ahmet Yılmaz",
                hashed_password=get_password_hash("Demo1234!"),
                role=UserRole.USER,
                is_active=True
            )
            db.add(demo_user)
            db.commit()
            print("[OK] Demo izleyici kullanıcısı oluşturuldu.")

        # 3. Abonelik Planları
        if db.query(SubscriptionPlan).count() == 0:
            free_plan = SubscriptionPlan(
                name="Haftalık Plan",
                slug="haftalık",
                price=150,
                billing_period="weekly",
                description="Standart HD kalitede temel dizi ve ilk bölümlere ücretsiz erişim.",
                features_json=json.dumps([
                    "Tüm ücretsiz bölümlere erişim",
                    "720p HD Video Kalitesi",
                    "Favori listesi oluşturma",
                    "İzleme geçmişi ve kaldığın yerden devam etme"
                ], ensure_ascii=False),
                is_popular=False
            )
            prem_plan = SubscriptionPlan(
                name="Premium Aylık",
                slug="premium-aylik",
                price=250,
                billing_period="monthly",
                description="Tüm lisanslı dizilere, tüm sezonlara sınırsız ve kesintisiz 4K Ultra HD erişim.",
                features_json=json.dumps([
                    "Tüm dizilere ve kilitli bölümlere tam erişim",
                    "1080p Full HD & 4K Ultra HD Kalite",
                    "Aynı anda 4 cihazdan izleme",
                    "Öncelikli yeni bölüm erişimi",
                    "Reklamsız sinematik deneyim"
                ], ensure_ascii=False),
                is_popular=True
            )
            vip_plan = SubscriptionPlan(
                name="VIP Sinema Yıllık",
                slug="vip-yillik",
                price=1799,
                billing_period="yearly",
                description="Yıllık avantajlı paketle tüm platform ayrıcalıkları ve özel etkinlik yayınları.",
                features_json=json.dumps([
                    "Tüm Premium özellikleri dahil",
                    "2 Ay bedava izleme avantajı",
                    "Özel kamera arkası ve röportajlar",
                    "7/24 VIP Destek hattı"
                ], ensure_ascii=False),
                is_popular=False
            )
            db.add_all([free_plan, prem_plan, vip_plan])
            db.commit()
            print("[OK] Abonelik planları eklendi.")

        # 4. Kategoriler
        categories_data = [
            ("Drama", "drama", "Derin insan hikayeleri, duygusal ve sürükleyici yapımlar.", "fa-masks-theater"),
            ("Aksiyon", "aksiyon", "Nefes kesen maceralar, dövüş ve dinamik sahneler.", "fa-fire"),
            ("Bilim Kurgu", "bilim-kurgu", "Gelecek, uzay, yapay zeka ve alternatif evrenler.", "fa-robot"),
            ("Romantik", "romantik", "Aşk, tutku ve unutulmaz duygusal bağlar.", "fa-heart"),
            ("Komedi", "komedi", "Eğlenceli ve keyif dolu anlar sunan diziler.", "fa-face-laugh-beam"),
            ("Gerilim", "gerilim", "Gizemli olaylar, suç dosyaları ve yüksek tempo.", "fa-skull"),
            ("Fantastik", "fantastik", "Büyülü dünyalar, mitoloji ve epik kahramanlar.", "fa-wand-magic-sparkles"),
            ("Belgesel", "belgesel", "Gerçek olaylar, doğa, bilim ve tarih incelemeleri.", "fa-earth-americas")
        ]
        
        cat_map = {}
        for name, slug, desc, icon in categories_data:
            cat = db.query(Category).filter(Category.slug == slug).first()
            if not cat:
                cat = Category(name=name, slug=slug, description=desc, icon=icon)
                db.add(cat)
                db.flush()
            cat_map[slug] = cat
        db.commit()
        print("[OK] Kategoriler hazırlandı.")

        # 5. Oyuncular
        actors_data = [
            ("Caner Özkan", "caner-ozkan", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300"),
            ("Elif Sönmez", "elif-sonmez", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300"),
            ("Burak Demir", "burak-demir", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300"),
            ("Zeynep Kaya", "zeynep-kaya", "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=300"),
            ("Murat Yıldız", "murat-yildiz", "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=300")
        ]
        actor_map = {}
        for name, slug, photo in actors_data:
            act = db.query(Actor).filter(Actor.slug == slug).first()
            if not act:
                act = Actor(name=name, slug=slug, photo_url=photo)
                db.add(act)
                db.flush()
            actor_map[slug] = act
        db.commit()

        # 6. Açık Kaynak / Lisanslı Örnek Dizi İçerikleri
        sample_videos = [
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4"
        ]

        series_data = [
            {
                "title": "Siber Şafak: 2088",
                "slug": "siber-safak-2088",
                "description": "Geleceğin mega-kentinde yapay zeka sistemlerinin kontrolü ele geçirdiği bir çağda, insanlığın son özgürlük direnişini yöneten gizli bir hacker grubunun nefes kesen mücadelesi.",
                "poster_url": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600&q=80",
                "banner_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1920&q=80",
                "release_year": 2026,
                "director": "Kaan Arslan",
                "country": "Türkiye",
                "rating": 9.3,
                "is_featured": True,
                "is_popular": True,
                "is_premium_only": False,
                "categories": ["bilim-kurgu", "aksiyon", "gerilim"],
                "actors": ["caner-ozkan", "elif-sonmez", "burak-demir"],
                "episodes_count": 6
            },
            {
                "title": "Kayıp Krallık Masalları",
                "slug": "kayip-krallik-masallari",
                "description": "Kadim çağlardan kalma büyülü bir mührün kırılmasıyla ortaya çıkan karanlık güçlere karşı, yedi krallığın kaderini belirleyecek efsanevi yolculuk.",
                "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&q=80",
                "banner_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1920&q=80",
                "release_year": 2025,
                "director": "Deniz Karahan",
                "country": "Türkiye",
                "rating": 9.1,
                "is_featured": True,
                "is_popular": True,
                "is_premium_only": False,
                "categories": ["fantastik", "drama", "aksiyon"],
                "actors": ["zeynep-kaya", "murat-yildiz", "elif-sonmez"],
                "episodes_count": 5
            },
            {
                "title": "Gölgedeki Dedektif",
                "slug": "golgedeki-dedektif",
                "description": "İstanbul'un sisli sokaklarında işlenen çözülememiş gizemli cinayetleri soruşturan emektar bir başkomiser ve genç adli bilişim uzmanının gerilim dolu ortaklığı.",
                "poster_url": "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=600&q=80",
                "banner_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1920&q=80",
                "release_year": 2026,
                "director": "Okan Çetin",
                "country": "Türkiye",
                "rating": 8.9,
                "is_featured": True,
                "is_popular": True,
                "is_premium_only": False,
                "categories": ["gerilim", "drama"],
                "actors": ["burak-demir", "zeynep-kaya"],
                "episodes_count": 4
            },
            {
                "title": "Boğazda Sonbahar",
                "slug": "bogazda-sonbahar",
                "description": "Farklı dünyalardan gelen iki tutkulu mimarın İstanbul Boğazı'nın eşsiz manzarasında kesişen yolları, fedakarlık ve sevgi üzerine dokunaklı bir romantik hikaye.",
                "poster_url": "https://images.unsplash.com/photo-1516589178581-6cd7833ae3b2?w=600&q=80",
                "banner_url": "https://images.unsplash.com/photo-1527838832700-5059252407fa?w=1920&q=80",
                "release_year": 2025,
                "director": "Selin Vural",
                "country": "Türkiye",
                "rating": 8.7,
                "is_featured": False,
                "is_popular": True,
                "is_premium_only": False,
                "categories": ["romantik", "drama"],
                "actors": ["caner-ozkan", "elif-sonmez"],
                "episodes_count": 4
            },
            {
                "title": "Yıldızlararası Yolculuk: Titan",
                "slug": "yildizlararasi-yolculuk-titan",
                "description": "Satürn'ün en büyük uydusu Titan'da kurulan ilk insan kolonisiyle Dünya arasındaki iletişimin aniden kesilmesi sonucu başlayan derin uzay kurtarma operasyonu.",
                "poster_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&q=80",
                "banner_url": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=1920&q=80",
                "release_year": 2026,
                "director": "Mert Aksoy",
                "country": "Türkiye",
                "rating": 9.4,
                "is_featured": True,
                "is_popular": True,
                "is_premium_only": True,
                "categories": ["bilim-kurgu", "gerilim"],
                "actors": ["murat-yildiz", "burak-demir"],
                "episodes_count": 6
            },
            {
                "title": "Mahallenin Neşesi",
                "slug": "mahallenin-nesesi",
                "description": "Tarihi bir mahallede fırıncılık yapan samimi bir ailenin ve komşularının başından geçen kahkaha dolu maceralar ve sıcacık dostluklar.",
                "poster_url": "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=600&q=80",
                "banner_url": "https://images.unsplash.com/photo-1514306191717-452ec28c7814?w=1920&q=80",
                "release_year": 2025,
                "director": "Emre Güneş",
                "country": "Türkiye",
                "rating": 8.6,
                "is_featured": False,
                "is_popular": True,
                "is_premium_only": False,
                "categories": ["komedi", "drama"],
                "actors": ["zeynep-kaya", "caner-ozkan"],
                "episodes_count": 4
            }
        ]

        for s_idx, item in enumerate(series_data):
            existing_series = db.query(Series).filter(Series.slug == item["slug"]).first()
            if not existing_series:
                new_s = Series(
                    title=item["title"],
                    slug=item["slug"],
                    description=item["description"],
                    poster_url=item["poster_url"],
                    banner_url=item["banner_url"],
                    release_year=item["release_year"],
                    director=item["director"],
                    country=item["country"],
                    rating=item["rating"],
                    is_featured=item["is_featured"],
                    is_popular=item["is_popular"],
                    is_premium_only=item["is_premium_only"],
                    view_count=1250 * (s_idx + 1)
                )

                # Kategorileri ekle
                for c_slug in item["categories"]:
                    if c_slug in cat_map:
                        new_s.categories.append(cat_map[c_slug])

                # Oyuncuları ekle
                for a_slug in item["actors"]:
                    if a_slug in actor_map:
                        new_s.actors.append(actor_map[a_slug])

                db.add(new_s)
                db.flush()

                # Sezon 1 ve Bölümleri oluştur
                season1 = Season(series_id=new_s.id, season_number=1, title="1. Sezon", description=f"{new_s.title} ilk sezon")
                db.add(season1)
                db.flush()

                for ep_i in range(1, item["episodes_count"] + 1):
                    v_url = sample_videos[(ep_i - 1 + s_idx) % len(sample_videos)]
                    ep = Episode(
                        season_id=season1.id,
                        episode_number=ep_i,
                        title=f"{ep_i}. Bölüm: {new_s.title} Başlangıç" if ep_i == 1 else f"{ep_i}. Bölüm: Düğüm Çözülüyor",
                        description=f"{new_s.title} dizisinin 1. sezon {ep_i}. bölümünde tansiyon yükseliyor.",
                        thumbnail_url=item["poster_url"],
                        video_url=v_url,
                        duration_minutes=42 + ep_i,
                        is_free=(ep_i <= 2), # İlk 2 bölüm ücretsiz, devamı premium
                        view_count=500 * ep_i
                    )
                    db.add(ep)

                db.commit()
                print(f"[OK] Dizi eklendi: {new_s.title} ({item['episodes_count']} bölüm)")

        # 7. Site Ayarları
        default_settings = [
            ("site_name", "SenaDizi"),
            ("logo_text", "SenaDizi"),
            ("site_description", "Yüksek Kaliteli Lisanslı Dizi ve Video Platformu"),
            ("primary_color", "#E50914"),
            ("contact_email", "destek@senadizinet.com"),
            ("social_twitter", "https://twitter.com"),
            ("social_instagram", "https://instagram.com"),
            ("social_youtube", "https://youtube.com")
        ]
        for key, val in default_settings:
            s = db.query(SiteSetting).filter(SiteSetting.key == key).first()
            if not s:
                db.add(SiteSetting(key=key, value=val))
        db.commit()
        print("[OK] Site ayarları yüklendi.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
