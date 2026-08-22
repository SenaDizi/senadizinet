/**
 * SedaDizi - Core Frontend Application Engine (Pink Cinema)
 */

window.SEDA_SERIES_DATABASE = [];

class SedaApp {
  constructor() {
    this.searchTimeout = null;
    this.initTokenSync();
    this.bindGlobalEvents();
    this.loadSeriesData();
  }

  async loadSeriesData() {
    try {
      const res = await fetch('diziler.json?t=' + Date.now());
      if (res.ok) {
        const data = await res.json();
        if (data && data.series && data.series.length > 0) {
          window.SEDA_SERIES_DATABASE = data.series;
          window.dispatchEvent(new CustomEvent('seda:seriesLoaded', { detail: data.series }));
          console.log(`[SedaDizi] ${data.series.length} dizi yüklendi.`);
        }
      }
    } catch (err) {
      console.warn("[SedaDizi] Veri yüklenirken hata:", err);
    }
  }

  initTokenSync() {
    const token = localStorage.getItem('seda_token') || localStorage.getItem('sena_token');
    if (token) {
      document.querySelectorAll('input[type="text"], input[type="password"], textarea').forEach(box => {
        if (!box.value && (box.placeholder && (box.placeholder.includes('Bearer') || box.placeholder.includes('Token') || box.placeholder.includes('Cookie')))) {
          box.value = token;
        }
      });
    }
  }

  showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'fixed bottom-20 md:bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none px-4 md:px-0';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgClass = type === 'error' 
      ? 'bg-rose-950/90 border-rose-500 text-rose-100' 
      : 'bg-[#1D162B]/95 border-pink-500 text-white shadow-pink-500/20';
    const icon = type === 'error' ? 'fa-circle-exclamation text-rose-400' : 'fa-circle-check text-pink-400';

    toast.className = `flex items-center gap-3 p-4 rounded-2xl border shadow-2xl backdrop-blur-md transform transition-all duration-300 pointer-events-auto opacity-0 translate-y-4 ${bgClass}`;
    toast.innerHTML = `
      <i class="fa-solid ${icon} text-lg flex-shrink-0"></i>
      <span class="text-xs sm:text-sm font-medium flex-1">${message}</span>
    `;

    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.remove('opacity-0', 'translate-y-4'));

    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-4');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  toggleFavorite(seriesId, btnElement) {
    let favs = JSON.parse(localStorage.getItem('seda_favs') || '[]');
    const index = favs.indexOf(seriesId);
    const isAdding = (index === -1);

    if (isAdding) favs.push(seriesId);
    else favs.splice(index, 1);

    localStorage.setItem('seda_favs', JSON.stringify(favs));
    this.showToast(isAdding ? 'Favorilerinize eklendi.' : 'Favorilerden kaldırıldı.', 'success');

    if (btnElement) {
      const icon = btnElement.querySelector('i');
      if (isAdding) {
        btnElement.classList.add('text-pink-500', 'border-pink-500');
        if (icon) { icon.classList.remove('fa-regular'); icon.classList.add('fa-solid'); }
      } else {
        btnElement.classList.remove('text-pink-500', 'border-pink-500');
        if (icon) { icon.classList.remove('fa-solid'); icon.classList.add('fa-regular'); }
      }
    }
  }

  handleHeaderSearch(input) {
    clearTimeout(this.searchTimeout);
    const q = input.value.trim().toLowerCase();
    const dropdown = document.getElementById('search-dropdown');
    if (!dropdown) return;

    if (q.length < 2) {
      dropdown.classList.add('hidden');
      dropdown.innerHTML = '';
      return;
    }

    this.searchTimeout = setTimeout(() => {
      const list = window.SEDA_SERIES_DATABASE || [];
      const matches = list.filter(s => 
        (s.title && s.title.toLowerCase().includes(q)) || 
        (s.title_en && s.title_en.toLowerCase().includes(q)) ||
        (s.title_original && s.title_original.toLowerCase().includes(q)) ||
        (s.genres && s.genres.some(g => g.includes(q)))
      );

      dropdown.innerHTML = '';

      if (matches.length > 0) {
        matches.slice(0, 5).forEach(item => {
          const row = document.createElement('a');
          row.href = `dizi-detay.html?slug=${item.slug}`;
          row.className = 'flex items-center gap-3 p-3 hover:bg-[#261D38] transition rounded-xl border-b border-white/5 last:border-0';
          row.innerHTML = `
            <img src="${item.poster}" class="w-10 h-14 object-cover rounded-lg shadow flex-shrink-0" alt="${item.title}" loading="lazy">
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold text-white truncate">${item.title}</div>
              <div class="text-xs text-pink-300 flex items-center gap-2 mt-0.5">
                <span class="text-amber-400 font-bold">⭐ ${item.rating}</span>
                <span>•</span>
                <span>${item.category_badge || item.country}</span>
              </div>
            </div>
          `;
          dropdown.appendChild(row);
        });

        const viewAll = document.createElement('a');
        viewAll.href = `diziler.html?q=${encodeURIComponent(q)}`;
        viewAll.className = 'block p-2.5 text-center text-xs font-bold text-pink-400 hover:text-pink-300 hover:bg-[#261D38] transition rounded-b-xl border-t border-white/5';
        viewAll.textContent = 'Tüm Sonuçları Gör';
        dropdown.appendChild(viewAll);

        dropdown.classList.remove('hidden');
      } else {
        dropdown.innerHTML = `<div class="p-4 text-center text-xs text-zinc-400">Sonuç bulunamadı.</div>`;
        dropdown.classList.remove('hidden');
      }
    }, 200);
  }

  toggleMobileMenu() {
    const menu = document.getElementById('mobile-drawer');
    if (menu) menu.classList.toggle('hidden');
  }

  toggleLangMenu() {
    const menu = document.getElementById('lang-dropdown-menu');
    if (menu) menu.classList.toggle('hidden');
  }

  bindGlobalEvents() {
    document.addEventListener('click', (e) => {
      const searchContainer = document.getElementById('search-container');
      const dropdown = document.getElementById('search-dropdown');
      if (dropdown && searchContainer && !searchContainer.contains(e.target)) {
        dropdown.classList.add('hidden');
      }
      const langWrapper = document.getElementById('lang-dropdown-wrapper');
      const langMenu = document.getElementById('lang-dropdown-menu');
      if (langMenu && langWrapper && !langWrapper.contains(e.target)) {
        langMenu.classList.add('hidden');
      }
    });
  }
}

window.sedaApp = new SedaApp();
window.toggleFavorite = (id, el) => window.sedaApp.toggleFavorite(id, el);
window.handleHeaderSearch = (el) => window.sedaApp.handleHeaderSearch(el);
window.toggleMobileMenu = () => window.sedaApp.toggleMobileMenu();
