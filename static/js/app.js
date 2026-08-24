/**
 * SenaDizi – Dramakolik Birebir Frontend & Etkileşim Motoru
 */

// 1. Toast Bildirim Sistemi
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const bgClass = type === 'error' ? 'toast-error' : (type === 'info' ? 'toast-info' : 'toast-success');
  const icon = type === 'error' ? '✕' : (type === 'info' ? 'ℹ' : '✓');

  toast.className = `toast ${bgClass}`;
  toast.innerHTML = `<span style="font-size:16px;">${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// 2. Canlı Aktif Kullanıcı Sayacı
(function() {
  setInterval(function() {
    const el = document.getElementById('globalOnlineCount');
    if (el) {
      let count = parseInt(el.innerText.replace(/\./g, ''));
      if (isNaN(count)) return;
      let diff = Math.floor(Math.random() * 21) - 10;
      let newCount = count + diff;
      if (newCount < 1500) newCount = 1500;
      if (newCount > 3000) newCount = 3000;
      el.innerText = newCount.toLocaleString('tr-TR');
    }
  }, 3500);
})();

// 3. Hero Slider Kontrolü
let currentHero = 0;
let heroInterval;

function goToHero(idx) {
  const slides = document.querySelectorAll('.hero.slide');
  const dots = document.querySelectorAll('.hero-dot');
  if (!slides.length) return;
  
  slides[currentHero].classList.remove('active');
  if (dots[currentHero]) dots[currentHero].classList.remove('active');
  currentHero = (idx + slides.length) % slides.length;
  slides[currentHero].classList.add('active');
  if (dots[currentHero]) dots[currentHero].classList.add('active');
  resetHeroInterval();
}

function moveHero(dir) {
  goToHero(currentHero + dir);
}

function resetHeroInterval() {
  clearInterval(heroInterval);
  const slides = document.querySelectorAll('.hero.slide');
  if (slides.length > 1) {
    heroInterval = setInterval(() => moveHero(1), 5000);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const slides = document.querySelectorAll('.hero.slide');
  if (slides.length > 1) {
    resetHeroInterval();
  } else {
    document.querySelectorAll('.hero-nav, .hero-dots').forEach(el => el.style.display = 'none');
  }
});

// 4. Kaldığın Yerden Devam Et (localStorage & Server Sync)
window.devamTemizle = function(btnEl) {
  try { localStorage.removeItem('vipdrama_devam'); } catch(_) {}
  try { fetch('/api/user/progress/clear', { method: 'POST' }).catch(() => {}); } catch(_) {}
  const sec = document.getElementById('devamSection');
  if (sec) sec.style.display = 'none';
  showToast('İzleme geçmişi temizlendi.', 'info');
};

document.addEventListener('DOMContentLoaded', () => {
  try {
    const dv = JSON.parse(localStorage.getItem('vipdrama_devam') || '[]').filter(x => x && x.slug);
    const sec = document.getElementById('devamSection');
    const row = document.getElementById('devamRow');
    const btn = document.getElementById('devamTemizleBtn');
    
    if (dv.length && sec && row) {
      row.innerHTML = dv.slice(0, 15).map(x => {
        const esc = t => (t || '').replace(/</g, '&lt;');
        return `<a href="/dizi/${encodeURIComponent(x.slug)}?ep=${x.ep || 1}" class="card-continue">
          <div class="card-poster">
            <img src="${x.poster ? x.poster + '?v=2' : ''}" alt="${esc(x.baslik)}" width="425" height="640" loading="lazy" referrerpolicy="no-referrer-when-downgrade">
            <div class="ep-badge">▶ ${x.ep || 1}. Bölüm</div>
            <div class="play-icon">▶</div>
          </div>
          <div class="card-info"><div class="card-title">${esc(x.baslik)}</div></div>
        </a>`;
      }).join('');
      sec.style.display = 'block';
      if (btn) btn.style.display = 'inline-block';
    } else {
      if (btn) btn.style.display = 'none';
    }
  } catch(_) {}
});

// 5. Telegram & VIP Popup Modal (12 Saat Throttle)
function closeTelegramModal() {
  const tm = document.getElementById('telegramModal');
  if (tm) {
    tm.style.opacity = '0';
    setTimeout(() => { tm.style.display = 'none'; }, 300);
  }
  try { localStorage.setItem('tg_modal_seen', Date.now()); } catch(e) {}
}

(function() {
  let shown = 0;
  try { shown = parseInt(localStorage.getItem('tg_modal_seen') || '0'); } catch(e) {}
  if (Date.now() - shown > 43200000) { // 12 saat
    try { localStorage.setItem('tg_modal_seen', Date.now()); } catch(e) {}
    setTimeout(() => {
      const tm = document.getElementById('telegramModal');
      if (tm) {
        tm.style.display = 'flex';
        tm.style.opacity = '0';
        tm.style.transition = 'opacity 0.3s ease';
        setTimeout(() => { tm.style.opacity = '1'; }, 50);
      }
    }, 2000);
  }
})();

// 6. iOS PWA Banner
(function() {
  const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const isStandalone = window.navigator.standalone === true;
  let dismissed = false;
  try { dismissed = localStorage.getItem('iosBannerDismissed') === '1'; } catch(e) {}
  if (isIos && !isStandalone && !dismissed) {
    setTimeout(() => {
      const b = document.getElementById('iosBanner');
      if (b) b.style.display = 'block';
    }, 2000);
  }
})();

function iosBannerKapat() {
  const b = document.getElementById('iosBanner');
  if (b) b.style.display = 'none';
  try { localStorage.setItem('iosBannerDismissed', '1'); } catch(e) {}
}

// 7. Favori Ekle / Çıkar
async function toggleFavorite(seriesId, btnElement) {
  try {
    const res = await fetch(`/api/user/favorites/${seriesId}`, { method: 'POST' });
    if (res.status === 401) {
      window.location.href = `/giris?next=${encodeURIComponent(window.location.pathname)}`;
      return;
    }
    const data = await res.json();
    if (res.ok) {
      showToast(data.message || 'İşlem başarılı.', 'success');
      if (btnElement) {
        if (data.status === 'added') {
          btnElement.classList.add('text-red-500');
          btnElement.innerHTML = '❤️ Favorilerde';
        } else {
          btnElement.classList.remove('text-red-500');
          btnElement.innerHTML = '🤍 Favorilere Ekle';
        }
      }
    } else {
      showToast(data.detail || 'İşlem gerçekleştirilemedi.', 'error');
    }
  } catch (err) {
    showToast('Bağlantı hatası.', 'error');
  }
}

// 8. Çıkış Yap (Logout)
async function handleLogout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    try { localStorage.removeItem('flk_token'); } catch(e) {}
    showToast('Çıkış yapıldı...', 'success');
    setTimeout(() => window.location.href = '/', 500);
  } catch (err) {
    window.location.href = '/';
  }
}

// 9. PWA Kurulum Butonu
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const pwaBtn = document.getElementById('pwaInstallBtn');
  if (pwaBtn) pwaBtn.style.display = 'flex';
});

function pwaInstall() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(() => {
      deferredPrompt = null;
      const pwaBtn = document.getElementById('pwaInstallBtn');
      if (pwaBtn) pwaBtn.style.display = 'none';
    });
  } else {
    showToast('Uygulamayı yüklemek için tarayıcı menüsünden "Ana Ekrana Ekle"yi seçin.', 'info');
  }
}
