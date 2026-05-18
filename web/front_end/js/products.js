// @ts-nocheck
// products.js - AiGen Store Dashboard
(function () {
    let currentProductPage = 1;
    let currentSubId = null;
    const itemsPerPage = 10;

    // ── Entry point ──
    window.loadProductsPage = async function (tab) {
        if (tab === 'kategori') await renderCategories(1);
        else if (tab === 'subkategori') await renderSubcategorySelector(1);
        else if (tab === 'item') await renderItemSelector(1);
        else if (tab === 'data') await window.loadDataTab();
    };

    // ═══════════════ RINGKASAN GRID ═══════════════
    async function fetchSummary(tab, params = '') {
        const res = await fetch(`/api/products/summary?tab=${tab}${params}`);
        return await res.json();
    }

    function renderSummaryGrid(summary, tab) {
        let items = [];
        if (tab === 'kategori') {
            items = [
                { label: 'Total', value: summary.total, sub: 'Kategori' },
                { label: 'Terisi', value: summary.terisi, sub: 'Kategori' },
                { label: 'Kosong', value: summary.kosong, sub: 'Kategori' }
            ];
        } else if (tab === 'subkategori') {
            items = [
                { label: 'Total', value: summary.total, sub: 'Subkategori' },
                { label: 'Terisi', value: summary.terisi, sub: 'Subkategori' },
                { label: 'Kosong', value: summary.kosong, sub: 'Subkategori' }
            ];
        } else if (tab === 'item') {
            items = [
                { label: 'Total', value: summary.total, sub: 'Item' },
                { label: 'Tersedia', value: summary.tersedia, sub: 'Item' },
                { label: 'Terpakai', value: summary.terpakai, sub: 'Item' }
            ];
        }
        return `
            <div class="summary-grid">
                ${items.map(i => `
                    <div class="summary-card">
                        <div class="summary-label">
                            ${i.sub}<br>${i.label}
                        </div>
                        <div class="summary-value">${i.value}</div>
                    </div>
                `).join('')}
            </div>`;
    }

    // ═══════════════ KATEGORI ═══════════════
    async function renderCategories(page) {
        currentProductPage = page;
        try {
            const [catRes, sumData] = await Promise.all([
                fetch(`/api/products/categories?page=${page}&limit=${itemsPerPage}`).then(r => r.json()),
                fetchSummary('kategori')
            ]);
            let html = renderSummaryGrid(sumData, 'kategori');
            html += '<button class="btn btn-primary btn-full" onclick="window.showCategoryModal()">➕ Tambah Kategori</button>';
            html += '<div id="catList">';
            const start = (page - 1) * itemsPerPage;

            catRes.data.forEach((c, index) => {
                html += `
                    <div class="list-row">
                        <span class="list-row-label">
                            ${start + index + 1}. ${c.name}
                        </span>
                        <div class="list-row-actions">
                            <button class="btn-icon" onclick="window.editCategory(${c.id}, '${c.name}')">✏️</button>
                            <button class="btn-icon" onclick="window.deleteCategory(${c.id})">🗑️</button>
                        </div>
                    </div>`;
            });
            html += '</div>';
            html += paginationControls(page, catRes.total, 'renderCategories');
            content.innerHTML = html;
        } catch (e) {
            content.innerHTML = '<div class="placeholder"><p>❌ Gagal memuat kategori.</p></div>';
        }
    }

    window.renderCategories = renderCategories;

    function setupKeyboardAware(modalElement) {
        const inputs = modalElement.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                setTimeout(() => {
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            });
        });
    }

    window.showCategoryModal = function (id = null, oldName = '') {
        const title = id ? 'Edit Kategori' : 'Tambah Kategori';
        const action = id ? `window.updateCategory(${id})` : 'window.createCategory()';
        const html = `
            <div class="modal-overlay show" id="modalOverlay">
                <div class="modal">
                    <div class="form-wrapper" style="overflow-y:auto; flex: 1;">
                        <p>${title}</p>
                        <div class="form-group">
                            <input type="text" id="modalInput" class="form-input" value="${oldName}" placeholder="Nama kategori">
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-primary" onclick="${action}">Simpan</button>
                        <button class="btn btn-outline" onclick="window.closeModal()">Batal</button>
                    </div>
                </div>
            </div>`;
        document.body.insertAdjacentHTML('beforeend', html);
        setupKeyboardAware(document.getElementById('modalOverlay'));
    };

    window.closeModal = function () {
        const overlay = document.getElementById('modalOverlay');
        if (overlay) overlay.remove();
    };

    window.createCategory = async function () {
        const name = document.getElementById('modalInput').value.trim();
        if (!name) return showToast('Nama tidak boleh kosong.', 'error');
        const formData = new FormData();
        formData.append('name', name);
        console.log("[CRUD DEBUG] Creating category", { name });
        const res = await fetch('/api/products/categories', { method: 'POST', body: formData });
        const data = await res.json();
        console.log("[CRUD DEBUG] Create response", data);
        showToast(data.message, data.success ? 'success' : 'error');
        closeModal();
        if (data.success) window.renderCategories(currentProductPage);
    };

    window.updateCategory = async function (id) {
        const name = document.getElementById('modalInput').value.trim();
        if (!name) return showToast('Nama tidak boleh kosong.', 'error');
        const formData = new FormData();
        formData.append('name', name);
        console.log("[CRUD DEBUG] Updating category", { id, name });
        const res = await fetch(`/api/products/categories/${id}`, { method: 'PUT', body: formData });
        const data = await res.json();
        console.log("[CRUD DEBUG] Update response", data);
        showToast(data.message, data.success ? 'success' : 'error');
        closeModal();
        if (data.success) window.renderCategories(currentProductPage);
    };

    window.deleteCategory = function (id) {
        window.showConfirmModal(
            'Yakin hapus kategori ini? Semua subkategori dan item akan ikut terhapus.',
            async () => {
                console.log("[CRUD DEBUG] Deleting category", { id });
                const res = await fetch(`/api/products/categories/${id}`, { method: 'DELETE' });
                const data = await res.json();
                console.log("[CRUD DEBUG] Delete response", data);
                showToast(data.message, data.success ? 'success' : 'error');
                if (data.success) window.renderCategories(currentProductPage);
            }
        );
    };

    // ═══════════════ SUBKATEGORI ═══════════════
    window.renderSubcategorySelector = async function (page = 1, selectedCatId = null) {
        currentProductPage = page;
        const catsRes = await fetch('/api/products/categories?limit=100');
        const cats = await catsRes.json();
        
        let selectHtml = `<select id="catSelect" class="form-select" onchange="
            const catId = this.value;
            console.log('Category selected:', catId);
            document.getElementById('catLabel').textContent = this.options[this.selectedIndex].text;
            if(catId) window.renderSubcategories(catId, 1);
            else document.getElementById('subList').innerHTML = '';
        " style="display:none;">`;
        selectHtml += '<option value="">-- Pilih --</option>';
        cats.data.forEach(c => {
            selectHtml += `<option value="${c.id}" ${selectedCatId == c.id ? 'selected' : ''}>${c.name}</option>`;
        });
        selectHtml += '</select>';
        
        const currentCat = cats.data.find(c => c.id == selectedCatId);
        const label = currentCat ? currentCat.name : '-- Pilih Kategori --';

        let html = `
        <div class="form-group" onclick="window.showSearchableDropdown(document.getElementById('catSelect'))">
            <label>Pilih Kategori</label>
            <div class="form-input" style="cursor:pointer;" id="catLabel">${label}</div>
            ${selectHtml}
        </div>
        <div id="subList"></div>`;
        content.innerHTML = html;
        if (selectedCatId) await window.renderSubcategories(selectedCatId, page);
    };

    window.renderSubcategories = async function(catId, page) {
        console.log(`[DEBUG] Rendering subcategories for catId: ${catId}, page: ${page}`);
        
        const subList = document.getElementById('subList');
        if (subList) {
            subList.innerHTML = '<div class="placeholder"><p>⏳ Memuat data...</p></div>';
        }

        try {
            const response = await fetch(`/api/products/subcategories?category_id=${catId}&page=${page}&limit=${itemsPerPage}`);
            
            if (response.status === 401) {
                showToast('Sesi habis, silakan login ulang.', 'error');
                console.error('[AUTH ERROR] Unauthorized access.');
                return;
            }

            const subRes = await response.json();
            const sumData = await fetchSummary('subkategori', `&category_id=${catId}`);
            
            console.log('[DEBUG] API Response:', subRes);
            
            if (!subList) return;
            
            let html = renderSummaryGrid(sumData, 'subkategori');
            html += `<button class="btn btn-primary btn-full" onclick="window.showSubcategoryModal(${catId})">➕ Tambah Subkategori</button>`;
            
            if (!subRes.data || subRes.data.length === 0) {
                html += '<div class="placeholder"><p>📭 Belum ada subkategori.</p></div>';
            } else {
                html += '<div id="subListContent">';
                const start = (page - 1) * itemsPerPage;

                subRes.data.forEach((s, index) => {
                    html += `
                        <div class="list-row">
                            <span class="list-row-label">
                                ${start + index + 1}. ${s.name} (Rp${s.price})
                            </span>
                            <div class="list-row-actions">
                                <button class="btn-icon" onclick="window.editSubcategory(${s.id}, ${catId}, '${s.name}', ${s.price_raw})">✏️</button>
                                <button class="btn-icon" onclick="window.deleteSubcategory(${s.id})">🗑️</button>
                            </div>
                        </div>`;
                });
                html += '</div>';
                html += paginationControls(page, subRes.total, `window.renderSubcategoriesPage`);
            }
            
            window.renderSubcategoriesPage = function (p) { window.renderSubcategories(catId, p); };
            subList.innerHTML = html;
        } catch (e) {
            console.error('[ERROR] Error rendering subcategories:', e);
            if (subList) {
                subList.innerHTML = '<div class="placeholder"><p>❌ Gagal memuat subkategori.</p></div>';
            }
        }
    };

    window.showSubcategoryModal = function (catId, subId = null, oldName = '', oldPrice = '') {
        const title = subId ? 'Edit Subkategori' : 'Tambah Subkategori';
        const action = subId ? `window.updateSubcategory(${subId})` : `window.createSubcategory(${catId})`;
        const html = `
            <div class="modal-overlay show" id="modalOverlay">
                <div class="modal">
                    <div class="form-wrapper" style="overflow-y:auto; flex: 1;">
                        <p>${title}</p>
                        <div class="form-group">
                            <input type="text" id="modalName" class="form-input" value="${oldName}" placeholder="Nama">
                        </div>
                        <div class="form-group">
                            <input type="number" id="modalPrice" class="form-input" value="${oldPrice}" placeholder="Harga">
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-primary" onclick="${action}">Simpan</button>
                        <button class="btn btn-outline" onclick="window.closeModal()">Batal</button>
                    </div>
                </div>
            </div>`;
        document.body.insertAdjacentHTML('beforeend', html);
        setupKeyboardAware(document.getElementById('modalOverlay'));
    };

    window.createSubcategory = async function (catId) {
        const name = document.getElementById('modalName').value.trim();
        const price = document.getElementById('modalPrice').value.trim();
        if (!name || !price) return showToast('Semua kolom harus diisi.', 'error');
        const formData = new FormData();
        formData.append('category_id', catId);
        formData.append('name', name);
        formData.append('price', price);
        
        console.log("[CRUD DEBUG] Creating subcategory", { catId, name, price });
        const res = await fetch('/api/products/subcategories', { method: 'POST', body: formData });
        const data = await res.json();
        
        console.log("[CRUD DEBUG] Create response", data);
        showToast(data.message, data.success ? 'success' : 'error');
        closeModal();
        if (data.success) window.renderSubcategories(catId, currentProductPage);
    };

    window.updateSubcategory = async function (subId) {
        const name = document.getElementById('modalName').value.trim();
        const price = document.getElementById('modalPrice').value.trim();
        if (!name || !price) return showToast('Semua kolom harus diisi.', 'error');
        const formData = new FormData();
        formData.append('name', name);
        formData.append('price', price);
        const res = await fetch(`/api/products/subcategories/${subId}`, { method: 'PUT', body: formData });
        const data = await res.json();
        showToast(data.message, data.success ? 'success' : 'error');
        closeModal();
        if (data.success) {
            const catId = document.getElementById('catSelect').value;
            renderSubcategories(catId, currentProductPage);
        }
    };

    window.editSubcategory = function (subId, catId, name, price) {
        showSubcategoryModal(catId, subId, name, price);
    };

    window.deleteSubcategory = function (subId) {
        window.showConfirmModal(
            'Yakin hapus subkategori ini? Semua item akan ikut terhapus.',
            async () => {
                const res = await fetch(`/api/products/subcategories/${subId}`, { method: 'DELETE' });
                const data = await res.json();
                showToast(data.message, data.success ? 'success' : 'error');
                if (data.success) {
                    const catId = document.getElementById('catSelect').value;
                    renderSubcategories(catId, currentProductPage);
                }
            }
        );
    };


    // ═══════════════ ITEM ═══════════════
    window.renderItemSelector = async function (page = 1) {
        currentProductPage = page;
        const catsRes = await fetch('/api/products/categories?limit=100');
        const cats = await catsRes.json();
        
        let catSelectHtml = `<select id="itemCatSelect" class="form-select" style="display:none;">`;
        catSelectHtml += '<option value="">-- Pilih --</option>';
        cats.data.forEach(c => { catSelectHtml += `<option value="${c.id}">${c.name}</option>`; });
        catSelectHtml += '</select>';

        let html = `
        <div class="form-group" onclick="window.showSearchableDropdown(document.getElementById('itemCatSelect'))">
            <label>Kategori</label>
            <div class="form-input" style="cursor:pointer;" id="catLabel">-- Pilih Kategori --</div>
            ${catSelectHtml}
        </div>
        <div class="form-group" onclick="if(!document.getElementById('itemSubSelect').disabled) window.showSearchableDropdown(document.getElementById('itemSubSelect'))">
            <label>Subkategori</label>
            <div class="form-input" style="cursor:pointer;" id="subLabel">-- Pilih kategori dulu --</div>
            <select id="itemSubSelect" class="form-select" disabled style="display:none;">
                <option value="">-- Pilih kategori dulu --</option>
            </select>
        </div>
        <div id="itemList"></div>`;
        content.innerHTML = html;

        document.getElementById('itemCatSelect').addEventListener('change', async (e) => {
            const catId = e.target.value;
            const subSelect = document.getElementById('itemSubSelect');
            const catLabel = document.getElementById('catLabel');
            const subLabel = document.getElementById('subLabel');
            
            catLabel.textContent = e.target.options[e.target.selectedIndex].text;
            
            if (!catId) {
                subSelect.innerHTML = '<option value="">-- Pilih kategori dulu --</option>';
                subSelect.disabled = true;
                subLabel.textContent = '-- Pilih kategori dulu --';
                document.getElementById('itemList').innerHTML = '';
                return;
            }
            const subRes = await fetch(`/api/products/subcategories?category_id=${catId}&limit=100`);
            const subs = await subRes.json();
            subSelect.innerHTML = '<option value="">-- Pilih --</option>';
            subs.data.forEach(s => { subSelect.innerHTML += `<option value="${s.id}">${s.name}</option>`; });
            subSelect.disabled = false;
            subLabel.textContent = '-- Pilih Subkategori --';
        });

        document.getElementById('itemSubSelect').addEventListener('change', async (e) => {
            const subId = e.target.value;
            const subLabel = document.getElementById('subLabel');
            subLabel.textContent = e.target.options[e.target.selectedIndex].text;
            currentSubId = subId;
            if (subId) await renderItems(subId, 1);
            else document.getElementById('itemList').innerHTML = '';
        });
    };

    async function renderItems(subId, page) {
        const [itemRes, sumData] = await Promise.all([
            fetch(`/api/products/items?subcategory_id=${subId}&page=${page}&limit=${itemsPerPage}`).then(r => r.json()),
            fetchSummary('item', `&subcategory_id=${subId}`)
        ]);
        const itemList = document.getElementById('itemList');
        let html = renderSummaryGrid(sumData, 'item');
        html += '<div class="btn-row">';
        html += '<button class="btn btn-primary" onclick="window.showItemModal(' + subId + ')">➕ Tambah</button>';
        html += '<button class="btn btn-outline" onclick="window.importCSV(' + subId + ')">📥 Impor</button>';
        html += '<button class="btn btn-outline" onclick="window.exportCSV(' + subId + ')">📤 Ekspor</button>';
        html += '</div>';
        const start = (page - 1) * itemsPerPage;

        itemRes.data.forEach((item, index) => {
            html += `
            <div class="list-row">
                <span class="list-row-label">
                    ${start + index + 1}. ${item.code}
                    <small>(${item.is_used ? '🔒 Terpakai' : '🟢 Tersedia'})</small>
                </span>
                <div class="list-row-actions">
                    ${!item.is_used ? `
                        <button class="btn-icon" onclick="window.editItem(${item.id}, '${item.code}')">✏️</button>
                        <button class="btn-icon" onclick="window.deleteItem(${item.id})">🗑️</button>
                    ` : ''}
                </div>
            </div>`;
        });
        html += paginationControls(page, itemRes.total, `window.renderItemsPage`);
        window.renderItemsPage = function (p) { renderItems(subId, p); };
        itemList.innerHTML = html;
    };

    window.showItemModal = function (subId, itemId = null, oldCode = '') {
        const title = itemId ? 'Edit Item' : 'Tambah Item';
        const action = itemId ? `window.updateItem(${itemId})` : `window.createItem(${subId})`;
        const html = `
            <div class="modal-overlay show" id="modalOverlay">
                <div class="modal">
                    <div class="form-wrapper" style="overflow-y:auto; flex: 1;">
                        <p>${title}</p>
                        <div class="form-group">
                            <textarea id="modalCode" class="form-textarea" rows="5" placeholder="Masukkan kode (satu per baris)">${oldCode}</textarea>
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-primary" onclick="${action}">Simpan</button>
                        <button class="btn btn-outline" onclick="window.closeModal()">Batal</button>
                    </div>
                </div>
            </div>`;
        document.body.insertAdjacentHTML('beforeend', html);
        setupKeyboardAware(document.getElementById('modalOverlay'));
    };

    window.createItem = async function (subId) {
        const codes = document.getElementById('modalCode').value.trim();
        if (!codes) return showToast('Kode tidak boleh kosong.', 'error');
        const formData = new FormData();
        formData.append('subcategory_id', subId);
        formData.append('codes', codes);
        const res = await fetch('/api/products/items', { method: 'POST', body: formData });
        const data = await res.json();
        showToast(data.message, data.success ? 'success' : 'error');
        closeModal();
        if (data.success) renderItems(subId, currentProductPage);
    };

    window.updateItem = async function (itemId) {
        const newCode = document.getElementById('modalCode').value.trim();
        if (!newCode) return showToast('Kode tidak boleh kosong.', 'error');
        const formData = new FormData();
        formData.append('new_code', newCode);
        const res = await fetch(`/api/products/items/${itemId}`, { method: 'PUT', body: formData });
        const data = await res.json();
        showToast(data.message, data.success ? 'success' : 'error');
        closeModal();
        if (data.success) {
            renderItems(currentSubId, currentProductPage);
        }
    };

    window.editItem = function (itemId, code) {
        showItemModal(currentSubId, itemId, code);
    };

    window.deleteItem = function (itemId) {
        window.showConfirmModal(
            'Yakin hapus item ini?',
            async () => {
                const res = await fetch(`/api/products/items/${itemId}`, { method: 'DELETE' });
                const data = await res.json();
                showToast(data.message, data.success ? 'success' : 'error');
                if (data.success) {
                    renderItems(currentSubId, currentProductPage);
                }
            }
        );
    };

    window.exportCSV = async function (subId) {
        const res = await fetch(`/api/products/items/export?subcategory_id=${subId}`);
        const data = await res.json();
        const blob = new Blob([data.codes.join('\n')], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `items_sub${subId}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    window.importCSV = async function (subId) {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.csv';
        fileInput.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            formData.append('subcategory_id', subId);
            const res = await fetch('/api/products/items/import/preview', { method: 'POST', body: formData });
            const preview = await res.json();
            let html = '<div class="modal-overlay show"><div class="modal"><p>Pratinjau Impor</p>';
            preview.forEach(p => {
                html += `<div>${p.code} - ${p.status === 'duplicate' ? '⚠️ Duplikat' : '✅ Baru'}</div>`;
            });
            html += `<div class="modal-actions">
                <button class="btn btn-primary" onclick="window.executeImport(${subId}, '${preview.filter(p => p.status === 'new').map(p => p.code).join('\n')}')">Impor Semua Baru</button>
                <button class="btn btn-outline" onclick="window.closeModal()">Batal</button>
            </div></div></div>`;
            document.body.insertAdjacentHTML('beforeend', html);
        };
        fileInput.click();
    };

    window.executeImport = async function (subId, codes) {
        const formData = new FormData();
        formData.append('subcategory_id', subId);
        formData.append('codes', codes);
        const res = await fetch('/api/products/items/import/execute', { method: 'POST', body: formData });
        const data = await res.json();
        showToast(data.message, data.success ? 'success' : 'error');
        closeModal();
        if (data.success) renderItems(subId, currentProductPage);
    };

    // ═══════════════ DATA (Ekspor/Impor Global) ═══════════════
    window.loadDataTab = async function () {
        content.innerHTML = `<div class="placeholder"><p>🔄 Memuat data...</p></div>`;
        let html = '<div class="list-title">📦 Data Global</div>';
        html += '<div class="btn-row">';
        html += '<button class="btn btn-primary" onclick="window.exportAllData()">📤 Ekspor CSV Global</button>';
        html += '<button class="btn btn-outline" onclick="window.importGlobalCSV()">📥 Impor CSV Global</button>';
        html += '</div>';
        html += '<div id="importResult"></div>';
        content.innerHTML = html;
    };

    window.exportAllData = async function () {
        try {
            const res = await fetch('/api/products/export-all');
            if (!res.ok) {
                showToast('Gagal mengekspor data.', 'error');
                return;
            }
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'semua_item.csv';
            a.click();
            URL.revokeObjectURL(url);
            showToast('✅ Ekspor berhasil.', 'success');
        } catch (e) {
            showToast('❌ Gagal mengekspor data.', 'error');
        }
    };

    window.importGlobalCSV = function () {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.csv';
        fileInput.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            showToast('⏳ Mengimpor...', 'info');
            try {
                const res = await fetch('/api/products/import', { method: 'POST', body: formData });
                const data = await res.json();
                showToast(data.message, data.success ? 'success' : 'error');
                if (data.success) {
                    document.getElementById('importResult').innerHTML = `<p>✅ ${data.message}</p>`;
                }
            } catch (err) {
                showToast('❌ Gagal mengimpor.', 'error');
            }
        };
        fileInput.click();
    };

    // ── Pagination ──
    function paginationControls(page, total, callback) {
        const totalPages = Math.ceil(total / itemsPerPage);
        if (totalPages <= 1) return '';
        let html = '<div class="pagination">';
        if (page > 1) html += `<button class="btn-page" onclick="(${callback})(${page - 1})">◀</button>`;
        html += `<span>Hal ${page}/${totalPages}</span>`;
        if (page < totalPages) html += `<button class="btn-page" onclick="(${callback})(${page + 1})">▶</button>`;
        html += '</div>';
        return html;
    }
})();