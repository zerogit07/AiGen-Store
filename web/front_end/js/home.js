// web/front_end/js/home.js

let currentUserPage = 1;

let currentReportPage = 1;

let currentSearch = "";

let currentFilter = "";

let currentFilterLabel = "-- Filter --";

let currentStartDate = "";

let currentEndDate = "";

let currentMonth = "";

let currentCustomType = "";

async function loadHomePage(tab = "statistik") {
    try {
        let endpoint = `/api/home?month=${currentMonth}`;

        if (tab === "user") {
            endpoint = `/api/home/users?page=${currentUserPage}&search=${currentSearch}`;
        }

        if (tab === "laporan") {
            endpoint = `
            /api/home/report
            ?page=${currentReportPage}
            
            &filter_type=${currentFilter}
            
            &custom_type=${currentCustomType}
            
            &start_date=${currentStartDate}
            
            &end_date=${currentEndDate}
            `;

            endpoint = endpoint.replace(/\n/g, "").replace(/\s+/g, "");
        }

        const res = await fetch(endpoint);

        const data = await res.json();

        const renderMap = {
            statistik: () => renderStatistik(data),

            user: () => renderUser(data),

            laporan: () => renderLaporan(data)
        };

        content.innerHTML =
            renderMap[tab]?.() || renderPlaceholder("Tab tidak ditemukan");

        initEvents(tab);
    } catch (e) {
        console.log(e);

        content.innerHTML = renderPlaceholder("❌ Gagal memuat");
    }
}

function initEvents(tab) {}

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

        <div class="revenue-header">

            <span>💰 Pendapatan •</span>

            <button
                class="month-btn"
                onclick="openMonthModal()"
            >
                ${data.bulan}
            </button>

        </div>

        <div class="card-value-large">
            Rp${data.total_revenue}
        </div>

    </div>

    ${renderMonthModal()}
    `;
}

function renderMonthModal() {
    const bulan = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember"
    ];

    return `
    <div
        id="monthModal"
        class="home-modal"
    >

        <div class="home-modal-content">

            <input
                id="monthSearch"
                class="search-modal-input"
                placeholder="🔎 Cari bulan..."
                oninput="filterMonth()"
            >

            <div id="monthList">

                ${bulan
                    .map(
                        item => `
                    <div
                        class="month-item"
                        onclick="
                            selectMonth(
                                '${item}'
                            )
                        "
                    >
                        ${item}
                    </div>
                `
                    )
                    .join("")}

            </div>

        </div>

    </div>
    `;
}

function openMonthModal() {
    document.getElementById("monthModal").style.display = "block";
}

function closeMonthModal() {
    document.getElementById("monthModal").style.display = "none";
}

function selectMonth(month) {
    currentMonth = month;

    closeMonthModal();

    loadHomePage("statistik");
}

function filterMonth() {
    const input = document.getElementById("monthSearch").value.toLowerCase();

    const items = document.querySelectorAll(".month-item");

    items.forEach(item => {
        item.style.display = item.innerText.toLowerCase().includes(input)
            ? "block"
            : "none";
    });
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

        <div class="card">

            <div class="card-label-center">
                📊 Statistik Pesanan
            </div>

            <table class="summary-table">
                <tbody>

                    <tr>
                        <td>Disetujui</td>
                        <td>${data.approved}</td>
                    </tr>

                    <tr>
                        <td>Pending</td>
                        <td>${data.pending}</td>
                    </tr>

                    <tr>
                        <td>Ditolak</td>
                        <td>${data.rejected}</td>
                    </tr>

                    <tr>
                        <td>Total</td>
                        <td>${data.total_orders}</td>
                    </tr>

                </tbody>
            </table>

        </div>

    </div>
    `;
}

function renderInfoCard(title, rows) {
    return `
    <div class="card">

        <div class="card-label-center">
            ${title}
        </div>

        <table class="summary-table">

            <tbody>

                ${rows
                    .map(
                        ([label, value]) => `
                    <tr>
                        <td>${label}</td>
                        <td>${value}</td>
                    </tr>
                `
                    )
                    .join("")}

            </tbody>

        </table>

    </div>
    `;
}

/* ======================
   USER
====================== */

function renderUser(data) {
    return [renderUserTable(data), renderUserModal(), renderSearchModal()].join(
        ""
    );
}

function renderUserTable(data) {
    return `
    <div class="card">

        <button
            class="filter-btn"
            onclick="openSearchModal()"
        >
            Cari User
        </button>

        <div class="table-responsive">

            <table class="user-table">

                <thead>
                    <tr>
                        <th>No</th>
                        <th>User ID</th>
                        <th>Username</th>
                        <th>Order</th>
                        <th>Total</th>
                        <th>Status</th>
                    </tr>
                </thead>

                <tbody>
                    ${renderUserRows(data.data)}
                </tbody>

            </table>

        </div>

        ${renderPagination(data.pagination, "user")}

    </div>
    `;
}

function renderUserRows(users) {
    return users
        .map(
            (user, index) => `
        <tr
            onclick="
                openUserModal(
                    ${user.user_id}
                )
            "
        >

            <td>${index + 1}</td>

            <td>${user.user_id}</td>

            <td>${user.username}</td>

            <td>${user.order}</td>

            <td>${user.total}</td>

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
    <div
        id="userModal"
        class="home-modal">

        <div
            id="userModalContent"
            class="home-modal-content">

        </div>

    </div>
    `;
}
function renderSearchModal() {
    return `
    <div
        id="searchModal"
        class="home-modal"
    >

        <div class="home-modal-content">

            <h3>
                Cari User
            </h3>

            <input
                id="searchUserInput"
                class="search-modal-input"
                placeholder="Masukkan User ID"
            >

            <div class="modal-action">

                <button
                    onclick="submitSearch()"
                >
                    Cari
                </button>

                <button
                    onclick="closeSearchModal()"
                >
                    Batal
                </button>

            </div>

        </div>

    </div>
    `;
}

function closeUserModal() {
    document.getElementById("userModal").style.display = "none";
}

async function openUserModal(userId) {
    const res = await fetch(`/api/home/user-detail?user_id=${userId}`);

    const data = await res.json();

    document.getElementById("userModalContent").innerHTML = `

        <h3>
            Detail User
        </h3>

        <p>
            ID :
            ${data.user_id}
        </p>

        <p>
            Username :
            ${data.username}
        </p>

        <p>
            Order :
            ${data.order}
        </p>

        <p>
            Total :
            ${data.total}
        </p>

        <p>
            Status :
            ${data.status}
        </p>

        <button onclick="toggleUserStatus(${data.user_id},${data.is_banned})">
    ${data.is_banned ? "Unban User" : "Ban User"}
</button>

<button onclick="closeUserModal()">
    Tutup
</button>
    `;

    document.getElementById("userModal").style.display = "block";
}
async function toggleUserStatus(userId, banned) {
    await fetch("/api/home/user-status", {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            user_id: userId,
            status: banned ? 0 : 1
        })
    });

    closeUserModal();

    loadHomePage("user");
}

function openSearchModal() {
    document.getElementById("searchModal").style.display = "block";
}

function closeSearchModal() {
    document.getElementById("searchModal").style.display = "none";
}

function submitSearch() {
    const value = document.getElementById("searchUserInput").value;

    currentSearch = value;

    currentUserPage = 1;

    closeSearchModal();

    loadHomePage("user");
}
/* ======================
   PAGINATION
====================== */

function renderPagination(data, tab) {
    const totalPages = data.total_pages || 1;

    return `
    <div class="pagination">

        <button
            onclick="
            changePage(
            '${tab}',
            -1
            )
            "

            ${data.page <= 1 ? "disabled" : ""}
        >

            Prev

        </button>

        <span>

            ${data.page}
            /
            ${totalPages}

        </span>

        <button
            onclick="
            changePage(
            '${tab}',
            1
            )
            "

            ${data.page >= totalPages ? "disabled" : ""}

        >

            Next

        </button>

    </div>
    `;
}

function changePage(tab, step) {
    if (tab === "user") {
        currentUserPage = Math.max(1, currentUserPage + step);
    }

    if (tab === "laporan") {
        currentReportPage = Math.max(1, currentReportPage + step);
    }

    loadHomePage(tab);
}
/* ======================
   LAPORAN
====================== */

function renderLaporan(data) {
    return [
        renderFilterButton(),
        renderProdukTerlaris(data.products),
        renderRiwayat(data),
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
            onclick="openFilterModal()">

            ${currentFilterLabel}

        </button>

    </div>
    `;
}

function renderFilterModal() {
    return `
    <div
        id="filterModal"
        class="home-modal"
    >

        <div class="filter-overlay">

            <div class="home-modal-content filter-box">

                <h3>
                    Filter Laporan
                </h3>

                <button
                    onclick="
                        selectFilter(
                            'today'
                        )
                    "
                >
                    Hari Ini
                </button>

                <button
                    onclick="
                        selectFilter(
                            'week'
                        )
                    "
                >
                    Minggu Ini
                </button>

                <button
                    onclick="
                        selectFilter(
                            'month'
                        )
                    "
                >
                    Bulan Ini
                </button>

                <button
                    onclick="
                        selectFilter(
                            'year'
                        )
                    "
                >
                    Tahun Ini
                </button>

                <button
                    onclick="
                        openCustomFilter()
                    "
                >
                    Custom
                </button>

                <button
                    onclick="
                        closeFilterModal()
                    "
                >
                    Tutup
                </button>

            </div>

        </div>

    </div>
    `;
}

function selectFilter(type) {
    currentFilter = type;

    currentReportPage = 1;

    closeFilterModal();

    loadHomePage("laporan");
}

function openFilterModal() {
    document.getElementById("filterModal").style.display = "block";
}

function closeFilterModal() {
    document.getElementById("filterModal").style.display = "none";
}
function openCustomFilter() {
    document.getElementById("filterModal").innerHTML = `

<div class="filter-overlay">

    <div class="home-modal-content filter-box">

        <h3>
            Custom
        </h3>

        <button onclick="selectCustomType('range')">
            Rentang
        </button>

        <button onclick="selectCustomType('day')">
            Hari
        </button>

        <button onclick="selectCustomType('week')">
            Minggu
        </button>

        <button onclick="selectCustomType('month')">
            Bulan
        </button>

        <button onclick="selectCustomType('year')">
            Tahun
        </button>

        <button onclick="backToFilter()">
            Kembali
        </button>

    </div>

</div>

`;
}

function backToFilter() {
    document.getElementById("filterModal").outerHTML = renderFilterModal();

    openFilterModal();
}

function selectCustomType(type) {
    let html = "";

    if (type === "range") {
        html = `

    <h3>Rentang</h3>

    <input
        id="startDate"
        type="date"
        class="search-modal-input"
    >

    <input
        id="endDate"
        type="date"
        class="search-modal-input"
    >

    <button onclick="applyRange()">
        Terapkan
    </button>

    <button onclick="openCustomFilter()">
        Kembali
    </button>
    `;
    } else if (type === "day") {
        html = `

    <h3>Pilih Hari</h3>

    <input
        id="dayDate"
        type="date"
        class="search-modal-input"
    >

    <button onclick="applyDay()">
        Terapkan
    </button>

    <button onclick="openCustomFilter()">
        Kembali
    </button>
    `;
    } else if (type === "week") {
        html = `

    <h3>Pilih Minggu</h3>

    <input
        id="weekDate"
        type="week"
        class="search-modal-input"
    >

    <button onclick="applyWeek()">
        Terapkan
    </button>

    <button onclick="openCustomFilter()">
        Kembali
    </button>
    `;
    } else if (type === "month") {
        html = `

    <h3>Pilih Bulan</h3>

    <input
        id="monthDate"
        type="month"
        class="search-modal-input"
    >

    <button onclick="applyMonth()">
        Terapkan
    </button>

    <button onclick="openCustomFilter()">
        Kembali
    </button>
    `;
    } else if (type === "year") {
        const years = [];

        for (let i = new Date().getFullYear(); i >= 2020; i--) {
            years.push(i);
        }

        html = `

    <h3>
        Pilih Tahun
    </h3>

    <select
        id="yearDate"
        class="search-modal-input"
    >

        <option value="">
            Pilih tahun
        </option>

        ${years
            .map(
                year => `
                <option value="${year}">
                    ${year}
                </option>
                `
            )
            .join("")}

    </select>

    <button onclick="applyYear()">
        Terapkan
    </button>

    <button onclick="openCustomFilter()">
        Kembali
    </button>
    `;
    }

    document.getElementById("filterModal").innerHTML = `

    <div class="filter-overlay">

        <div
            class="
            home-modal-content
            filter-box
            "
        >

            ${html}

        </div>

    </div>

    `;
}

function applyRange() {
    currentCustomType = "range";

    currentStartDate = document.getElementById("startDate").value;

    currentEndDate = document.getElementById("endDate").value;

    currentFilterLabel = "📅 Rentang";

    currentReportPage = 1;

    closeFilterModal();

    loadHomePage("laporan");
}

function applyDay() {
    currentCustomType = "day";

    currentStartDate = document.getElementById("dayDate").value;

    currentEndDate = "";

    currentFilterLabel = "📅 Hari";

    currentReportPage = 1;

    closeFilterModal();

    loadHomePage("laporan");
}

function applyWeek() {
    currentCustomType = "week";

    currentStartDate = document.getElementById("weekDate").value;

    currentEndDate = "";

    currentFilterLabel = "📅 Minggu";

    currentReportPage = 1;

    closeFilterModal();

    loadHomePage("laporan");
}

function applyMonth() {
    currentCustomType = "month";

    currentStartDate = document.getElementById("monthDate").value;

    currentEndDate = "";

    currentFilterLabel = "📅 Bulan";

    currentReportPage = 1;

    closeFilterModal();

    loadHomePage("laporan");
}

function applyYear() {
    currentCustomType = "year";

    currentStartDate = document.getElementById("yearDate").value;

    currentEndDate = "";

    currentFilterLabel = "📅 Tahun";

    currentReportPage = 1;

    closeFilterModal();

    loadHomePage("laporan");
}

/* ======================
   SUMMARY
====================== */

function renderSummary(data) {
    return `
    <div class="card">
        <div class="card-label-center">
            Ringkasan
        </div>

        <table class="summary-table">
            <tbody>

                <tr>
                    <td>Pendapatan</td>
                    <td>${data.pendapatan}</td>
                </tr>

                <tr>
                    <td>Disetujui</td>
                    <td>${data.approved}</td>
                </tr>

                <tr>
                    <td>Pending</td>
                    <td>${data.pending}</td>
                </tr>

                <tr>
                    <td>Ditolak</td>
                    <td>${data.rejected}</td>
                </tr>

                <tr>
                    <td>Total</td>
                    <td>${data.order}</td>
                </tr>

            </tbody>
        </table>

    </div>
    `;
}

/* ======================
   PRODUK
====================== */

function renderProdukTerlaris(products) {
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

                ${products
                    .map(
                        (item, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${item.name}</td>
                        <td>${item.sold}</td>
                    </tr>
                    `
                    )
                    .join("")}

            </tbody>

        </table>

    </div>
    `;
}

/* ======================
   RIWAYAT
====================== */

function renderRiwayat(data) {
    return `
    <div class="card">

        <div class="card-label-center">
            Riwayat Transaksi
        </div>

        <div class="table-responsive">

            <table class="history-table">

                <thead>
                    <tr>
                        <th>No</th>
                        <th>Order ID</th>
                        <th>User ID</th>
                        <th>Username</th>
                        <th>Produk</th>
                        <th>Qty</th>
                        <th>Total</th>
                        <th>Tanggal</th>
                        <th>Status</th>
                    </tr>
                </thead>

                <tbody>
                    ${renderRiwayatRows(data.history)}


                </tbody>

            </table>

        </div>

        ${renderPagination(data.pagination, "laporan")}

    </div>
    `;
}

function renderRiwayatRows(data) {
    return data
        .map(
            (item, index) => `
        <tr>

            <td>${index + 1}</td>

            <td>${item.id}</td>

            <td>${item.user_id}</td>

            <td>${item.username}</td>

            <td class="history-product">
                ${item.produk}
            </td>

            <td>${item.qty}</td>

            <td>${item.total}</td>

            <td>${item.tanggal}</td>

            <td>
                ${renderOrderStatus(item.status)}
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

function renderOrderStatus(status) {
    let cls = "warning";

    if (status === "approved") {
        cls = "success";
    }

    if (status === "rejected") {
        cls = "danger";
    }

    return `
    <span class="badge ${cls}">
        ${status}
    </span>
    `;
}
