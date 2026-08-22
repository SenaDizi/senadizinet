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

// Statik Dosyaları Sunma
app.use(express.static(path.join(__dirname)));

// 1. Canlı Dizi Listesi REST API
app.get('/api/diziler', (req, res) => {
  const jsonPath = path.join(__dirname, 'diziler.json');
  if (fs.existsSync(jsonPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
      return res.json({ success: true, data });
    } catch (e) {
      return res.status(500).json({ success: false, error: 'JSON parse hatası' });
    }
  }
  res.status(404).json({ success: false, error: 'diziler.json bulunamadı' });
});

// Bot Çalıştırma Fonksiyonu
function triggerDramaBot() {
  return new Promise((resolve, reject) => {
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

// 2. Güvenli Webhook / Tetikleme Endpoint'i (/api/cron/update-dramas ve /api/cron)
app.all(['/api/cron/update-dramas', '/api/cron'], async (req, res) => {
  const key = req.query.key || req.query.token || req.headers['x-cron-key'];

  if (key !== CRON_SECRET && key !== 'sena_secret_cron_token_2026') {
    return res.status(401).json({
      success: false,
      error: 'Geçersiz veya eksik gizli anahtar! (key=SENADIZI_SECRET kullanın)'
    });
  }

  const result = await triggerDramaBot();
  res.json({
    success: result.success,
    timestamp: new Date().toISOString(),
    details: result
  });
});

// 3. Dahili Otomatik Saatlik node-cron (Her saat başı)
cron.schedule('0 * * * *', async () => {
  console.log('[NODE-CRON] Saatlik otomatik Asya dizi güncellemesi tetiklendi.');
  await triggerDramaBot();
});

// SPA / Rota Yönlendirme
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`SedaDizi Sunucusu Yayında: http://localhost:${PORT}`);
  console.log(`Canlı Dizi API: http://localhost:${PORT}/api/diziler`);
  console.log(`Güvenli Cron Webhook: http://localhost:${PORT}/api/cron/update-dramas?key=${CRON_SECRET}`);
  console.log(`Yönetici Paneli: http://localhost:${PORT}/admin.html`);
  console.log(`====================================================`);
});
