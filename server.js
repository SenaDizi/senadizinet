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

// 1. Canlı Dizi Verisi REST API
app.get('/api/diziler', (req, res) => {
  const jsonPath = path.join(__dirname, 'diziler.json');
  if (fs.existsSync(jsonPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
      return res.json({ success: true, data });
    } catch (e) {
      return res.status(500).json({ success: false, error: 'JSON okuma hatası' });
    }
  }
  res.status(404).json({ success: false, error: 'diziler.json bulunamadı' });
});

// Bot Çalıştırma Fonksiyonu
function triggerDramaBot() {
  return new Promise((resolve) => {
    console.log(`[${new Date().toISOString()}] [CRON/BOT] Otomatik Asya dizi çekimi başlatılıyor...`);
    exec('python cron_bot.py', { cwd: __dirname }, (error, stdout, stderr) => {
      if (error) {
        console.error('[CRON/BOT HATA]:', stderr || error.message);
        return resolve({ success: false, error: error.message, output: stderr });
      }
      console.log('[CRON/BOT TAMAMLANDI]:', stdout.trim());
      resolve({ success: true, message: 'Diziler ve embed kaynaklar güncellendi.', output: stdout.trim() });
    });
  });
}

// 2. Güvenli Webhook / Cron Tetikleyici Endpoint'i
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

// 3. Dahili Saatlik node-cron
cron.schedule('0 * * * *', async () => {
  console.log('[NODE-CRON] Saatlik otomatik Asya dizi güncellemesi tetiklendi.');
  await triggerDramaBot();
});

// 4. Doğrudan HTML Sayfa Yönlendirmeleri (404 Önleme)
app.get('/admin.html', (req, res) => res.sendFile(path.join(__dirname, 'admin.html')));
app.get('/admin', (req, res) => res.sendFile(path.join(__dirname, 'admin.html')));
app.get('/dmca.html', (req, res) => res.sendFile(path.join(__dirname, 'dmca.html')));
app.get('/dmca', (req, res) => res.sendFile(path.join(__dirname, 'dmca.html')));
app.get('/diziler.html', (req, res) => res.sendFile(path.join(__dirname, 'diziler.html')));
app.get('/dizi-detay.html', (req, res) => res.sendFile(path.join(__dirname, 'dizi-detay.html')));
app.get('/izle.html', (req, res) => res.sendFile(path.join(__dirname, 'izle.html')));
app.get('/abonelik.html', (req, res) => res.sendFile(path.join(__dirname, 'abonelik.html')));
app.get('/giris.html', (req, res) => res.sendFile(path.join(__dirname, 'giris.html')));
app.get('/kayit.html', (req, res) => res.sendFile(path.join(__dirname, 'kayit.html')));

// 5. Statik Dosyalar
app.use(express.static(path.join(__dirname)));

// 6. SPA Fallback
app.get('*', (req, res) => {
  const reqPath = req.path.replace(/^\//, '');
  const directFile = path.join(__dirname, reqPath);
  const htmlFile = path.join(__dirname, `${reqPath}.html`);

  if (reqPath && fs.existsSync(directFile) && fs.statSync(directFile).isFile()) {
    return res.sendFile(directFile);
  }
  if (reqPath && fs.existsSync(htmlFile)) {
    return res.sendFile(htmlFile);
  }
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`SedaDizi Sunucusu Yayında: http://localhost:${PORT}`);
  console.log(`Admin Paneli: http://localhost:${PORT}/admin.html`);
  console.log(`Webhook API: http://localhost:${PORT}/api/cron/update-dramas?key=${CRON_SECRET}`);
});
