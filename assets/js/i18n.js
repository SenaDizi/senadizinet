/**
 * SedaDizi - Dynamic Multi-Language (i18n) Engine
 * Supported Languages: TR (Türkçe), EN (English), DE (Deutsch), ES (Español), AR (العربية - RTL), RU (Русский)
 */

const SEDA_TRANSLATIONS = {
  tr: {
    lang_name: "Türkçe",
    dir: "ltr",
    nav_home: "Ana Sayfa",
    nav_series: "Diziler",
    nav_categories: "Kategoriler",
    nav_new: "Yeni Eklenenler",
    nav_popular: "Popüler",
    nav_premium: "Premium",
    nav_login: "Giriş Yap",
    nav_register: "Kayıt Ol",
    nav_logout: "Çıkış Yap",
    nav_profile: "Profilim",
    nav_favorites: "Favorilerim",
    nav_history: "İzleme Geçmişi",
    nav_search: "Ara",
    search_placeholder: "Dizi veya oyuncu ara...",
    search_results: "Arama Sonuçları",
    search_no_results: "Sonuç bulunamadı.",
    search_view_all: "Tüm Sonuçları Gör",
    hero_badge_featured: "ÖNE ÇIKAN",
    hero_badge_score: "Puan",
    hero_btn_watch: "Hemen İzle",
    hero_btn_details: "Detaylar",
    hero_btn_fav: "Favorilere Ekle",
    hero_btn_fav_remove: "Favorilerden Çıkar",
    section_popular: "Popüler Diziler",
    section_new: "Yeni Eklenen Diziler",
    section_episodes: "Yeni Bölümler",
    section_drama: "Drama Dizileri",
    section_action: "Aksiyon Dizileri",
    section_scifi: "Bilim Kurgu Dizileri",
    section_comedy: "Komedi Dizileri",
    section_romantic: "Romantik Dizileri",
    view_all: "Tümünü Gör",
    more: "Daha Fazla",
    season: "Sezon",
    episode: "Bölüm",
    duration_min: "dk",
    player_next_episode: "Sonraki Bölüme Geç",
    player_all_episodes: "Tüm Bölümler",
    player_resume_prompt: "Bu bölüme en son {time} dakikasında kalmıştınız. Kaldığınız yerden devam etmek ister misiniz?",
    player_speed: "Hız",
    player_quality: "Kalite",
    player_subtitle: "Altyazı",
    player_subtitle_off: "Kapalı",
    player_subtitle_tr: "Türkçe",
    player_subtitle_en: "İngilizce",
    sub_title: "Abonelik Paketleri",
    sub_desc: "Reklamsız, 4K Ultra HD ve sınırsız sinematik dizi deneyimi.",
    plan_free: "Ücretsiz",
    plan_standard: "Standart HD",
    plan_ultra: "Ultra 4K Sinema",
    plan_select: "Planı Seç",
    plan_active: "Mevcut Planınız",
    footer_desc: "Türkiye'nin modern, sinematik ve lisanslı içerik akış platformu. Yüksek görüntü kalitesi ve kesintisiz izleme deneyimi.",
    footer_quick_links: "Hızlı Bağlantılar",
    footer_legal: "Kurumsal & Yasal",
    footer_about: "Hakkımızda",
    footer_contact: "İletişim",
    footer_privacy: "Gizlilik Politikası",
    footer_terms: "Kullanım Şartları",
    footer_kvkk: "KVKK Aydınlatma",
    footer_copyright_notice: "Telif Hakkı Bildirimi",
    footer_rights: "© 2026 SedaDizi. Tüm hakları saklıdır. Platformda yalnızca lisanslı ve yetkili içerikler yayınlanmaktadır.",
    toast_token_saved: "Oturum belirteci (sena_token) başarıyla senkronize edildi.",
    toast_fav_added: "Favorilerinize eklendi.",
    toast_fav_removed: "Favorilerinizden kaldırıldı.",
    toast_login_success: "Giriş başarılı! Yönlendiriliyorsunuz..."
  },
  en: {
    lang_name: "English",
    dir: "ltr",
    nav_home: "Home",
    nav_series: "TV Shows",
    nav_categories: "Categories",
    nav_new: "New Releases",
    nav_popular: "Popular",
    nav_premium: "Premium",
    nav_login: "Sign In",
    nav_register: "Sign Up",
    nav_logout: "Sign Out",
    nav_profile: "My Profile",
    nav_favorites: "My Favorites",
    nav_history: "Watch History",
    nav_search: "Search",
    search_placeholder: "Search series or actors...",
    search_results: "Search Results",
    search_no_results: "No results found.",
    search_view_all: "View All Results",
    hero_badge_featured: "FEATURED",
    hero_badge_score: "Rating",
    hero_btn_watch: "Watch Now",
    hero_btn_details: "Details",
    hero_btn_fav: "Add to Favorites",
    hero_btn_fav_remove: "Remove from Favorites",
    section_popular: "Popular Shows",
    section_new: "Newly Added Shows",
    section_episodes: "Latest Episodes",
    section_drama: "Drama Shows",
    section_action: "Action Shows",
    section_scifi: "Sci-Fi Shows",
    section_comedy: "Comedy Shows",
    section_romantic: "Romance Shows",
    view_all: "View All",
    more: "Explore More",
    season: "Season",
    episode: "Episode",
    duration_min: "min",
    player_next_episode: "Next Episode",
    player_all_episodes: "All Episodes",
    player_resume_prompt: "You left off at {time}. Would you like to resume where you left off?",
    player_speed: "Speed",
    player_quality: "Quality",
    player_subtitle: "Subtitles",
    player_subtitle_off: "Off",
    player_subtitle_tr: "Turkish",
    player_subtitle_en: "English",
    sub_title: "Subscription Plans",
    sub_desc: "Ad-free, 4K Ultra HD and unlimited cinematic series streaming.",
    plan_free: "Free",
    plan_standard: "Standard HD",
    plan_ultra: "Ultra 4K Cinema",
    plan_select: "Choose Plan",
    plan_active: "Current Plan",
    footer_desc: "Global cinematic and licensed streaming platform. High quality visual streaming with zero interruptions.",
    footer_quick_links: "Quick Links",
    footer_legal: "Corporate & Legal",
    footer_about: "About Us",
    footer_contact: "Contact",
    footer_privacy: "Privacy Policy",
    footer_terms: "Terms of Service",
    footer_kvkk: "Data Protection (GDPR)",
    footer_copyright_notice: "Copyright Notice",
    footer_rights: "© 2026 SedaDizi. All rights reserved. Only licensed & authorized contents are broadcasted.",
    toast_token_saved: "Session token (sena_token) synchronized successfully.",
    toast_fav_added: "Added to your favorites.",
    toast_fav_removed: "Removed from favorites.",
    toast_login_success: "Login successful! Redirecting..."
  },
  de: {
    lang_name: "Deutsch",
    dir: "ltr",
    nav_home: "Startseite",
    nav_series: "Serien",
    nav_categories: "Kategorien",
    nav_new: "Neuheiten",
    nav_popular: "Beliebt",
    nav_premium: "Premium",
    nav_login: "Anmelden",
    nav_register: "Registrieren",
    nav_logout: "Abmelden",
    nav_profile: "Mein Profil",
    nav_favorites: "Favoriten",
    nav_history: "Verlauf",
    nav_search: "Suchen",
    search_placeholder: "Serie oder Schauspieler suchen...",
    search_results: "Suchergebnisse",
    search_no_results: "Keine Ergebnisse gefunden.",
    search_view_all: "Alle Ergebnisse anzeigen",
    hero_badge_featured: "HIGHLIGHT",
    hero_badge_score: "Bewertung",
    hero_btn_watch: "Jetzt ansehen",
    hero_btn_details: "Details",
    hero_btn_fav: "Zu Favoriten hinzufügen",
    hero_btn_fav_remove: "Aus Favoriten entfernen",
    section_popular: "Beliebte Serien",
    section_new: "Neu hinzugefügte Serien",
    section_episodes: "Neue Folgen",
    section_drama: "Drama Serien",
    section_action: "Action Serien",
    section_scifi: "Sci-Fi Serien",
    section_comedy: "Komödien",
    section_romantic: "Romantik Serien",
    view_all: "Alle ansehen",
    more: "Mehr entdecken",
    season: "Staffel",
    episode: "Folge",
    duration_min: "Min.",
    player_next_episode: "Nächste Folge",
    player_all_episodes: "Alle Folgen",
    player_resume_prompt: "Sie haben bei {time} aufgehört. Möchten Sie dort fortfahren?",
    player_speed: "Geschwindigkeit",
    player_quality: "Qualität",
    player_subtitle: "Untertitel",
    player_subtitle_off: "Aus",
    player_subtitle_tr: "Türkisch",
    player_subtitle_en: "Englisch",
    sub_title: "Abonnements",
    sub_desc: "Werbefreies Streaming in 4K Ultra HD.",
    plan_free: "Kostenlos",
    plan_standard: "Standard HD",
    plan_ultra: "Ultra 4K Kino",
    plan_select: "Plan wählen",
    plan_active: "Aktueller Plan",
    footer_desc: "Ihre globale Plattform für cineastische Serien in höchster Qualität.",
    footer_quick_links: "Schnelllinks",
    footer_legal: "Rechtliches",
    footer_about: "Über uns",
    footer_contact: "Kontakt",
    footer_privacy: "Datenschutz",
    footer_terms: "Nutzungsbedingungen",
    footer_kvkk: "DSGVO-Hinweise",
    footer_copyright_notice: "Urheberrecht",
    footer_rights: "© 2026 SedaDizi. Alle Rechte vorbehalten.",
    toast_token_saved: "Sitzungstoken erfolgreich synchronisiert.",
    toast_fav_added: "Zu Favoriten hinzugefügt.",
    toast_fav_removed: "Aus Favoriten entfernt.",
    toast_login_success: "Anmeldung erfolgreich!"
  },
  es: {
    lang_name: "Español",
    dir: "ltr",
    nav_home: "Inicio",
    nav_series: "Series",
    nav_categories: "Categorías",
    nav_new: "Novedades",
    nav_popular: "Popular",
    nav_premium: "Premium",
    nav_login: "Iniciar Sesión",
    nav_register: "Registrarse",
    nav_logout: "Cerrar Sesión",
    nav_profile: "Mi Perfil",
    nav_favorites: "Favoritos",
    nav_history: "Historial",
    nav_search: "Buscar",
    search_placeholder: "Buscar serie o actor...",
    search_results: "Resultados",
    search_no_results: "No se encontraron resultados.",
    search_view_all: "Ver todos los resultados",
    hero_badge_featured: "DESTACADO",
    hero_badge_score: "Puntuación",
    hero_btn_watch: "Ver Ahora",
    hero_btn_details: "Detalles",
    hero_btn_fav: "Añadir a Favoritos",
    hero_btn_fav_remove: "Eliminar de Favoritos",
    section_popular: "Series Populares",
    section_new: "Series Nuevas",
    section_episodes: "Últimos Episodios",
    section_drama: "Series de Drama",
    section_action: "Series de Acción",
    section_scifi: "Series de Ciencia Ficción",
    section_comedy: "Comedias",
    section_romantic: "Series Románticas",
    view_all: "Ver Todo",
    more: "Ver Más",
    season: "Temporada",
    episode: "Episodio",
    duration_min: "min",
    player_next_episode: "Siguiente Episodio",
    player_all_episodes: "Todos los Episodios",
    player_resume_prompt: "Te quedaste en {time}. ¿Quieres continuar?",
    player_speed: "Velocidad",
    player_quality: "Calidad",
    player_subtitle: "Subtítulos",
    player_subtitle_off: "Desactivado",
    player_subtitle_tr: "Turco",
    player_subtitle_en: "Inglés",
    sub_title: "Planes de Suscripción",
    sub_desc: "Streaming sin anuncios en 4K Ultra HD.",
    plan_free: "Gratis",
    plan_standard: "Estándar HD",
    plan_ultra: "Ultra 4K Cine",
    plan_select: "Seleccionar Plan",
    plan_active: "Plan Actual",
    footer_desc: "Plataforma global de streaming con calidad cinematográfica.",
    footer_quick_links: "Enlaces Rápidos",
    footer_legal: "Legal y Corporativo",
    footer_about: "Sobre Nosotros",
    footer_contact: "Contacto",
    footer_privacy: "Política de Privacidad",
    footer_terms: "Términos de Servicio",
    footer_kvkk: "Protección de Datos",
    footer_copyright_notice: "Derechos de Autor",
    footer_rights: "© 2026 SedaDizi. Todos los derechos reservados.",
    toast_token_saved: "Token sincronizado con éxito.",
    toast_fav_added: "Añadido a favoritos.",
    toast_fav_removed: "Eliminado de favoritos.",
    toast_login_success: "¡Inicio de sesión exitoso!"
  },
  ar: {
    lang_name: "العربية",
    dir: "rtl",
    nav_home: "الرئيسية",
    nav_series: "المسلسلات",
    nav_categories: "التصنيفات",
    nav_new: "أحدث الإضافات",
    nav_popular: "الأكثر شهرة",
    nav_premium: "بريميوم",
    nav_login: "تسجيل الدخول",
    nav_register: "إنشاء حساب",
    nav_logout: "تسجيل الخروج",
    nav_profile: "ملفي الشخصي",
    nav_favorites: "المفضلة",
    nav_history: "سجل المشاهدة",
    nav_search: "بحث",
    search_placeholder: "ابحث عن مسلسل أو ممثل...",
    search_results: "نتائج البحث",
    search_no_results: "لم يتم العثور على نتائج.",
    search_view_all: "عرض جميع النتائج",
    hero_badge_featured: "مميز",
    hero_badge_score: "التقييم",
    hero_btn_watch: "شاهد الآن",
    hero_btn_details: "التفاصيل",
    hero_btn_fav: "إضافة للمفضلة",
    hero_btn_fav_remove: "إزالة من المفضلة",
    section_popular: "المسلسلات الشائعة",
    section_new: "المسلسلات المضافة حديثاً",
    section_episodes: "الحلقات الجديدة",
    section_drama: "مسلسلات دراما",
    section_action: "مسلسلات أكشن",
    section_scifi: "مسلسلات خيال علمي",
    section_comedy: "مسلسلات كوميدية",
    section_romantic: "مسلسلات رومانسية",
    view_all: "عرض الكل",
    more: "المزيد",
    season: "الموسم",
    episode: "الحلقة",
    duration_min: "دقيقة",
    player_next_episode: "الحلقة التالية",
    player_all_episodes: "جميع الحلقات",
    player_resume_prompt: "توقفت عند {time}. هل ترغب في المتابعة؟",
    player_speed: "السرعة",
    player_quality: "الجودة",
    player_subtitle: "الترجمة",
    player_subtitle_off: "إيقاف",
    player_subtitle_tr: "التركية",
    player_subtitle_en: "الإنجليزية",
    sub_title: "باقات الاشتراك",
    sub_desc: "مشاهدة بدون إعلانات وبدقة 4K Ultra HD السينمائية.",
    plan_free: "مجاني",
    plan_standard: "HD قياسي",
    plan_ultra: "سينما 4K فائق",
    plan_select: "اختر الباقة",
    plan_active: "باقتك الحالية",
    footer_desc: "المنصة العالمية للبث السينمائي المرخص وبأعلى جودة.",
    footer_quick_links: "روابط سريعة",
    footer_legal: "قانوني",
    footer_about: "من نحن",
    footer_contact: "اتصل بنا",
    footer_privacy: "سياسة الخصوصية",
    footer_terms: "شروط الاستخدام",
    footer_kvkk: "حماية البيانات",
    footer_copyright_notice: "حقوق النشر",
    footer_rights: "© 2026 SedaDizi. جميع الحقوق محفوظة.",
    toast_token_saved: "تمت مزامنة رمز الجلسة بنجاح.",
    toast_fav_added: "تمت الإضافة إلى المفضلة.",
    toast_fav_removed: "تمت الإزالة من المفضلة.",
    toast_login_success: "تم تسجيل الدخول بنجاح!"
  },
  ru: {
    lang_name: "Русский",
    dir: "ltr",
    nav_home: "Главная",
    nav_series: "Сериалы",
    nav_categories: "Категории",
    nav_new: "Новинки",
    nav_popular: "Популярное",
    nav_premium: "Премиум",
    nav_login: "Войти",
    nav_register: "Регистрация",
    nav_logout: "Выйти",
    nav_profile: "Мой Профиль",
    nav_favorites: "Избранное",
    nav_history: "История",
    nav_search: "Поиск",
    search_placeholder: "Поиск сериала или актера...",
    search_results: "Результаты поиска",
    search_no_results: "Ничего не найдено.",
    search_view_all: "Показать все результаты",
    hero_badge_featured: "РЕКОМЕНДУЕМ",
    hero_badge_score: "Рейтинг",
    hero_btn_watch: "Смотреть",
    hero_btn_details: "Подробнее",
    hero_btn_fav: "В Избранное",
    hero_btn_fav_remove: "Удалить из избранного",
    section_popular: "Популярные сериалы",
    section_new: "Новые сериалы",
    section_episodes: "Свежие серии",
    section_drama: "Драмы",
    section_action: "Боевики",
    section_scifi: "Фантастика",
    section_comedy: "Комедии",
    section_romantic: "Мелодрамы",
    view_all: "Смотреть все",
    more: "Ещё",
    season: "Сезон",
    episode: "Серия",
    duration_min: "мин.",
    player_next_episode: "Следующая серия",
    player_all_episodes: "Все серии",
    player_resume_prompt: "Вы остановились на {time}. Продолжить просмотр?",
    player_speed: "Скорость",
    player_quality: "Качество",
    player_subtitle: "Субтитры",
    player_subtitle_off: "Выкл.",
    player_subtitle_tr: "Турецкий",
    player_subtitle_en: "Английский",
    sub_title: "Тарифные планы",
    sub_desc: "Без рекламы в качестве 4K Ultra HD.",
    plan_free: "Бесплатный",
    plan_standard: "Стандарт HD",
    plan_ultra: "Ультра 4K Кино",
    plan_select: "Выбрать",
    plan_active: "Текущий план",
    footer_desc: "Глобальная кинематографическая платформа потокового вещания.",
    footer_quick_links: "Быстрые ссылки",
    footer_legal: "Информация",
    footer_about: "О нас",
    footer_contact: "Контакты",
    footer_privacy: "Конфиденциальность",
    footer_terms: "Условия",
    footer_kvkk: "Защита данных",
    footer_copyright_notice: "Авторские права",
    footer_rights: "© 2026 SedaDizi. Все права защищены.",
    toast_token_saved: "Токен сессии успешно сохранен.",
    toast_fav_added: "Добавлено в избранное.",
    toast_fav_removed: "Удалено из избранного.",
    toast_login_success: "Вход выполнен успешно!"
  }
};

class I18nEngine {
  constructor() {
    this.currentLang = this.detectLanguage();
    this.init();
  }

  detectLanguage() {
    const saved = localStorage.getItem('sena_lang');
    if (saved && SEDA_TRANSLATIONS[saved]) return saved;
    const browserLang = (navigator.language || 'tr').split('-')[0].toLowerCase();
    return SEDA_TRANSLATIONS[browserLang] ? browserLang : 'tr';
  }

  init() {
    this.applyTranslations();
    document.addEventListener('DOMContentLoaded', () => {
      this.applyTranslations();
      this.renderLanguageSelector();
    });
  }

  setLanguage(lang) {
    if (!SEDA_TRANSLATIONS[lang]) return;
    this.currentLang = lang;
    localStorage.setItem('sena_lang', lang);
    this.applyTranslations();
    this.renderLanguageSelector();
    window.dispatchEvent(new CustomEvent('sena:languageChanged', { detail: { lang } }));
  }

  t(key, params = {}) {
    const dict = SEDA_TRANSLATIONS[this.currentLang] || SEDA_TRANSLATIONS['tr'];
    let text = dict[key] || SEDA_TRANSLATIONS['tr'][key] || key;
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
    }
    return text;
  }

  applyTranslations() {
    const langData = SEDA_TRANSLATIONS[this.currentLang] || SEDA_TRANSLATIONS['tr'];
    document.documentElement.lang = this.currentLang;
    document.documentElement.dir = langData.dir || 'ltr';

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      el.textContent = this.t(key);
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      el.placeholder = this.t(key);
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      el.title = this.t(key);
    });

    document.querySelectorAll('[data-i18n-aria]').forEach(el => {
      const key = el.getAttribute('data-i18n-aria');
      el.setAttribute('aria-label', this.t(key));
    });
  }

  renderLanguageSelector() {
    const containers = document.querySelectorAll('.lang-selector-mount');
    containers.forEach(container => {
      const current = SEDA_TRANSLATIONS[this.currentLang];
      container.innerHTML = `
        <div class="relative inline-block text-left" id="lang-dropdown-wrapper">
          <button type="button" onclick="window.senaApp.toggleLangMenu()" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800/80 hover:bg-zinc-700 text-xs font-semibold text-zinc-200 border border-white/10 transition" aria-expanded="false" aria-haspopup="true">
            <i class="fa-solid fa-globe text-pink-400"></i>
            <span>${current.lang_name}</span>
            <i class="fa-solid fa-chevron-down text-[10px] text-zinc-400"></i>
          </button>
          <div id="lang-dropdown-menu" class="hidden absolute right-0 mt-2 w-36 rounded-xl bg-[#17171C] border border-zinc-800 shadow-2xl py-1 z-50">
            ${Object.keys(SEDA_TRANSLATIONS).map(code => `
              <button type="button" onclick="window.senaI18n.setLanguage('${code}')" class="w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-zinc-800 transition ${this.currentLang === code ? 'text-pink-400 font-bold bg-zinc-800/40' : 'text-zinc-300'}">
                <span>${SEDA_TRANSLATIONS[code].lang_name}</span>
                ${this.currentLang === code ? '<i class="fa-solid fa-check text-xs"></i>' : ''}
              </button>
            `).join('')}
          </div>
        </div>
      `;
    });
  }
}

window.senaI18n = new I18nEngine();
