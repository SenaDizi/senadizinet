const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const cron = require('node-cron');
const { exec } = require('child_process');

const app = express();
const PORT = process.env.PORT || 8080;
const CRON_SECRET = process.env.CRON_SECRET || 'SENADIZI_SECRET';

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 1. ÖNCELİKLİ ADMİN VE SAYFA ROTALARI (TOP-PRIORITY DIRECT ROUTES)
app.get(['/admin', '/admin.html'], (req, res) => {
  const adminFile = path.resolve(__dirname, 'admin.html');
  if (fs.existsSync(adminFile)) {
    return res.sendFile(adminFile);
  }
  res.status(404).send('admin.html dosyası bulunamadı');
});

app.get(['/dmca', '/dmca.html'], (req, res) => {
  res.sendFile(path.resolve(__dirname, 'dmca.html'));
});

app.get(['/diziler', '/diziler.html'], (req, res) => {
  res.sendFile(path.resolve(__dirname, 'diziler.html'));
});

app.get(['/dizi-detay', '/dizi-detay.html'], (req, res) => {
  res.sendFile(path.resolve(__dirname, 'dizi-detay.html'));
});

app.get(['/izle', '/izle.html'], (req, res) => {
  res.sendFile(path.resolve(__dirname, 'izle.html'));
});

app.get(['/abonelik', '/abonelik.html'], (req, res) => {
  res.sendFile(path.resolve(__dirname, 'abonelik.html'));
});

app.get(['/giris', '/giris.html'], (req, res) => {
  res.sendFile(path.resolve(__dirname, 'giris.html'));
});

app.get(['/kayit', '/kayit.html'], (req, res) => {
  res.sendFile(path.resolve(__dirname, 'kayit.html'));
});

// 2. CANLI DİZİ LİSTESİ REST API (/api/diziler)
app.get('/api/diziler', (req, res) => {
  const jsonPath = path.resolve(__dirname, 'diziler.json');
  if (fs.existsSync(jsonPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
      return res.json({ success: true, data });
    } catch (e) {
      return res.status(500).json({ success: false, error: 'diziler.json parse hatası' });
    }
  }
  res.status(404).json({ success: false, error: 'diziler.json bulunamadı' });
});

// Bot Çalıştırıcı Fonksiyon
function triggerDramaBot() {
  return new Promise((resolve) => {
    console.log(`[${new Date().toISOString()}] [CRON/BOT] Otomatik Asya dizi çekimi başlatılıyor...`);
    exec('python cron_bot.py', { cwd: __dirname }, (error, stdout, stderr) => {
      if (error) {
        console.error('[CRON/BOT HATA]:', stderr || error.message);
        return resolve({ success: false, error: error.message, output: stderr });
      }
      console.log('[CRON/BOT TAMAMLANDI]:', stdout.trim());
      resolve({ success: true, message: 'Diziler ve embed kaynaklar başarıyla güncellendi.', output: stdout.trim() });
    });
  });
}

// 3. GÜVENLİ CRON / WEBHOOK ENDPOINT'LERİ (/api/cron/update-dramas ve /api/cron)
app.all(['/api/cron/update-dramas', '/api/cron'], async (req, res) => {
  const key = req.query.key || req.query.token || req.headers['x-cron-key'];
  if (key !== CRON_SECRET && key !== 'sena_secret_cron_token_2026') {
    return res.status(401).json({
      success: false,
      error: 'Geçersiz gizli anahtar! (?key=SENADIZI_SECRET kullanınız)'
    });
  }

  const result = await triggerDramaBot();
  res.json({
    success: result.success,
    timestamp: new Date().toISOString(),
    details: result
  });
});

// 4. DAHİLİ SAATLİK CRON (node-cron)
cron.schedule('0 * * * *', async () => {
  console.log('[NODE-CRON] Saatlik otomatik Asya dizi güncellemesi tetiklendi.');
  await triggerDramaBot();
});

// 5. STATİK DOSYALARI SUNMA (ASSETS & KÖK DİZİN)
app.use('/assets', express.static(path.resolve(__dirname, 'assets')));
app.use(express.static(path.resolve(__dirname)));

// 6. SPA / YEDEK ROTA
app.get('*', (req, res) => {
  const requestedFile = req.path.replace(/^\//, '');
  const directPath = path.resolve(__dirname, requestedFile);
  const htmlPath = path.resolve(__dirname, `${requestedFile}.html`);

  if (requestedFile && fs.existsSync(directPath) && fs.statSync(directPath).isFile()) {
    return res.sendFile(directPath);
  }
  if (requestedFile && fs.existsSync(htmlPath)) {
    return res.sendFile(htmlPath);
  }
  res.sendFile(path.resolve(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`SedaDizi Sunucusu Yayında: http://localhost:${PORT}`);
  console.log(`Admin Paneli: http://localhost:${PORT}/admin.html`);
  console.log(`Webhook API: http://localhost:${PORT}/api/cron/update-dramas?key=${CRON_SECRET}`);
  console.log(`====================================================`);
});
