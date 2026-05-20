// web/front_end/js/home.js

async function loadHomePage(tab = "statistik") {
    try {
        const res = await fetch("/api/home");
        const data = await res.json();

        const renderMap = {
            statistik: () => renderStatistik(data),
            user: () => renderUser(),
            laporan: () => renderLaporan()
        };

        content.innerHTML =
            renderMap[tab]?.() || renderPlaceholder("Tab tidak ditemukan");
    } catch (e) {
        console.log(e);

        content.innerHTML = renderPlaceholder("❌ Gagal memuat");
    }
}

/* ======================
   STATISTIK
====================== */

function renderStatistik(data) {
    return [
        renderRevenue(data),
        renderTopCards(data),
        renderStatistikCards(data)
    ].join("");
}

function renderRevenue(data) {
    return `
    <div class="home-revenue card">

        <div class="card-label-center">
            💰 Pendapatan
        </div>

        <div class="card-value-large">
            Rp${data.total_revenue}
        </div>

    </div>
    `;
}

function renderTopCards(data) {
    return `
    <div class="home-grid-2">

        ${renderSimpleCard("📥 Masuk", data.incoming_total)}

        ${renderSimpleCard("⏳ Pending", data.pending_total)}

    </div>
    `;
}

function renderSimpleCard(title, value) {
    return `
    <div class="card">

        <div class="card-label-center">
            ${title}
        </div>

        <div class="card-value-large">
            ${value}
        </div>

    </div>
    `;
}

function renderStatistikCards(data) {
    return `
    <div class="home-grid-2">

        ${renderInfoCard("📁 Statistik Data", [
            ["Kategori", data.categories],
            ["Subkategori", data.subcategories],
            ["Terjual", data.items_sold],
            ["Tersedia", data.items_available]
        ])}

        ${renderInfoCard("📊 Statistik Pesanan", [
            ["Disetujui", data.approved],
            ["Ditolak", data.rejected],
            ["Total", data.total_orders]
        ])}

    </div>
    `;
}

function renderInfoCard(title, rows) {
    return `
    <div class="card">

        <div class="card-label-center">
            ${title}
        </div>

        <div class="home-stats-list">

            ${rows
                .map(
                    ([label, value]) => `
                    <div class="home-stat-row">

                        <span>${label}</span>

                        <span>${value}</span>

                    </div>
                    `
                )
                .join("")}

        </div>

    </div>
    `;
}

/* ======================
   USER
====================== */

function renderUser() {
    return [renderUserTable(), renderUserModal()].join("");
}

function renderUserTable() {
    return `
    <div class="card">

        <input
            class="table-search"
            placeholder="Cari ID..."
        >

        <div class="table-responsive">

            <table class="user-table">

                <thead>

                    <tr>

                        <th>No</th>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Order</th>
                        <th>Total</th>
                        <th>Status</th>

                    </tr>

                </thead>

                <tbody>

                    ${renderUserRows()}

                </tbody>

            </table>

        </div>

        ${renderPagination()}

    </div>
    `;
}

function renderUserRows() {
    const users = Array.from({ length: 10 }, (_, i) => ({
        id: 100123 + i,
        username: `User${i + 1}`,
        order: Math.floor(Math.random() * 20),

        total: ((i + 1) * 50000).toLocaleString(),

        status: i % 2 === 0 ? "Active" : "Banned"
    }));

    return users
        .map(
            (user, index) => `
            <tr onclick="openUserModal()">

                <td>${index + 1}</td>

                <td>${user.id}</td>

                <td>${user.username}</td>

                <td>${user.order}</td>

                <td>Rp${user.total}</td>

                <td>
                    ${renderStatus(user.status)}
                </td>

            </tr>
            `
        )
        .join("");
}

function renderStatus(status) {
    const cls = status === "Active" ? "success" : "danger";

    return `
    <span class="badge ${cls}">
        ${status}
    </span>
    `;
}

function renderUserModal() {
    return `
    <div id="userModal" class="home-modal">

        <div class="home-modal-content">

            <h3>Detail User</h3>

            <p>ID : 100123</p>

            <p>Username : Abdul</p>

            <p>Order : 15</p>

            <p>Total : Rp150.000</p>

            <button>
                Ban User
            </button>

            <button onclick="closeUserModal()">
                Tutup
            </button>

        </div>

    </div>
    `;
}

function openUserModal() {
    document.getElementById("userModal").style.display = "block";
}

function closeUserModal() {
    document.getElementById("userModal").style.display = "none";
}

/* ======================
   PAGINATION
====================== */

function renderPagination() {
    return `
    <div class="pagination">

        <button>
            Prev
        </button>

        <span>
            1 2 3
        </span>

        <button>
            Next
        </button>

    </div>
    `;
}

/* ======================
   LAPORAN
====================== */

function renderLaporan() {
    return [
        renderFilterButton(),
        renderSummary(),
        renderProdukTerlaris(),
        renderRiwayat(),
        renderFilterModal()
    ].join("");
}

/* ======================
   FILTER
====================== */

function renderFilterButton() {
    return `
    <div class="card">

        <button
            class="filter-btn"
            onclick="openFilterModal()"
        >

            -- Filter --

        </button>

    </div>
    `;
}

function renderFilterModal() {
    return `
    <div id="filterModal" class="home-modal">

        <div class="home-modal-content">

            <h3>
                Filter Laporan
            </h3>

            <button onclick="selectFilter('today')">
                Hari Ini
            </button>

            <button onclick="selectFilter('week')">
                Minggu Ini
            </button>

            <button onclick="selectFilter('month')">
                Bulan Ini
            </button>

            <button onclick="selectFilter('year')">
                Tahun Ini
            </button>

            <button onclick="openCustomFilter()">
                Custom
            </button>

            <button onclick="closeFilterModal()">
                Tutup
            </button>

        </div>

    </div>
    `;
}

function selectFilter(type) {
    console.log(type);

    closeFilterModal();
}

function openFilterModal() {
    document.getElementById("filterModal").style.display = "block";
}

function closeFilterModal() {
    document.getElementById("filterModal").style.display = "none";
}

function openCustomFilter() {
    alert("Custom belum dibuat");
}

/* ======================
   RINGKASAN
====================== */

function renderSummary() {
    return `
    <div class="card">

        <div class="card-label-center">
            Ringkasan
        </div>

        <table class="summary-table">

            <tbody>

                <tr>
                    <td>Pendapatan</td>
                    <td>Rp1.250.000</td>
                </tr>

                <tr>
                    <td>Order</td>
                    <td>120</td>
                </tr>

                <tr>
                    <td>Disetujui</td>
                    <td>113</td>
                </tr>

                <tr>
                    <td>Pending</td>
                    <td>5</td>
                </tr>

                <tr>
                    <td>Ditolak</td>
                    <td>2</td>
                </tr>

            </tbody>

        </table>

    </div>
    `;
}

/* ======================
   PRODUK
====================== */

function renderProdukTerlaris() {
    return `
    <div class="card">

        <div class="card-label-center">
            Produk Terlaris
        </div>

        <table class="top-product-table">

            <thead>

                <tr>

                    <th>No</th>
                    <th>Produk</th>
                    <th>Terjual</th>

                </tr>

            </thead>

            <tbody>

                <tr>
                    <td>1</td>
                    <td>Netflix</td>
                    <td>35</td>
                </tr>

            </tbody>

        </table>

    </div>
    `;
}

/* ======================
   RIWAYAT
====================== */

function renderRiwayat() {
    return `
    <div class="card">

        <div class="card-label-center">
            Riwayat Transaksi
        </div>

        <input
            class="table-search"
            placeholder="Cari Order ID..."
        >

        <div class="table-responsive">

            <table class="history-table">

                <thead>
                    <tr>

                        <th>No</th>
                        <th>Order ID</th>
                        <th>User</th>
                        <th>Produk</th>
                        <th>Total</th>
                        <th>Status</th>

                    </tr>
                </thead>

                <tbody>
                    ${renderRiwayatRows()}
                </tbody>

            </table>

        </div>

        ${renderPagination()}

    </div>
    `;
}

function renderRiwayatRows() {
    const data = Array.from({ length: 10 }, (_, i) => ({
        id: `ORD${129 + i}`,
        user: `User${i + 1}`,
        produk: "Netflix",
        total: "25.000",
        status: "Selesai"
    }));

    return data
        .map(
            (item, index) => `
            <tr>

                <td>${index + 1}</td>

                <td>${item.id}</td>

                <td>${item.user}</td>

                <td>${item.produk}</td>

                <td>Rp${item.total}</td>

                <td>
                    <span class="badge success">
                        ${item.status}
                    </span>
                </td>

            </tr>
        `
        )
        .join("");
}

function renderPlaceholder(text) {
    return `
    <div class="card">

        <div class="card-label-center">
            ${text}
        </div>

    </div>
    `;
}
