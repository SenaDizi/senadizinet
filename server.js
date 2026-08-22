/**
 * SenaDiziNet - Web Sunucusu, API ve node-cron Otomasyon Modülü
 */

const path = require('path');
const fs = require('fs');
const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const { scrapeDiziler } = require('./scraper');

const app = express();
const PORT = process.env.PORT || 8080;
const CRON_SECRET = process.env.CRON_SECRET || 'sena_secret_cron_token_2026';

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Statik Dosyalar (HTML, CSS, JS, Assets)
app.use(express.static(__dirname));

/**
 * 1. API: Güncel Dizi Listesini Getir
 */
app.get('/api/diziler', (req, res) => {
  const jsonPath = path.join(__dirname, 'diziler.json');
  if (fs.existsSync(jsonPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
      return res.json(data);
    } catch (err) {
      return res.status(500).json({ error: 'Veri dosyası okunamadı.' });
    }
  }
  return res.status(404).json({ error: 'diziler.json bulunamadı.' });
});

/**
 * 2. API / Harici Cron Endpoint: /api/cron/update-diziler
 * Harici cron servisleri (Render Cron, cron-job.org vb.) için tetikleyici
 */
app.all('/api/cron/update-diziler', async (req, res) => {
  const token = req.query.token || req.headers['x-cron-secret'] || (req.body && req.body.token);

  // Güvenlik doğrulaması (Opsiyonel: Eğer secret tanımlıysa kontrol et)
  if (CRON_SECRET && token && token !== CRON_SECRET) {
    return res.status(401).json({ status: 'error', message: 'Yetkisiz erişim: Geçersiz token.' });
  }

  try {
    console.log('[API CRON] Manuel/Harici dizi güncelleme tetiklendi.');
    const result = await scrapeDiziler();
    return res.json({
      status: 'success',
      message: 'Diziler başarıyla güncellendi.',
      updated_at: result.last_updated,
      total_series: result.total_series
    });
  } catch (err) {
    return res.status(500).json({
      status: 'error',
      message: 'Scraping sırasında hata oluştu.',
      detail: err.message
    });
  }
});

/**
 * 3. Otomatik Dahili Cron Job: node-cron ile Her Saat Başı Çalışır
 * Cron İfadesi: '0 * * * *' (Her saatin 0. dakikasında)
 */
cron.schedule('0 * * * *', async () => {
  console.log(`[NODE-CRON] [${new Date().toISOString()}] Saatlik otomatik dizi çekme görevi başladı.`);
  try {
    await scrapeDiziler();
    console.log(`[NODE-CRON] Saatlik otomatik güncelleme başarıyla tamamlandı.`);
  } catch (err) {
    console.error(`[NODE-CRON HATA] Otomatik güncelleme başarısız:`, err.message);
  }
});

// SPA / Sayfa Yönlendirmeleri
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Sunucuyu Başlat
app.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`🎬 SenaDiziNet Sunucusu Yayında: http://localhost:${PORT}`);
  console.log(`⏰ node-cron Altyapısı: Aktif (Her saat başı otomatik çalışır)`);
  console.log(`🔗 Cron Tetikleme URL: http://localhost:${PORT}/api/cron/update-diziler?token=${CRON_SECRET}`);
  console.log(`====================================================`);
});
