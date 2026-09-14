// SenaDizi Downloader & Video Studio PRO - Frontend Engine

function getClientId() {
    let cid = localStorage.getItem('senadizi_client_id');
    if (!cid || cid.length < 8) {
        cid = 'user_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 9);
        localStorage.setItem('senadizi_client_id', cid);
    }
    try {
        document.cookie = `senadizi_client_id=${cid}; path=/; max-age=31536000; SameSite=Lax`;
    } catch (e) {}
    return cid;
}

function getClientHeaders(extra = {}) {
    return Object.assign({
        'X-Client-ID': getClientId()
    }, extra);
}

let parsedEpisodes = [];
let scannedSeries = null;
let statusInterval = null;
let completedInterval = null;
let viralPollingInterval = null;
let promoPollingInterval = null;
let currentViralTaskId = null;
let currentPromoTaskId = null;

document.addEventListener('DOMContentLoaded', () => {
    // 1. Navigation Tab Switching
    initTabs();

    // 2. Downloader Handlers
    initDownloader();

    // 3. Viral Video Studio Handlers
    initViralStudio();

    // 4. Promo Video Creator Handlers
    initPromoCreator();

    // 5. Server IP & Tunnel Polling
    fetchServerIps();
    setInterval(fetchServerIps, 3500);
    
    // 6. Automated Background VIP Token Sync
    autoSyncTokens();
    setInterval(autoSyncTokens, 10000);

    startStatusPolling();
    startCompletedPolling();
});

// ---------------- TAB NAVIGATION ----------------
function initTabs() {
    const tabs = [
        { btn: document.getElementById('tab-downloader'), panel: document.getElementById('panel-downloader') },
        { btn: document.getElementById('tab-viral'), panel: document.getElementById('panel-viral') },
        { btn: document.getElementById('tab-promo'), panel: document.getElementById('panel-promo') }
    ];

    tabs.forEach(t => {
        if (!t.btn || !t.panel) return;
        t.btn.addEventListener('click', () => {
            tabs.forEach(other => {
                if (other.btn) other.btn.classList.remove('active');
                if (other.panel) {
                    other.panel.classList.remove('active');
                    other.panel.style.display = 'none';
                }
            });
            t.btn.classList.add('active');
            t.panel.classList.add('active');
            t.panel.style.display = 'block';

            if (t.btn.id === 'tab-viral') {
                refreshViralVideoOptions();
            } else if (t.btn.id === 'tab-promo') {
                loadPromoCovers();
            }
        });
    });
}

// ---------------- DOWNLOADER ENGINE ----------------
function initDownloader() {
    const btnScan = document.getElementById('btn-scan');
    const inputUrl = document.getElementById('series-url');
    const btnDownloadSelected = document.getElementById('btn-download-selected');
    const btnDownloadMerged = document.getElementById('btn-download-merged');
    const btnSelectAll = document.getElementById('btn-select-all');
    const btnSelect10 = document.getElementById('btn-select-10');
    const btnSelect20 = document.getElementById('btn-select-20');
    const btnDeselectAll = document.getElementById('btn-deselect-all');
    const btnApplyRange = document.getElementById('btn-apply-range');
    const btnClearActive = document.getElementById('btn-clear-active');

    if (btnScan) btnScan.addEventListener('click', scanSeriesUrl);
    if (inputUrl) {
        inputUrl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') scanSeriesUrl();
        });
    }

    if (btnSelectAll) {
        btnSelectAll.addEventListener('click', () => {
            document.querySelectorAll('.ep-checkbox-input').forEach(chk => chk.checked = true);
            updateSelectedBadge();
        });
    }

    if (btnSelect10) {
        btnSelect10.addEventListener('click', () => {
            document.querySelectorAll('.ep-checkbox-input').forEach((chk, idx) => {
                chk.checked = (idx < 10);
            });
            updateSelectedBadge();
        });
    }

    if (btnSelect20) {
        btnSelect20.addEventListener('click', () => {
            document.querySelectorAll('.ep-checkbox-input').forEach((chk, idx) => {
                chk.checked = (idx < 20);
            });
            updateSelectedBadge();
        });
    }

    if (btnDeselectAll) {
        btnDeselectAll.addEventListener('click', () => {
            document.querySelectorAll('.ep-checkbox-input').forEach(chk => chk.checked = false);
            updateSelectedBadge();
        });
    }

    if (btnApplyRange) {
        btnApplyRange.addEventListener('click', applyRangeSelection);
    }

    if (btnDownloadSelected) btnDownloadSelected.addEventListener('click', triggerDownloadQueue);
    if (btnDownloadMerged) btnDownloadMerged.addEventListener('click', triggerMergedDownload);

    const btnSelectAllCompleted = document.getElementById('btn-select-all-completed');
    const btnDeleteSelectedCompleted = document.getElementById('btn-delete-selected-completed');
    
    if (btnSelectAllCompleted && btnDeleteSelectedCompleted) {
        btnSelectAllCompleted.addEventListener('click', () => {
            const checkboxes = document.querySelectorAll('.completed-select-chk');
            const allChecked = Array.from(checkboxes).every(chk => chk.checked);
            checkboxes.forEach(chk => chk.checked = !allChecked);
            btnSelectAllCompleted.innerText = allChecked ? "Tümünü Seç" : "Seçimleri Kaldır";
        });
        
        btnDeleteSelectedCompleted.addEventListener('click', deleteSelectedCompletedFiles);
    }

    if (btnClearActive) {
        btnClearActive.addEventListener('click', async () => {
            try {
                await fetch(`/indir/api/status/clear?client_id=${encodeURIComponent(getClientId())}`, {
                    method: 'POST',
                    headers: getClientHeaders({ 'Content-Type': 'application/json' }),
                    body: '{}'
                });
                updateDownloadsDashboard({});
            } catch (e) {
                console.error("Clear error:", e);
            }
        });
    }
}

function copyText(text, btnElement) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            if (btnElement) {
                const orig = btnElement.innerHTML;
                btnElement.innerHTML = '<i class="fa-solid fa-check"></i> Kopyalandı!';
                btnElement.style.background = '#22c55e';
                btnElement.style.color = '#fff';
                setTimeout(() => {
                    btnElement.innerHTML = orig;
                    btnElement.style.background = '';
                    btnElement.style.color = '';
                }, 2000);
            }
        }).catch(() => {
            prompt('Link:', text);
        });
    } else {
        prompt('Link:', text);
    }
}

async function fetchServerIps() {
    try {
        let res;
        try {
            res = await fetch(`/downloader/api/ip?t=${Date.now()}`);
        } catch (err) {
            res = await fetch(`/indir/api/ip?t=${Date.now()}`);
        }
        if (res && res.ok) {
            const data = await res.json();
            const permUrl = data.permanent_url || 'https://www.senadizi.com/downloader';
            const workerOnline = data.worker_online || (data.public_tunnel && data.public_tunnel.length > 0);

            const lblPerm = document.getElementById('lbl-permanent-url') || document.getElementById('lbl-local-ip');
            const lblTunnel = document.getElementById('lbl-tunnel-ip');
            const qrImg = document.getElementById('header-qr-img');

            if (lblPerm) {
                lblPerm.innerHTML = `
                    <a href="${permUrl}" target="_blank" style="color: #60a5fa; font-weight: 700; text-decoration: underline;"><i class="fa-solid fa-globe"></i> ${permUrl}</a>
                    <button class="btn-copy-mini" onclick="copyText('${permUrl}', this)" title="Kalıcı Linki Kopyala"><i class="fa-solid fa-copy"></i> Kopyala</button>
                `;
            }
            if (lblTunnel) {
                if (workerOnline) {
                    lblTunnel.innerHTML = `
                        <span style="color: #4ade80; font-weight: 600;"><i class="fa-solid fa-circle-check"></i> PC İndirici Motoru Aktif (Süper Hız & Tek Parça Birleştirme)</span>
                    `;
                } else {
                    lblTunnel.innerHTML = `<span style="color: #94a3b8;"><i class="fa-solid fa-cloud"></i> Bulut Modu Aktif (7/24 Kesintisiz Dizi Tarama)</span>`;
                }
            }
            if (qrImg) {
                qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=${encodeURIComponent(permUrl)}`;
                qrImg.title = `Telefondan Açmak İçin Tara (Kalıcı 7/24 Link)`;
            }
        }
    } catch (e) {
        console.error("IP Fetch error:", e);
    }
}

async function autoSyncTokens() {
    try {
        const res = await fetch(`/indir/api/tokens?t=${Date.now()}`);
        if (res.ok) {
            const data = await res.json();
            const activeToken = data.active_token || (data.tokens && data.tokens.dramaflix ? data.tokens.dramaflix.cookie : '');
            const cookieBox = document.getElementById('user-cookie');
            if (cookieBox && activeToken) {
                if (!cookieBox.value.trim()) {
                    cookieBox.value = activeToken;
                }
            }
            const tokenBadge = document.getElementById('token-sync-badge');
            if (tokenBadge) {
                tokenBadge.innerHTML = `<span style="color: #4ade80; font-size: 11px; font-weight: 600;"><i class="fa-solid fa-circle-check"></i> VIP Tokenler Arka Planda Otomatik Senkronize (Aktif)</span>`;
            }
        }
    } catch (e) {
        console.warn("Token sync notice:", e);
    }
}

function updateSelectedBadge() {
    const selectedCount = document.querySelectorAll('.ep-checkbox-input:checked').length;
    const badge = document.getElementById('selected-count-badge');
    if (badge) badge.innerText = selectedCount;
}

function applyRangeSelection() {
    const input = document.getElementById('range-input').value.trim();
    if (!input) return;

    const parts = input.split('-');
    if (parts.length === 2) {
        const start = parseInt(parts[0].trim(), 10);
        const end = parseInt(parts[1].trim(), 10);
        if (!isNaN(start) && !isNaN(end)) {
            document.querySelectorAll('.episode-item').forEach(item => {
                const epNum = parseInt(item.getAttribute('data-epnum'), 10);
                const chk = item.querySelector('.ep-checkbox-input');
                if (chk) {
                    chk.checked = (epNum >= start && epNum <= end);
                }
            });
            updateSelectedBadge();
        }
    }
}

async function scanSeriesUrl() {
    const url = document.getElementById('series-url').value.trim();
    const btnScan = document.getElementById('btn-scan');
    const errorMsg = document.getElementById('error-msg');
    const mainContent = document.getElementById('main-content');

    if (!url) {
        errorMsg.style.display = 'block';
        errorMsg.innerText = "Lütfen geçerli bir URL veya dizi adı girin.";
        return;
    }

    btnScan.disabled = true;
    btnScan.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Taranıyor...';
    errorMsg.style.display = 'none';
    errorMsg.innerText = "";

    const userCookie = document.getElementById('user-cookie') ? document.getElementById('user-cookie').value.trim() : '';

    try {
        const response = await fetch('/indir/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, cookie: userCookie })
        });

        const data = await response.json();
        
        if (!response.ok || !data.success) {
            errorMsg.style.display = 'block';
            errorMsg.innerText = data.msg || "Taramada hata oluştu.";
            return;
        }

        // Render Series Details
        scannedSeries = data.series || {
            title: data.title,
            slug: data.slug,
            cover_image: data.cover,
            platform: data.platform,
            total_episodes: data.total_episodes
        };
        parsedEpisodes = data.episodes || [];

        document.getElementById('series-title').innerText = scannedSeries.title || "Dizi";
        document.getElementById('series-desc').innerText = scannedSeries.description || `${scannedSeries.title} Türkçe Kısa Dizi`;
        document.getElementById('series-platform').innerText = scannedSeries.platform || "NetShort";
        document.getElementById('series-total-eps').innerText = scannedSeries.total_episodes || parsedEpisodes.length;
        
        const coverEl = document.getElementById('series-cover');
        if (scannedSeries.cover_image) {
            coverEl.style.backgroundImage = `url('${scannedSeries.cover_image}')`;
        } else {
            coverEl.style.backgroundImage = 'none';
        }

        buildEpisodesGrid(parsedEpisodes);
        mainContent.style.display = 'block';

    } catch (err) {
        errorMsg.style.display = 'block';
        errorMsg.innerText = "Sunucuya bağlanılamadı: " + err.message;
    } finally {
        btnScan.disabled = false;
        btnScan.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Diziyi Tara';
    }
}


function buildEpisodesGrid(episodes) {
    const container = document.getElementById('episodes-grid-container');
    container.innerHTML = '';

    // Ensure every episode has a valid episode_number and integer id
    episodes.forEach((ep, idx) => {
        const epNum = parseInt(ep.episode_number || (idx + 1), 10);
        ep.episode_number = epNum;
        ep.id = ep.id !== undefined && ep.id !== null ? ep.id : epNum;
    });

    episodes.sort((a, b) => a.episode_number - b.episode_number);

    episodes.forEach(ep => {
        const epNum = ep.episode_number;
        const item = document.createElement('div');
        item.className = 'episode-item';
        item.setAttribute('data-id', ep.id);
        item.setAttribute('data-epnum', epNum);

        item.innerHTML = `
            <label class="ep-checkbox-label">
                <input type="checkbox" class="ep-checkbox-input" value="${epNum}" data-epnum="${epNum}" data-id="${ep.id}">
                <span class="ep-badge">${epNum}</span>
                <span class="ep-title">Bölüm ${epNum}</span>
                <i class="fa-solid fa-circle-check ep-unlocked" title="Otomatik Çözülmüş & İndirmeye Hazır"></i>
            </label>
        `;

        const chk = item.querySelector('.ep-checkbox-input');
        chk.addEventListener('change', updateSelectedBadge);

        item.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'LABEL') {
                chk.checked = !chk.checked;
                updateSelectedBadge();
            }
        });

        container.appendChild(item);
    });

    updateSelectedBadge();
}

function getSelectedEpisodesList() {
    const checkedInputs = document.querySelectorAll('.ep-checkbox-input:checked');
    if (!checkedInputs.length) return [];

    const selectedNums = [];
    checkedInputs.forEach(chk => {
        const num = parseInt(chk.getAttribute('data-epnum') || chk.value, 10);
        if (!isNaN(num) && num > 0 && !selectedNums.includes(num)) {
            selectedNums.push(num);
        }
    });

    selectedNums.sort((a, b) => a - b);

    const result = selectedNums.map(num => {
        const found = parsedEpisodes.find(e => parseInt(e.episode_number, 10) === num);
        if (found) {
            return {
                ...found,
                episode_number: num,
                id: found.id || num,
                title: found.title || `Bölüm ${num}`
            };
        }
        return {
            episode_number: num,
            id: num,
            title: `Bölüm ${num}`
        };
    });

    return result;
}

async function triggerDownloadQueue() {
    const selectedEpisodes = getSelectedEpisodesList();
    if (!selectedEpisodes.length) {
        alert("Lütfen indirmek için en az bir bölüm seçin.");
        return;
    }

    const btn = document.getElementById('btn-download-selected');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Başlatılıyor...';

    const userCookie = document.getElementById('user-cookie') ? document.getElementById('user-cookie').value.trim() : '';

    try {
        const res = await fetch('/indir/api/download', {
            method: 'POST',
            headers: getClientHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                series_slug: scannedSeries.slug,
                series_title: scannedSeries.title,
                episodes: selectedEpisodes,
                cookie: userCookie,
                client_id: getClientId()
            })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            alert(data.msg || "İndirme başlatılamadı.");
        } else {
            const activeCard = document.getElementById('active-tasks-card');
            if (activeCard) {
                activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
            setTimeout(fetchTaskStatus, 200);
        }
    } catch (e) {
        alert("Bağlantı hatası: " + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-down"></i> Seçilen Bölümleri İndir';
    }
}

async function triggerMergedDownload() {
    const selectedEpisodes = getSelectedEpisodesList();
    if (!selectedEpisodes.length) {
        alert("Lütfen birleştirmek için en az bir bölüm seçin.");
        return;
    }

    const btn = document.getElementById('btn-download-merged');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Başlatılıyor...';

    const userCookie = document.getElementById('user-cookie') ? document.getElementById('user-cookie').value.trim() : '';

    try {
        const res = await fetch('/indir/api/download/merged', {
            method: 'POST',
            headers: getClientHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                series_slug: scannedSeries.slug,
                series_title: scannedSeries.title,
                episodes: selectedEpisodes,
                cookie: userCookie,
                client_id: getClientId()
            })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            alert(data.msg || "Tek part indirme başlatılamadı.");
        } else {
            const activeCard = document.getElementById('active-tasks-card');
            if (activeCard) {
                activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
            setTimeout(fetchTaskStatus, 200);
        }
    } catch (e) {
        alert("Bağlantı hatası: " + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Tek Part Olarak Birleştir';
    }
}


async function fetchTaskStatus() {
    try {
        const res = await fetch(`/indir/api/status?client_id=${encodeURIComponent(getClientId())}&t=${Date.now()}`, {
            headers: getClientHeaders()
        });
        if (res.ok) {
            const tasks = await res.json();
            updateDownloadsDashboard(tasks);
        }
    } catch (e) {
        // Silently ignore network drop
    }
}

function startStatusPolling() {
    if (statusInterval) clearInterval(statusInterval);
    fetchTaskStatus();
    statusInterval = setInterval(fetchTaskStatus, 750);
}

function updateDownloadsDashboard(tasks) {
    const container = document.getElementById('downloads-list-container');
    const taskIds = Object.keys(tasks || {});

    if (taskIds.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-cloud-arrow-down"></i>
                <p>Henüz aktif indirme yok. Bölümleri seçip indirmeyi başlatın.</p>
            </div>
        `;
        return;
    }

    const emptyEl = container.querySelector('.empty-state');
    if (emptyEl) {
        emptyEl.remove();
    }

    const existingItems = {};
    container.querySelectorAll('.download-item').forEach(el => {
        existingItems[el.getAttribute('data-id')] = el;
    });

    taskIds.forEach(id => {
        const task = tasks[id];
        const pct = Math.max(0, Math.min(100, task.progress || 0));
        const statusText = task.status || 'İşleniyor';
        const speedText = task.speed ? `⚡ ${task.speed}` : '';
        const statusSlug = statusText.toLowerCase().replace(/[^a-z0-9]/g, '-');

        let item = existingItems[id];
        if (!item) {
            item = document.createElement('div');
            item.className = 'download-item';
            item.setAttribute('data-id', id);
            container.appendChild(item);
        }

        const isFinished = statusText === 'Tamamlandı';
        const isError = statusText === 'Hata';

        item.innerHTML = `
            <div class="dl-info-row">
                <span class="dl-title">${task.title}</span>
                <span class="status-badge ${statusSlug}">${statusText}</span>
            </div>
            ${!isError ? `
                <div class="progress-bar-outer">
                    <div class="progress-bar-inner" style="width: ${pct}%;"></div>
                </div>
                <div class="dl-meta-row">
                    <span class="dl-speed">${speedText}</span>
                    <span class="dl-pct">%${pct}</span>
                </div>
            ` : `
                <div class="dl-error-text">${task.error || 'İndirme hatası oluştu.'}</div>
            `}
            <div class="dl-actions-row">
                ${isFinished && task.filename ? `
                    <button class="btn-dl-action btn-play" onclick="playVideo('${task.filename.replace(/'/g, "\\'")}')"><i class="fa-solid fa-play"></i> Oynat</button>
                    <a class="btn-dl-action" href="/indir/api/downloads/file/${encodeURIComponent(task.filename)}" download><i class="fa-solid fa-download"></i> İndir</a>
                    <a class="btn-dl-action" href="/indir/api/downloads/file/${encodeURIComponent(task.filename.replace('.mp4', '.srt'))}" download title="Altyazı Dosyası (.srt)"><i class="fa-solid fa-closed-captioning"></i> .SRT</a>
                ` : ''}
                ${!isFinished && !isError ? `
                    <button class="btn-dl-action btn-cancel" onclick="cancelDownload('${id}')"><i class="fa-solid fa-xmark"></i> İptal</button>
                ` : ''}
            </div>
        `;
    });

    Object.keys(existingItems).forEach(id => {
        if (!tasks[id]) existingItems[id].remove();
    });
}

async function cancelDownload(taskId) {
    try {
        await fetch(`/indir/api/download/cancel/${taskId}`, {
            method: 'POST',
            headers: getClientHeaders()
        });
    } catch (e) {
        console.error("Cancel error:", e);
    }
}

// Completed Polling & Management
function startCompletedPolling() {
    if (completedInterval) clearInterval(completedInterval);
    const fetchCompleted = async () => {
        try {
            const res = await fetch(`/indir/api/downloads/list?client_id=${encodeURIComponent(getClientId())}&t=${Date.now()}`, {
                headers: getClientHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                renderCompletedList(data.files || []);
            }
        } catch (e) {
            // Ignore
        }
    };
    fetchCompleted();
    completedInterval = setInterval(fetchCompleted, 2500);
}

function renderCompletedList(files) {
    const container = document.getElementById('completed-list-container');
    if (!container) return;
    if (!files.length) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-film"></i>
                <p>Henüz tamamlanmış indirme yok.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = '';
    files.forEach(f => {
        const item = document.createElement('div');
        item.className = 'completed-item';
        const srtName = f.filename.replace('.mp4', '.srt');
        const safeName = f.filename.replace(/'/g, "\\'");
        item.innerHTML = `
            <div class="completed-left">
                <input type="checkbox" class="completed-select-chk" value="${f.filename}">
                <div>
                    <div class="completed-name">
                        ${f.filename}
                        ${f.has_subtitle ? '<span class="badge-sub-pill" title="Türkçe Altyazı Gömülü & Hazır"><i class="fa-solid fa-closed-captioning"></i> TR Altyazılı</span>' : ''}
                    </div>
                    <div class="completed-size">${f.size_mb ? f.size_mb + ' MB' : ''}</div>
                </div>
            </div>
            <div class="completed-actions">
                <button class="btn-circle" onclick="playVideo('${safeName}')" title="Altyazılı Oynat"><i class="fa-solid fa-play"></i></button>
                <a class="btn-circle btn-download" href="/indir/api/downloads/file/${encodeURIComponent(f.filename)}" download title="Videoyu İndir"><i class="fa-solid fa-download"></i></a>
                ${f.has_subtitle ? `<a class="btn-circle btn-sub" href="/indir/api/downloads/file/${encodeURIComponent(srtName)}" download title="Altyazıyı İndir (.srt)"><i class="fa-solid fa-closed-captioning"></i></a>` : ''}
                <button class="btn-circle btn-delete" onclick="deleteSingleCompletedFile('${safeName}')" title="Sil"><i class="fa-solid fa-trash-can"></i></button>
            </div>
        `;
        container.appendChild(item);
    });
}

function playVideo(filename) {
    const modal = document.getElementById('video-modal');
    const player = document.getElementById('modal-video-player');
    const title = document.getElementById('modal-video-title');

    title.innerHTML = `${filename} <span style="font-size:12px; color: #4ade80; margin-left: 8px; font-weight: normal;"><i class="fa-solid fa-closed-captioning"></i> Türkçe Altyazı Aktif</span>`;
    
    player.pause();
    player.removeAttribute('src');
    while (player.firstChild) {
        player.removeChild(player.firstChild);
    }

    const source = document.createElement('source');
    source.src = `/indir/api/downloads/file/${encodeURIComponent(filename)}`;
    source.type = 'video/mp4';
    player.appendChild(source);

    const track = document.createElement('track');
    track.kind = 'subtitles';
    track.label = 'Türkçe';
    track.srclang = 'tr';
    track.src = `/indir/api/downloads/subtitle/${encodeURIComponent(filename)}?t=${Date.now()}`;
    track.default = true;
    player.appendChild(track);

    player.load();
    modal.style.display = 'flex';

    const enableTrack = () => {
        try {
            if (player.textTracks && player.textTracks.length > 0) {
                for (let i = 0; i < player.textTracks.length; i++) {
                    player.textTracks[i].mode = 'showing';
                }
            }
        } catch (e) {}
    };

    player.onloadedmetadata = enableTrack;
    player.onloadeddata = enableTrack;
    player.onplay = enableTrack;

    player.play().catch(e => console.log('Autoplay prevent:', e));
}

async function deleteSingleCompletedFile(filename) {
    if (!confirm(`${filename} dosyasını silmek istediğinize emin misiniz?`)) return;
    try {
        await fetch('/indir/api/downloads/delete', {
            method: 'POST',
            headers: getClientHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ filenames: [filename] })
        });
        startCompletedPolling();
    } catch (e) {
        alert("Silinemedi: " + e.message);
    }
}

async function deleteSelectedCompletedFiles() {
    const checked = document.querySelectorAll('.completed-select-chk:checked');
    if (!checked.length) {
        alert("Lütfen silmek için en az bir dosya seçin.");
        return;
    }
    const filenames = Array.from(checked).map(c => c.value);
    if (!confirm(`${filenames.length} dosyayı silmek istediğinize emin misiniz?`)) return;

    try {
        await fetch('/indir/api/downloads/delete', {
            method: 'POST',
            headers: getClientHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ filenames: filenames })
        });
        startCompletedPolling();
    } catch (e) {
        alert("Silinemedi: " + e.message);
    }
}

// ---------------- VIRAL VIDEO STUDIO ----------------
function initViralStudio() {
    const fileInput = document.getElementById('viral-file-input');
    const btnGenerate = document.getElementById('btn-generate-viral');
    const btnCancel = document.getElementById('btn-cancel-viral');

    if (fileInput) {
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const help = document.getElementById('upload-status-help');
            if (help) help.innerHTML = `<span style="color: var(--accent-gold);"><i class="fa-solid fa-spinner fa-spin"></i> ${file.name} yükleniyor...</span>`;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/indir/api/viral/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    if (help) help.innerHTML = `<span style="color: #4ade80;"><i class="fa-solid fa-circle-check"></i> ${file.name} yüklendi ve seçildi!</span>`;
                    await refreshViralVideoOptions();
                    const select = document.getElementById('viral-source-video');
                    if (select) select.value = data.filename;
                } else {
                    if (help) help.innerHTML = `<span style="color: #ef4444;"><i class="fa-solid fa-circle-xmark"></i> Yükleme hatası: ${data.msg || 'Bilinmeyen hata'}</span>`;
                }
            } catch (err) {
                if (help) help.innerHTML = `<span style="color: #ef4444;">Yükleme hatası: ${err.message}</span>`;
            }
        });
    }

    if (btnGenerate) {
        btnGenerate.addEventListener('click', async () => {
            const videoSelect = document.getElementById('viral-source-video');
            const videoFilename = videoSelect ? videoSelect.value : '';
            if (!videoFilename) {
                alert("Lütfen işlemek için bir video seçin veya bilgisayarınızdan yükleyin.");
                return;
            }

            const clipMode = document.getElementById('viral-clip-mode').value;
            const bgType = document.getElementById('viral-bg-type').value;
            const burnSubs = document.getElementById('viral-burn-subs').checked;
            const mirror = document.getElementById('viral-mirror').checked;
            const speedup = document.getElementById('viral-speedup').checked;
            const splitRatio = parseInt(document.getElementById('viral-split-ratio').value, 10) || 65;

            btnGenerate.disabled = true;
            btnGenerate.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İşlem Başlatılıyor...';

            try {
                const res = await fetch('/indir/api/viral/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        video_filename: videoFilename,
                        clip_mode: clipMode,
                        bg_type: bgType,
                        burn_subs: burnSubs,
                        mirror: mirror,
                        speedup: speedup,
                        split_ratio: splitRatio
                    })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    currentViralTaskId = data.task_id;
                    startViralPolling(data.task_id);
                } else {
                    alert(data.msg || "Viral video işlemi başlatılamadı.");
                    btnGenerate.disabled = false;
                    btnGenerate.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> 9:16 Dikey Viral Video Üret';
                }
            } catch (e) {
                alert("Bağlantı hatası: " + e.message);
                btnGenerate.disabled = false;
                btnGenerate.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> 9:16 Dikey Viral Video Üret';
            }
        });
    }

    if (btnCancel) {
        btnCancel.addEventListener('click', async () => {
            if (!currentViralTaskId) return;
            try {
                await fetch(`/indir/api/viral/cancel/${currentViralTaskId}`, { method: 'POST' });
            } catch (e) {}
        });
    }
}

async function refreshViralVideoOptions() {
    const select = document.getElementById('viral-source-video');
    if (!select) return;

    try {
        const res = await fetch(`/indir/api/downloads/list?client_id=${encodeURIComponent(getClientId())}&t=${Date.now()}`, {
            headers: getClientHeaders()
        });
        if (res.ok) {
            const data = await res.json();
            const currentVal = select.value;
            select.innerHTML = '<option value="">-- Klip Yapılacak Videoyu Seçin --</option>';
            (data.files || []).forEach(f => {
                const opt = document.createElement('option');
                opt.value = f.filename;
                opt.innerText = `${f.filename} (${f.size_mb ? f.size_mb + ' MB' : ''})`;
                select.appendChild(opt);
            });
            if (currentVal) select.value = currentVal;
        }
    } catch (e) {
        console.error("Refresh viral options error:", e);
    }
}

function startViralPolling(taskId) {
    if (viralPollingInterval) clearInterval(viralPollingInterval);
    const spinner = document.getElementById('viral-spinner');
    const cancelBtn = document.getElementById('btn-cancel-viral');
    const btnGenerate = document.getElementById('btn-generate-viral');

    if (spinner) spinner.style.display = 'inline-block';
    if (cancelBtn) cancelBtn.style.display = 'block';

    viralPollingInterval = setInterval(async () => {
        try {
            const res = await fetch(`/indir/api/viral/status/${taskId}?t=${Date.now()}`);
            if (res.ok) {
                const task = await res.json();
                const statusText = task.status || 'İşleniyor';
                const pct = Math.max(0, Math.min(100, task.progress || 0));

                const txtEl = document.getElementById('viral-status-text');
                const valEl = document.getElementById('viral-progress-val');
                const barEl = document.getElementById('viral-progress-bar');

                if (txtEl) txtEl.innerText = statusText;
                if (valEl) valEl.innerText = `%${pct}`;
                if (barEl) barEl.style.width = `${pct}%`;

                if (task.status === 'Tamamlandı' || task.status === 'Hata' || task.status === 'İptal Edildi') {
                    clearInterval(viralPollingInterval);
                    if (spinner) spinner.style.display = 'none';
                    if (cancelBtn) cancelBtn.style.display = 'none';
                    if (btnGenerate) {
                        btnGenerate.disabled = false;
                        btnGenerate.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> 9:16 Dikey Viral Video Üret';
                    }
                    if (task.status === 'Tamamlandı') {
                        startCompletedPolling();
                    }
                }
            }
        } catch (e) {}
    }, 800);
}

// ---------------- PROMO VIDEO CREATOR ----------------
function initPromoCreator() {
    const btnSync = document.getElementById('btn-sync-covers');
    const btnSelectAll = document.getElementById('btn-select-all-covers');
    const btnDeselectAll = document.getElementById('btn-deselect-all-covers');
    const btnGenerate = document.getElementById('btn-generate-promo');

    if (btnSync) {
        btnSync.addEventListener('click', async () => {
            btnSync.disabled = true;
            btnSync.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Senkronize Ediliyor...';

            try {
                const res = await fetch('/indir/api/promo/sync_covers', { method: 'POST' });
                const data = await res.json();
                if (res.ok && data.success) {
                    pollCoversSync();
                } else {
                    alert(data.msg || "Afiş senkronizasyonu başlatılamadı.");
                    btnSync.disabled = false;
                    btnSync.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Siteden Afişleri Çek';
                }
            } catch (e) {
                alert("Bağlantı hatası: " + e.message);
                btnSync.disabled = false;
                btnSync.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Siteden Afişleri Çek';
            }
        });
    }

    if (btnSelectAll) {
        btnSelectAll.addEventListener('click', () => {
            document.querySelectorAll('.promo-cover-chk').forEach(c => c.checked = true);
        });
    }

    if (btnDeselectAll) {
        btnDeselectAll.addEventListener('click', () => {
            document.querySelectorAll('.promo-cover-chk').forEach(c => c.checked = false);
        });
    }

    if (btnGenerate) {
        btnGenerate.addEventListener('click', async () => {
            const checkedCovers = Array.from(document.querySelectorAll('.promo-cover-chk:checked')).map(c => c.value);
            if (!checkedCovers.length) {
                alert("Lütfen en az bir dizi afişi seçin.");
                return;
            }

            const bgType = document.getElementById('promo-bg-type').value;
            const splitRatio = parseInt(document.getElementById('promo-split-ratio').value, 10) || 65;

            btnGenerate.disabled = true;
            btnGenerate.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Tanıtım Videosu Üretiliyor...';

            try {
                const res = await fetch('/indir/api/promo/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        covers: checkedCovers,
                        bg_type: bgType,
                        split_ratio: splitRatio
                    })
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    currentPromoTaskId = data.task_id;
                    startPromoPolling(data.task_id);
                } else {
                    alert(data.msg || "Tanıtım videosu işlemi başlatılamadı.");
                    btnGenerate.disabled = false;
                    btnGenerate.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Tanıtım Slayt Videosu Üret';
                }
            } catch (e) {
                alert("Bağlantı hatası: " + e.message);
                btnGenerate.disabled = false;
                btnGenerate.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Tanıtım Slayt Videosu Üret';
            }
        });
    }
}

async function loadPromoCovers() {
    const grid = document.getElementById('promo-covers-grid');
    if (!grid) return;

    try {
        const res = await fetch(`/indir/api/promo/covers?t=${Date.now()}`);
        if (res.ok) {
            const data = await res.json();
            const covers = data.covers || [];
            if (!covers.length) {
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--text-secondary); padding: 20px; font-size: 12px;">Henüz afiş bulunmuyor. "Siteden Afişleri Çek" butonuna basın.</div>';
                return;
            }

            grid.innerHTML = '';
            covers.forEach(c => {
                const card = document.createElement('label');
                card.style.cssText = 'display: flex; flex-direction: column; align-items: center; cursor: pointer; background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 6px; padding: 6px; position: relative;';
                card.innerHTML = `
                    <input type="checkbox" class="promo-cover-chk" value="${c.filename}" style="position: absolute; top: 8px; left: 8px; width: 16px; height: 16px; accent-color: var(--accent-red); z-index: 2;">
                    <img src="${c.url}" alt="${c.filename}" style="width: 100%; height: 110px; object-fit: cover; border-radius: 4px; margin-bottom: 6px;">
                    <span style="font-size: 10px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; text-align: center;">${c.filename.replace('.webp', '')}</span>
                `;
                grid.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Load covers error:", e);
    }
}

function pollCoversSync() {
    const btnSync = document.getElementById('btn-sync-covers');
    const syncInterval = setInterval(async () => {
        try {
            const res = await fetch(`/indir/api/promo/status/sync_covers?t=${Date.now()}`);
            if (res.ok) {
                const task = await res.json();
                if (btnSync) btnSync.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${task.status || 'Senkronize ediliyor...'}`;
                if (task.progress >= 100 || (task.status && task.status.includes('Başarıyla'))) {
                    clearInterval(syncInterval);
                    if (btnSync) {
                        btnSync.disabled = false;
                        btnSync.innerHTML = '<i class="fa-solid fa-circle-check text-green"></i> Afişler Güncellendi';
                        setTimeout(() => {
                            btnSync.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Siteden Afişleri Çek';
                        }, 3000);
                    }
                    loadPromoCovers();
                }
            }
        } catch (e) {}
    }, 1000);
}

function startPromoPolling(taskId) {
    if (promoPollingInterval) clearInterval(promoPollingInterval);
    const spinner = document.getElementById('promo-spinner');
    const btnGenerate = document.getElementById('btn-generate-promo');

    if (spinner) spinner.style.display = 'inline-block';

    promoPollingInterval = setInterval(async () => {
        try {
            const res = await fetch(`/indir/api/promo/status/${taskId}?t=${Date.now()}`);
            if (res.ok) {
                const task = await res.json();
                const statusText = task.status || 'İşleniyor';
                const pct = Math.max(0, Math.min(100, task.progress || 0));

                const txtEl = document.getElementById('promo-status-text');
                const valEl = document.getElementById('promo-progress-val');
                const barEl = document.getElementById('promo-progress-bar');

                if (txtEl) txtEl.innerText = statusText;
                if (valEl) valEl.innerText = `%${pct}`;
                if (barEl) barEl.style.width = `${pct}%`;

                if (task.status === 'Tamamlandı' || task.status === 'Hata') {
                    clearInterval(promoPollingInterval);
                    if (spinner) spinner.style.display = 'none';
                    if (btnGenerate) {
                        btnGenerate.disabled = false;
                        btnGenerate.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Tanıtım Slayt Videosu Üret';
                    }
                    if (task.status === 'Tamamlandı') {
                        startCompletedPolling();
                    }
                }
            }
        } catch (e) {}
    }, 800);
}
