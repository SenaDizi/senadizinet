/**
 * SenaDizi – Admin Paneli JS Motoru
 */

// Dizi Silme
async function deleteSeries(id, title) {
  if (!confirm(`'${title}' dizisini ve bu diziye ait tüm sezon ve bölümleri silmek istediğinize emin misiniz?`)) {
    return;
  }
  try {
    const res = await fetch(`/api/admin/series/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(data.detail || 'Silme işlemi başarısız.', 'error');
    }
  } catch (err) {
    showToast('Hata oluştu.', 'error');
  }
}

// Bölüm Silme
async function deleteEpisode(id, title) {
  if (!confirm(`'${title}' bölümünü silmek istediğinize emin misiniz?`)) {
    return;
  }
  try {
    const res = await fetch(`/api/admin/episodes/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(data.detail || 'Silme işlemi başarısız.', 'error');
    }
  } catch (err) {
    showToast('Hata oluştu.', 'error');
  }
}

// Kategori Silme
async function deleteCategory(id, name) {
  if (!confirm(`'${name}' kategorisini silmek istediğinize emin misiniz?`)) return;
  try {
    const res = await fetch(`/api/admin/categories/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(data.detail || 'Hata oluştu.', 'error');
    }
  } catch (err) {
    showToast('Hata oluştu.', 'error');
  }
}

// Kullanıcı Durumunu Değiştir (Aktif/Pasif)
async function toggleUserStatus(userId) {
  try {
    const res = await fetch(`/api/admin/users/${userId}/toggle-status`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      setTimeout(() => window.location.reload(), 600);
    } else {
      showToast(data.detail || 'İşlem başarısız.', 'error');
    }
  } catch (err) {
    showToast('Hata oluştu.', 'error');
  }
}

// Modal Kontrolleri
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('hidden');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('hidden');
}
