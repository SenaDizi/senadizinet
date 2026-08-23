/**
 * SenaDizi – Modern Frontend Motoru (Dramaflix & Dramakolik Stili)
 * Toast Bildirimleri, Canlı Arama, Favori Sistemi, Mobil Çekmece & Profil Etkileşimleri
 */

// Toast Bildirim Sistemi
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed bottom-20 md:bottom-6 right-6 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-4 md:px-0';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const bgClass = type === 'error' ? 'toast-error' : (type === 'info' ? 'toast-info' : 'toast-success');
  const icon = type === 'error' ? 'fa-circle-exclamation' : (type === 'info' ? 'fa-circle-info' : 'fa-circle-check');

  toast.className = `toast ${bgClass} pointer-events-auto`;
  toast.innerHTML = `
    <i class="fa-solid ${icon} text-base"></i>
    <span class="text-xs font-bold flex-1 leading-snug">${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Favori Ekle / Çıkar
async function toggleFavorite(seriesId, btnElement) {
  try {
    const res = await fetch(`/api/user/favorites/${seriesId}`, { method: 'POST' });
    if (res.status === 401) {
      window.location.href = `/giris?next=${encodeURIComponent(window.location.pathname)}`;
      return;
    }
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      if (btnElement) {
        const icon = btnElement.querySelector('i');
        const text = btnElement.querySelector('span');
        if (data.status === 'added') {
          btnElement.classList.add('text-pink-500', 'border-pink-500/50');
          if (icon) { icon.classList.remove('fa-regular'); icon.classList.add('fa-solid', 'text-pink-500'); }
          if (text) text.textContent = 'Favorilerden Çıkar';
        } else {
          btnElement.classList.remove('text-pink-500', 'border-pink-500/50');
          if (icon) { icon.classList.remove('fa-solid', 'text-pink-500'); icon.classList.add('fa-regular'); }
          if (text) text.textContent = 'Favorilere Ekle';
        }
      }
    } else {
      showToast(data.detail || 'İşlem başarısız.', 'error');
    }
  } catch (err) {
    showToast('Bağlantı hatası.', 'error');
  }
}

// Canlı Arama (Debounced Live Search)
let searchTimeout = null;
function handleHeaderSearch(input) {
  clearTimeout(searchTimeout);
  const q = input.value.trim();
  const dropdown = document.getElementById('search-dropdown');
  if (!dropdown) return;

  if (q.length < 2) {
    dropdown.classList.add('hidden');
    dropdown.innerHTML = '';
    return;
  }

  searchTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`/api/series/search?q=${encodeURIComponent(q)}&limit=6`);
      const data = await res.json();
      dropdown.innerHTML = '';

      if (data.series && data.series.length > 0) {
        data.series.forEach(item => {
          const row = document.createElement('a');
          row.href = `/dizi/${item.slug}`;
          row.className = 'flex items-center gap-3.5 p-3 hover:bg-white/10 transition-colors border-b border-white/5 last:border-0';
          row.innerHTML = `
            <img src="${item.poster_url}" class="w-10 h-14 object-cover rounded-xl shadow-md flex-shrink-0" alt="${item.title}">
            <div class="flex-1 min-w-0">
              <div class="text-xs font-bold text-white truncate">${item.title}</div>
              <div class="text-[11px] text-zinc-400 flex items-center gap-2 mt-0.5 font-medium">
                <span class="text-amber-400 font-bold">⭐ ${item.rating || '9.0'}</span>
                <span>•</span>
                <span>${item.release_year || '2026'}</span>
                <span>•</span>
                <span class="truncate">${item.country || 'Asya'}</span>
              </div>
            </div>
          `;
          dropdown.appendChild(row);
        });

        // Tümünü Gör Butonu
        const viewAll = document.createElement('a');
        viewAll.href = `/ara?q=${encodeURIComponent(q)}`;
        viewAll.className = 'block p-2.5 text-center text-xs font-black text-fuchsia-400 hover:text-fuchsia-300 hover:bg-white/5 transition-colors border-t border-white/10';
        viewAll.textContent = `Tüm Sonuçları Gör (${data.series.length}+)`;
        dropdown.appendChild(viewAll);

        dropdown.classList.remove('hidden');
      } else {
        dropdown.innerHTML = '<div class="p-4 text-center text-xs text-zinc-400">Sonuç bulunamadı.</div>';
        dropdown.classList.remove('hidden');
      }
    } catch (err) {
      console.error(err);
    }
  }, 250);
}

// Dışarı tıklanınca arama kutusunu kapat
document.addEventListener('click', (e) => {
  const searchContainer = document.getElementById('search-container');
  const dropdown = document.getElementById('search-dropdown');
  if (dropdown && searchContainer && !searchContainer.contains(e.target)) {
    dropdown.classList.add('hidden');
  }
});

// Mobil Hamburger Çekmece Menü (Kusursuz Soldan Açılma ve Z-Index Kontrolü)
function toggleMobileMenu(forceState) {
  const drawer = document.getElementById('mobile-drawer');
  const backdrop = document.getElementById('drawer-backdrop');
  const panel = document.getElementById('drawer-panel');
  const hamburgerBtn = document.getElementById('hamburger-btn');
  if (!drawer || !panel || !backdrop) return;

  const isCurrentlyOpen = panel.classList.contains('translate-x-0');
  const shouldOpen = forceState !== undefined ? forceState : !isCurrentlyOpen;

  if (shouldOpen) {
    drawer.classList.remove('pointer-events-none');
    backdrop.classList.remove('opacity-0');
    backdrop.classList.add('opacity-100');
    panel.classList.remove('-translate-x-full');
    panel.classList.add('translate-x-0');
    document.body.style.overflow = 'hidden';
    if (hamburgerBtn) {
      hamburgerBtn.innerHTML = '<i class="fa-solid fa-xmark text-xl text-fuchsia-400"></i>';
    }
  } else {
    backdrop.classList.remove('opacity-100');
    backdrop.classList.add('opacity-0');
    panel.classList.remove('translate-x-0');
    panel.classList.add('-translate-x-full');
    drawer.classList.add('pointer-events-none');
    document.body.style.overflow = '';
    if (hamburgerBtn) {
      hamburgerBtn.innerHTML = '<i class="fa-solid fa-bars-staggered text-xl text-zinc-300"></i>';
    }
  }
}

// ESC tuşu ile çekmeceyi kapat
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    toggleMobileMenu(false);
    toggleUserMenu(false);
  }
});

// Kullanıcı Profil Menüsü Dropdown
function toggleUserMenu(forceState) {
  const menu = document.getElementById('user-dropdown');
  if (!menu) return;
  if (forceState !== undefined) {
    if (forceState) menu.classList.remove('hidden');
    else menu.classList.add('hidden');
  } else {
    menu.classList.toggle('hidden');
  }
}

// Dışarı tıklanınca profil menüsünü kapat
document.addEventListener('click', (e) => {
  const userMenu = document.getElementById('user-dropdown');
  if (userMenu && !userMenu.contains(e.target) && !e.target.closest('button[onclick="toggleUserMenu()"]')) {
    userMenu.classList.add('hidden');
  }
});

// Oturum Kapatma (Logout)
async function handleLogout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    showToast('Çıkış yapıldı, yönlendiriliyorsunuz...', 'success');
    setTimeout(() => window.location.href = '/', 700);
  } catch (err) {
    window.location.href = '/';
  }
}

// Abonelik Başlatma
async function selectPlan(planSlug) {
  try {
    const res = await fetch('/api/subscriptions/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan_slug: planSlug })
    });
    if (res.status === 401) {
      window.location.href = `/giris?next=/abonelik`;
      return;
    }
    const data = await res.json();
    if (res.ok && data.success) {
      showToast(data.message, 'success');
      setTimeout(() => window.location.href = '/profil', 1000);
    } else {
      showToast(data.detail || 'Abonelik işlemi gerçekleştirilemedi.', 'error');
    }
  } catch (err) {
    showToast('Bağlantı hatası oluştu.', 'error');
  }
}
