/**
 * SedaDizi Multi-Server & Universal Embed Player Suite
 * Cross-Browser (iOS Safari, Chrome, Edge, Firefox) & DMCA Safe Harbor Compliant
 */

class SedaDiziPlayer {
  constructor(options = {}) {
    this.videoId = options.videoId || 'sedadizi-player';
    this.iframeId = options.iframeId || 'sedadizi-iframe';
    this.seriesSlug = options.seriesSlug || 'squid-game-2';
    this.episodeId = options.episodeId || 1;
    this.video = document.getElementById(this.videoId);
    this.iframe = document.getElementById(this.iframeId);
    if (!this.video && !this.iframe) return;

    this.container = (this.video ? this.video.closest('.player-container') : null) || (this.iframe ? this.iframe.closest('.player-container') : null);
    this.controls = document.getElementById('player-controls');
    this.playBtn = document.getElementById('play-btn');
    this.centerPlayBtn = document.getElementById('center-play-btn');
    this.seekBar = document.getElementById('seek-bar');
    this.timeDisplay = document.getElementById('time-display');
    this.volumeBar = document.getElementById('volume-bar');
    this.volumeBtn = document.getElementById('volume-btn');
    this.fullscreenBtn = document.getElementById('fullscreen-btn');
    this.speedSelect = document.getElementById('speed-select');
    this.theaterBtn = document.getElementById('theater-btn');

    this.currentServer = 'server1';
    this.controlsTimeout = null;
    this.init();
  }

  init() {
    if (this.video) {
      this.setupIOSCompatibility();
      this.bindEvents();
      this.checkResumePlayback();
      this.startProgressSaver();
    }
    this.setupKeyboardShortcuts();
  }

  setupIOSCompatibility() {
    if (!this.video) return;
    this.video.setAttribute('playsinline', 'true');
    this.video.setAttribute('webkit-playsinline', 'true');
    this.video.setAttribute('x5-playsinline', 'true');
    this.video.preload = 'metadata';
  }

  switchServer(serverKey, serverUrl, btnElement) {
    this.currentServer = serverKey;
    const isEmbed = serverKey === 'server3' || serverUrl.includes('embed') || serverUrl.includes('iframe');

    if (isEmbed) {
      if (this.video) {
        this.video.pause();
        this.video.classList.add('hidden');
      }
      if (this.controls) this.controls.classList.add('hidden');

      let iframeEl = document.getElementById('sedadizi-iframe');
      if (!iframeEl && this.container) {
        iframeEl = document.createElement('iframe');
        iframeEl.id = 'sedadizi-iframe';
        iframeEl.className = 'w-full h-full border-0';
        iframeEl.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
        iframeEl.allowFullscreen = true;
        this.container.appendChild(iframeEl);
      }
      if (iframeEl) {
        iframeEl.src = serverUrl.includes('http') ? serverUrl : 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4';
        iframeEl.classList.remove('hidden');
      }
    } else {
      const iframeEl = document.getElementById('sedadizi-iframe');
      if (iframeEl) iframeEl.classList.add('hidden');
      if (this.video) {
        this.video.classList.remove('hidden');
        if (this.controls) this.controls.classList.remove('hidden');
        const currentTime = this.video.currentTime;
        const isPaused = this.video.paused;

        this.video.src = serverUrl;
        this.video.load();
        this.video.addEventListener('loadedmetadata', () => {
          this.video.currentTime = currentTime;
          if (!isPaused) this.video.play().catch(() => {});
        }, { once: true });
      }
    }

    document.querySelectorAll('.server-btn').forEach(btn => {
      btn.classList.remove('bg-pink-600', 'text-white', 'border-pink-500');
      btn.classList.add('bg-[#1D162B]', 'text-zinc-300', 'border-zinc-700');
    });
    if (btnElement) {
      btnElement.classList.remove('bg-[#1D162B]', 'text-zinc-300', 'border-zinc-700');
      btnElement.classList.add('bg-pink-600', 'text-white', 'border-pink-500');
    }

    if (window.sedaApp) {
      window.sedaApp.showToast(`${btnElement ? btnElement.textContent.trim() : serverKey} aktif edildi.`, 'success');
    }
  }

  bindEvents() {
    if (!this.video) return;

    this.video.addEventListener('click', () => this.togglePlay());
    if (this.playBtn) this.playBtn.addEventListener('click', () => this.togglePlay());
    if (this.centerPlayBtn) this.centerPlayBtn.addEventListener('click', () => this.togglePlay());

    this.video.addEventListener('timeupdate', () => this.onTimeUpdate());
    this.video.addEventListener('play', () => this.updatePlayUI(true));
    this.video.addEventListener('pause', () => this.updatePlayUI(false));
    this.video.addEventListener('ended', () => this.onEnded());

    if (this.seekBar) {
      this.seekBar.addEventListener('input', (e) => {
        if (this.video.duration) {
          this.video.currentTime = (e.target.value / 100) * this.video.duration;
        }
      });
    }

    if (this.volumeBar) {
      this.volumeBar.addEventListener('input', (e) => {
        this.video.volume = e.target.value;
        this.video.muted = (e.target.value == 0);
        this.updateVolumeUI();
      });
    }
    if (this.volumeBtn) this.volumeBtn.addEventListener('click', () => this.toggleMute());
    if (this.fullscreenBtn) this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
    if (this.theaterBtn) this.theaterBtn.addEventListener('click', () => this.toggleTheaterMode());

    if (this.speedSelect) {
      this.speedSelect.addEventListener('change', (e) => {
        this.video.playbackRate = parseFloat(e.target.value);
      });
    }

    if (this.container) {
      this.container.addEventListener('mousemove', () => this.showControls());
      this.container.addEventListener('touchstart', () => this.showControls(), { passive: true });
      this.container.addEventListener('mouseleave', () => this.hideControls());
    }
  }

  toggleTheaterMode() {
    let backdrop = document.getElementById('theater-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.id = 'theater-backdrop';
      document.body.appendChild(backdrop);
    }

    const isTheater = this.container.classList.toggle('theater-mode');
    backdrop.classList.toggle('active', isTheater);

    if (this.theaterBtn) {
      this.theaterBtn.innerHTML = isTheater 
        ? '<i class="fa-solid fa-lightbulb text-pink-400"></i>' 
        : '<i class="fa-regular fa-lightbulb"></i>';
    }
  }

  showControls() {
    if (this.controls) {
      this.controls.classList.remove('opacity-0', 'pointer-events-none');
      this.controls.classList.add('opacity-100');
    }
    clearTimeout(this.controlsTimeout);
    if (this.video && !this.video.paused) {
      this.controlsTimeout = setTimeout(() => this.hideControls(), 3500);
    }
  }

  hideControls() {
    if (this.controls && this.video && !this.video.paused) {
      this.controls.classList.remove('opacity-100');
      this.controls.classList.add('opacity-0', 'pointer-events-none');
    }
  }

  togglePlay() {
    if (!this.video) return;
    if (this.video.paused || this.video.ended) {
      const playPromise = this.video.play();
      if (playPromise !== undefined) {
        playPromise.catch(() => {
          this.video.muted = true;
          this.video.play();
          this.updateVolumeUI();
        });
      }
    } else {
      this.video.pause();
    }
  }

  updatePlayUI(isPlaying) {
    if (this.playBtn) {
      this.playBtn.innerHTML = isPlaying ? '<i class="fa-solid fa-pause"></i>' : '<i class="fa-solid fa-play"></i>';
    }
    if (this.centerPlayBtn) {
      this.centerPlayBtn.classList.toggle('hidden', isPlaying);
    }
  }

  onTimeUpdate() {
    if (this.video && this.video.duration) {
      const percent = (this.video.currentTime / this.video.duration) * 100;
      if (this.seekBar) this.seekBar.value = percent;
      if (this.timeDisplay) {
        this.timeDisplay.textContent = `${this.formatTime(this.video.currentTime)} / ${this.formatTime(this.video.duration)}`;
      }
    }
  }

  toggleMute() {
    if (!this.video) return;
    this.video.muted = !this.video.muted;
    this.updateVolumeUI();
  }

  updateVolumeUI() {
    if (this.volumeBtn && this.video) {
      if (this.video.muted || this.video.volume === 0) {
        this.volumeBtn.innerHTML = '<i class="fa-solid fa-volume-xmark text-pink-400"></i>';
        if (this.volumeBar) this.volumeBar.value = 0;
      } else {
        this.volumeBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
        if (this.volumeBar) this.volumeBar.value = this.video.volume;
      }
    }
  }

  toggleFullscreen() {
    const el = this.container || this.video;
    if (!el) return;
    if (document.fullscreenElement || document.webkitFullscreenElement) {
      if (document.exitFullscreen) document.exitFullscreen();
      else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
    } else {
      if (el.requestFullscreen) el.requestFullscreen();
      else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
      else if (this.video && this.video.webkitEnterFullscreen) this.video.webkitEnterFullscreen();
    }
  }

  checkResumePlayback() {
    if (!this.video) return;
    const key = `sedadizi_watch_${this.seriesSlug}_ep${this.episodeId}`;
    const saved = parseFloat(localStorage.getItem(key));
    if (saved && saved > 10) {
      this.video.addEventListener('loadedmetadata', () => {
        if (saved < (this.video.duration - 30)) {
          if (confirm(`Bu bölüme en son ${this.formatTime(saved)} dakikasında kalmıştınız. Devam etmek ister misiniz?`)) {
            this.video.currentTime = saved;
          }
        }
      }, { once: true });
    }
  }

  startProgressSaver() {
    setInterval(() => {
      if (this.video && !this.video.paused && this.video.currentTime > 5) {
        const key = `sedadizi_watch_${this.seriesSlug}_ep${this.episodeId}`;
        localStorage.setItem(key, this.video.currentTime);
      }
    }, 4000);
  }

  onEnded() {
    const nextBtn = document.getElementById('next-episode-cta');
    if (nextBtn) {
      if (window.sedaApp) window.sedaApp.showToast("Bölüm bitti! Sonraki bölüme geçiliyor...", "success");
      setTimeout(() => nextBtn.click(), 2500);
    }
  }

  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
      if (e.code === 'Space' || e.code === 'KeyK') { e.preventDefault(); this.togglePlay(); }
      else if (this.video && (e.code === 'ArrowLeft' || e.code === 'KeyJ')) { e.preventDefault(); this.video.currentTime = Math.max(0, this.video.currentTime - 10); }
      else if (this.video && (e.code === 'ArrowRight' || e.code === 'KeyL')) { e.preventDefault(); this.video.currentTime = Math.min(this.video.duration, this.video.currentTime + 10); }
      else if (e.code === 'KeyF') { e.preventDefault(); this.toggleFullscreen(); }
      else if (e.code === 'KeyM') { e.preventDefault(); this.toggleMute(); }
    });
  }

  formatTime(sec) {
    if (isNaN(sec)) return "00:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
}

window.SedaDiziPlayer = SedaDiziPlayer;
