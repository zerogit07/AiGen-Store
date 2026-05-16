// orders.js
let currentOrdersPage = 1;
let currentOrdersTab = "masuk";
let currentFilter = "";

async function loadOrdersPage(tab) {
    currentOrdersTab = tab;
    currentOrdersPage = 1;
    currentFilter = "";
    await renderOrders();
}

async function renderOrders(page = 1) {
    currentOrdersPage = page;
    let url = `/api/orders/${currentOrdersTab}?page=${page}&limit=10`;
    if (currentOrdersTab === "riwayat" && currentFilter) {
        url += `&filter=${currentFilter}`;
    }
    const res = await fetch(url);
    const data = await res.json();
    const orders = data.data;
    const total = data.total;

    let html = "";
    if (currentOrdersTab === "riwayat") {
        html += renderFilterDropdown();
    }
    html += renderOrderList(orders, total, page);
    if (currentOrdersTab === "masuk" && orders.length > 0) {
        html += renderBulkActions();
    }
    content.innerHTML = html;
}

function renderFilterDropdown() {
    return `
        <div class="form-group">
            <select id="historyFilter" class="form-select" onchange="changeHistoryFilter(this.value)">
                <option value="" ${currentFilter === "" ? "selected" : ""}>Semua</option>
                <option value="approved" ${currentFilter === "approved" ? "selected" : ""}>Disetujui</option>
                <option value="rejected" ${currentFilter === "rejected" ? "selected" : ""}>Ditolak</option>
            </select>
        </div>`;
}

function changeHistoryFilter(filter) {
    currentFilter = filter;
    currentOrdersPage = 1;
    renderOrders();
}

function renderOrderList(orders, total, page) {
    if (!orders.length) {
        return '<div class="placeholder"><p>✨ Tidak ada pesanan.</p></div>';
    }
    if (currentOrdersTab === "masuk") {
        // Card
        let html = "";
        orders.forEach(o => {
            html += `
                <div class="card">
                    <div class="card-row"><span class="card-label">Order</span><span class="card-value">${o.order_id}</span></div>
                    <div class="card-row"><span class="card-label">User</span><span class="card-value">${o.user_id}</span></div>
                    <div class="card-row"><span class="card-label">Produk</span><span class="card-value">${o.product}</span></div>
                    <div class="card-row"><span class="card-label">Qty</span><span class="card-value">${o.qty}</span></div>
                    <div class="card-row"><span class="card-label">Total</span><span class="card-value">Rp${o.total}</span></div>
                    <div class="card-actions">
                        <button class="btn btn-approve" onclick="approveOrder('${o.order_id}')">✅ Setujui</button>
                        <button class="btn btn-reject" onclick="rejectOrder('${o.order_id}')">❌ Tolak</button>
                        ${o.proof ? `<button class="btn btn-outline" onclick="viewProof('${o.proof}')">📷 Bukti</button>` : ""}
                    </div>
                </div>`;
        });
        html += pagination(total, page);
        return html;
    } else {
        // Table untuk Pending & Riwayat
        let startNumber = (page - 1) * 10 + 1;
        let html =
            '<div class="table-responsive"><table class="order-table"><thead><tr>';
        html +=
            "<th>No</th><th>Order ID</th><th>User</th><th>Produk</th><th>Qty</th><th>Total</th>";
        if (currentOrdersTab === "riwayat") {
            html += "<th>Status</th><th>Bukti</th>";
        }
        html += "</tr></thead><tbody>";
        orders.forEach((o, index) => {
            let rowNumber = startNumber + index;
            html += `<tr>
                <td>${rowNumber}</td>
                <td>${o.order_id}</td>
                <td>${o.user_id}</td>
                <td>${o.product}</td>
                <td>${o.qty}</td>
                <td>Rp${o.total}</td>`;
            if (currentOrdersTab === "riwayat") {
                let statusLabel =
                    o.status === "approved" ? "Disetujui" : "Ditolak";
                let badgeClass =
                    o.status === "approved" ? "badge-success" : "badge-danger";
                html += `<td><span class="badge ${badgeClass}">${statusLabel}</span></td>`;
                html += `<td>${o.proof ? `<button class="btn btn-outline btn-small" onclick="viewProof('${o.proof}')">📷</button>` : "-"}</td>`;
            }
            html += "</tr>";
        });
        html += "</tbody></table></div>";
        // Pagination selalu muncul jika total > 10
        html += pagination(total, page);
        if (currentOrdersTab === "pending") {
            html += `<div class="card-actions" style="margin-top:16px;"><button class="btn btn-reject" onclick="deletePending()">🗑️ Hapus Semua Pending</button></div>`;
        } else if (currentOrdersTab === "riwayat") {
            html += `<div class="card-actions" style="margin-top:16px;"><button class="btn btn-reject" onclick="deleteHistory()">🗑️ Hapus Riwayat</button></div>`;
        }
        return html;
    }
}

function renderBulkActions() {
    return `<div class="card-actions" style="margin-top:16px;">
        <button class="btn btn-approve" onclick="bulkAction('approve-all')">✅ Setujui Semua</button>
        <button class="btn btn-reject" onclick="bulkAction('reject-all')">❌ Tolak Semua</button>
    </div>`;
}

function pagination(total, currentPage) {
    const totalPages = Math.ceil(total / 10);
    if (totalPages <= 1) return "";
    let html = '<div class="pagination">';
    if (currentPage > 1)
        html += `<button class="btn-page" onclick="renderOrders(${currentPage - 1})">◀</button>`;
    html += `<span>Hal ${currentPage}/${totalPages}</span>`;
    if (currentPage < totalPages)
        html += `<button class="btn-page" onclick="renderOrders(${currentPage + 1})">▶</button>`;
    html += "</div>";
    return html;
}

// ── Aksi ──
async function approveOrder(orderId) {
    window.showConfirmModal("Setujui pesanan ini?", async () => {
        const res = await fetch(`/api/orders/approve/${orderId}`, {
            method: "POST"
        });
        const data = await res.json();
        showToast(data.message, data.success ? "success" : "error");
        if (data.success) renderOrders(currentOrdersPage);
    });
}

async function rejectOrder(orderId) {
    window.showConfirmModal("Tolak pesanan ini?", async () => {
        const res = await fetch(`/api/orders/reject/${orderId}`, {
            method: "POST"
        });
        const data = await res.json();
        showToast(data.message, data.success ? "success" : "error");
        if (data.success) renderOrders(currentOrdersPage);
    });
}

async function bulkAction(action) {
    window.showConfirmModal(
        `Yakin ${action === "approve-all" ? "setujui" : "tolak"} semua pesanan masuk?`,
        async () => {
            const res = await fetch(`/api/orders/${action}`, {
                method: "POST"
            });
            const data = await res.json();
            showToast(data.message, data.success ? "success" : "error");
            if (data.success) renderOrders(1);
        }
    );
}

async function deletePending() {
    window.showConfirmModal("Hapus semua pesanan pending?", async () => {
        const res = await fetch("/api/orders/pending", { method: "DELETE" });
        const data = await res.json();
        showToast(data.message, data.success ? "success" : "error");
        if (data.success) renderOrders(1);
    });
}

async function deleteHistory() {
    let url = "/api/orders/history";
    if (currentFilter) {
        url += `?filter=${currentFilter}`;
    }
    window.showConfirmModal(
        `Hapus riwayat (${currentFilter || "semua"})?`,
        async () => {
            const res = await fetch(url, { method: "DELETE" });
            const data = await res.json();
            showToast(data.message, data.success ? "success" : "error");
            if (data.success) renderOrders(1);
        }
    );
}
function viewProof(fileId) {
    if (fileId.startsWith("http")) {
        window.open(fileId, "_blank");
    } else {
        window.open(
            `https://api.telegram.org/file/bot${BOT_TOKEN}/${fileId}`,
            "_blank"
        );
    }
}
