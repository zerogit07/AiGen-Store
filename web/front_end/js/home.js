// web/front_end/js/home.js
async function loadHomePage() {
    try {
        const res = await fetch('/api/home');
        const data = await res.json();
        
        let html = '';
        
        // Baris 1: Pendapatan (full width)
        html += `
            <div class="home-revenue card">
                <div class="card-label-center">💰 Pendapatan</div>
                <div class="card-value-large">Rp${data.total_revenue}</div>
            </div>`;
        
        // Baris 2: Masuk & Pending (grid 2 kolom)
        html += '<div class="home-grid-2">';
        html += `
            <div class="card">
                <div class="card-label-center">📥 Masuk</div>
                <div class="card-value-large">${data.incoming_total}</div>
            </div>`;
        html += `
            <div class="card">
                <div class="card-label-center">⏳ Pending</div>
                <div class="card-value-large">${data.pending_total}</div>
            </div>`;
        html += '</div>';
        
        // Baris 3: Statistik Data & Statistik Pesanan (grid 2 kolom, TERTUKAR)
        html += '<div class="home-grid-2">';
        // Statistik Data (sekarang di kiri)
        html += `
            <div class="card">
                <div class="card-label-center">📁 Statistik Data</div>
                <div class="home-stats-list">
                    <div class="home-stat-row"><span>📁 Kategori</span><span>${data.categories}</span></div>
                    <div class="home-stat-row"><span>📂 Subkategori</span><span>${data.subcategories}</span></div>
                    <div class="home-stat-row"><span>🎫 Item Terjual</span><span>${data.items_sold}</span></div>
                    <div class="home-stat-row"><span>🟢 Item Tersedia</span><span>${data.items_available}</span></div>
                </div>
            </div>`;
        // Statistik Pesanan (sekarang di kanan)
        html += `
            <div class="card">
                <div class="card-label-center">📊 Statistik Pesanan</div>
                <div class="home-stats-list">
                    <div class="home-stat-row"><span>✅ Disetujui</span><span>${data.approved}</span></div>
                    <div class="home-stat-row"><span>⏳ Pending</span><span>${data.pending_total}</span></div>
                    <div class="home-stat-row"><span>❌ Ditolak</span><span>${data.rejected}</span></div>
                    <div class="home-stat-row"><span>📦 Total</span><span>${data.total_orders}</span></div>
                </div>
            </div>`;
        html += '</div>';
        
        // Baris 4: Pesanan Terbaru
        if (data.recent_orders && data.recent_orders.length > 0) {
            html += '<div class="card"><div class="card-label-center">📥 Pesanan Terbaru</div>';
            data.recent_orders.forEach(o => {
                html += `
                    <div class="card" style="margin-top:8px;">
                        <div class="card-row"><span class="card-label">Order</span><span class="card-value">${o.order_id}</span></div>
                        <div class="card-row"><span class="card-label">User</span><span class="card-value">${o.user_id}</span></div>
                        <div class="card-row"><span class="card-label">Produk</span><span class="card-value">${o.product}</span></div>
                        <div class="card-row"><span class="card-label">Qty</span><span class="card-value">${o.qty}</span></div>
                        <div class="card-row"><span class="card-label">Total</span><span class="card-value">Rp${o.total}</span></div>
                    </div>`;
            });
            html += '</div>';
        }
        
        content.innerHTML = html;
    } catch (e) {
        content.innerHTML = '<div class="placeholder"><p>❌ Gagal memuat data.</p></div>';
    }
}