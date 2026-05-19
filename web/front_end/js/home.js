// web/front_end/js/home.js

async function loadHomePage(tab = "statistik") {
    try {
        const res = await fetch("/api/home");
        const data = await res.json();

        let html = "";

        if (tab === "statistik") {

            html += `
            <div class="home-revenue card">
                <div class="card-label-center">💰 Pendapatan</div>
                <div class="card-value-large">
                    Rp${data.total_revenue}
                </div>
            </div>`;

            html += '<div class="home-grid-2">';

            html += `
            <div class="card">
                <div class="card-label-center">📥 Masuk</div>
                <div class="card-value-large">
                    ${data.incoming_total}
                </div>
            </div>`;

            html += `
            <div class="card">
                <div class="card-label-center">⏳ Pending</div>
                <div class="card-value-large">
                    ${data.pending_total}
                </div>
            </div>`;

            html += "</div>";

            html += '<div class="home-grid-2">';

            html += `
            <div class="card">
                <div class="card-label-center">
                📁 Statistik Data
                </div>

                <div class="home-stats-list">
                    <div class="home-stat-row">
                    <span>📁 Kategori</span>
                    <span>${data.categories}</span>
                    </div>

                    <div class="home-stat-row">
                    <span>📂 Subkategori</span>
                    <span>${data.subcategories}</span>
                    </div>

                    <div class="home-stat-row">
                    <span>🎫 Terjual</span>
                    <span>${data.items_sold}</span>
                    </div>

                    <div class="home-stat-row">
                    <span>🟢 Tersedia</span>
                    <span>${data.items_available}</span>
                    </div>
                </div>
            </div>`;

            html += `
            <div class="card">
                <div class="card-label-center">
                📊 Statistik Pesanan
                </div>

                <div class="home-stats-list">
                    <div class="home-stat-row">
                    <span>✅ Disetujui</span>
                    <span>${data.approved}</span>
                    </div>

                    <div class="home-stat-row">
                    <span>❌ Ditolak</span>
                    <span>${data.rejected}</span>
                    </div>

                    <div class="home-stat-row">
                    <span>📦 Total</span>
                    <span>${data.total_orders}</span>
                    </div>
                </div>
            </div>`;

            html += "</div>";
        }

        else if(tab==="user"){

            html=`
            <div class="card">
                <div class="card-label-center">
                👤 User
                </div>

                <div class="home-stats-list">

                <div class="home-stat-row">
                <span>Total User</span>
                <span>Segera</span>
                </div>

                <div class="home-stat-row">
                <span>User Aktif</span>
                <span>Segera</span>
                </div>

                </div>
            </div>`;
        }

        else if(tab==="laporan"){

            html=`
            <div class="card">
                <div class="card-label-center">
                📄 Laporan
                </div>

                <div class="home-stats-list">

                <div class="home-stat-row">
                <span>Hari Ini</span>
                <span>Segera</span>
                </div>

                <div class="home-stat-row">
                <span>Minggu</span>
                <span>Segera</span>
                </div>

                </div>
            </div>`;
        }

        content.innerHTML=html;

    } catch(e){

        content.innerHTML=`
        <div class="placeholder">
        ❌ Gagal memuat
        </div>`;
    }
}