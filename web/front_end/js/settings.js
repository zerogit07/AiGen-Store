async function loadSettingsPage(tab) {
    if (tab === 'banner') await renderBannerSettings();
    else if (tab === 'qris') await renderQrisSettings();
    else if (tab === 'autodelete') await renderAutoDeleteSettings();
    else if (tab === 'manualdelete') await renderManualDelete();
}

async function renderBannerSettings() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        let html = '<div class="card"><div class="card-row"><span class="card-label">Status</span><span class="card-value">' + (data.banner ? '✅ Ada' : '❌ Belum diatur') + '</span></div></div>';
        html += '<div class="card-actions"><input type="file" id="bannerFile" accept="image/*" style="display:none;">';
        html += '<button class="btn btn-primary" onclick="document.getElementById(\'bannerFile\').click()">🔄 Upload Or Ganti</button>';
        html += '<button class="btn btn-outline" onclick="deleteBanner()">🗑️ Hapus</button></div>';
        content.innerHTML = html;

        document.getElementById('bannerFile').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/api/settings/banner', { method: 'POST', body: formData });
            const result = await res.json();
            showToast(result.message, result.success ? 'success' : 'error');
            if (result.success) renderBannerSettings();
        });
    } catch (e) {
        content.innerHTML = '<div class="placeholder"><p>❌ Gagal memuat.</p></div>';
    }
}

async function deleteBanner() {
    const res = await fetch('/api/settings/banner', { method: 'DELETE' });
    const data = await res.json();
    showToast(data.message, data.success ? 'success' : 'error');
    if (data.success) renderBannerSettings();
}

async function renderQrisSettings() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        let html = '<div class="card"><div class="card-row"><span class="card-label">Status</span><span class="card-value">' + (data.qris ? '✅ Ada' : '❌ Belum diatur') + '</span></div></div>';
        html += '<div class="card-actions"><input type="file" id="qrisFile" accept="image/*" style="display:none;">';
        html += '<button class="btn btn-primary" onclick="document.getElementById(\'qrisFile\').click()">🔄 Upload Or Ganti</button>';
        html += '<button class="btn btn-outline" onclick="deleteQris()">🗑️ Hapus</button></div>';
        content.innerHTML = html;

        document.getElementById('qrisFile').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/api/settings/qris', { method: 'POST', body: formData });
            const result = await res.json();
            showToast(result.message, result.success ? 'success' : 'error');
            if (result.success) renderQrisSettings();
        });
    } catch (e) {
        content.innerHTML = '<div class="placeholder"><p>❌ Gagal memuat.</p></div>';
    }
}

async function deleteQris() {
    const res = await fetch('/api/settings/qris', { method: 'DELETE' });
    const data = await res.json();
    showToast(data.message, data.success ? 'success' : 'error');
    if (data.success) renderQrisSettings();
}

async function renderAutoDeleteSettings() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        let html = '<div class="card"><div class="card-row"><span class="card-label">Hari</span><span class="card-value">' + data.auto_delete_days + '</span></div></div>';
        html += '<div class="form-group"><label>Jumlah Hari (0 = nonaktif)</label><input type="number" id="autoDeleteDays" class="form-input" value="' + data.auto_delete_days + '" min="0"></div>';
        html += '<div class="card-actions"><button class="btn btn-primary" onclick="updateAutoDelete()">💾 Simpan</button></div>';
        content.innerHTML = html;
    } catch (e) {
        content.innerHTML = '<div class="placeholder"><p>❌ Gagal memuat.</p></div>';
    }
}

async function updateAutoDelete() {
    const days = document.getElementById('autoDeleteDays').value;
    const formData = new FormData();
    formData.append('days', days);
    const res = await fetch('/api/settings/auto-delete', { method: 'POST', body: formData });
    const data = await res.json();
    showToast(data.message, data.success ? 'success' : 'error');
    if (data.success) renderAutoDeleteSettings();
}

async function renderManualDelete() {
    try {
        const res = await fetch('/api/settings/manual-delete/count');
        const data = await res.json();
        const count = data.count || 0;

        let html = '';

        if (count > 0) {
            html += `
                <div class="card">
                    <div class="card-row">
                        <span class="card-label">Item Terpakai</span>
                        <span class="card-value">${count}</span>
                    </div>
                </div>

                <div class="manual-delete-wrap">
                    <button
                        class="manual-delete-btn"
                        onclick="manualDelete()">
                        🗑️ Hapus Semua Item terpakai
                    </button>
                </div>
            `;
        } else {
            html += `
                <div class="manual-delete-empty">
                    Tidak ada item terpakai saat ini. ✅
                </div>
            `;
        }

        html += `
            <div id="manualDeleteResult"
                 style="margin-top:12px;">
            </div>
        `;

        content.innerHTML = html;

    } catch (e) {
        content.innerHTML =
            '<div class="placeholder"><p>❌ Gagal memuat.</p></div>';
    }
}
async function manualDelete() {
    window.showConfirmModal(
        'Yakin hapus semua item terpakai?',
        async () => {
            const res = await fetch('/api/settings/manual-delete', { method: 'POST' });
            const data = await res.json();
            showToast(data.message, data.success ? 'success' : 'error');
            if (data.success) {
                document.getElementById('manualDeleteResult').innerHTML = '<p>✅ ' + data.message + '</p>';
                const countRes = await fetch('/api/settings/manual-delete/count');
                const countData = await countRes.json();
                if (countData.count === 0) {
                    content.innerHTML = '<p>Tidak ada item terpakai saat ini. ✅</p>';
                }
            }
        }
    );
}


// Di renderBannerSettings, cari:
'<button class="btn btn-primary" onclick="document.getElementById(\'bannerFile\').click()">📤 Upload</button>'
// Ganti menjadi:

// Di renderQrisSettings, lakukan hal yang sama:
