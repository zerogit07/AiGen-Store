// AiGen Store - App Entry (Bottom Navigation)

const $ = sel => document.querySelector(sel);
const $$ = sel => document.querySelectorAll(sel);

const pageTitle = $("#pageTitle");
const tabBar = $("#tabBar");
const content = $("#content");

let currentPage = "home";
let currentTab = "";

/* =========================
   PAGE TITLE
========================= */

function updatePageTitle(page) {
    const titles = {
        home: "🏠 Home",
        products: "📂 Produk",
        orders: "📦 Pesanan",
        broadcast: "📣 Broadcast",
        settings: "⚙️ Pengaturan",
        profile: "👤 Profil",
        notifications: "🔔 Notifikasi"
    };

    pageTitle.textContent = titles[page] || page;
}

/* =========================
   TAB
========================= */

function updateTabBar(page, tabs) {
    tabBar.innerHTML = "";

    if (!tabs) {
        tabBar.classList.add("hidden");
        return;
    }

    tabBar.classList.remove("hidden");

    const labels = {
        user: "User",
        statistik: "Statistik",
        laporan: "Laporan",
        kategori: "Kategori",
        subkategori: "Subkategori",
        item: "Item",
        data: "Data",
        masuk: "Masuk",
        pending: "Pending",
        riwayat: "Riwayat",
        banner: "Banner",
        qris: "QRIS",
        autodelete: "Auto Delete",
        manualdelete: "Manual Delete"
    };

    tabs.split(",").forEach((tab, index) => {
        const btn = document.createElement("button");

        btn.className = "tab-btn";
        btn.textContent = labels[tab] || tab;

        if (
            (page === "home" && tab === "statistik") ||
            (page !== "home" && index === 0)
        ) {
            btn.classList.add("active");
            currentTab = tab;
        }

        btn.onclick = () => {
            $$(".tab-btn").forEach(x => x.classList.remove("active"));

            btn.classList.add("active");

            currentTab = tab;

            loadPageContent(page, tab);
        };

        tabBar.appendChild(btn);
    });
}

/* =========================
   LOAD PAGE
========================= */

async function loadPageContent(page, tab = "") {
    content.innerHTML = `
    <div class="placeholder">
        <p>🔄 Memuat...</p>
    </div>`;

    try {
        if (page === "home") {
    await loadHomePage(tab || "statistik");
} else if (page === "products") {
    await loadProductsPage(tab);
} else if (page === "orders") {
    await loadOrdersPage(tab);
} else if (page === "broadcast") {
    await loadBroadcastPage();
} else if (page === "settings") {
    await loadSettingsPage(tab);
} else if (page === "notifications") {
    await loadNotificationsPage();
} else {
    content.innerHTML = `
    <div class="placeholder">
        Halaman belum tersedia
    </div>`;
}
    } catch (e) {
        console.log(e);

        content.innerHTML = `
        <div class="placeholder">
            ❌ Gagal memuat
        </div>`;
    }
}

/* =========================
   BOTTOM NAV
========================= */

const navConfig = {
    home: "user,statistik,laporan",
    products: "kategori,subkategori,item,data",
    orders: "masuk,pending,riwayat",
    broadcast: "",
    settings: "banner,qris,autodelete,manualdelete"
};

$$(".bottom-item").forEach(btn => {
    btn.onclick = () => {
        $$(".bottom-item").forEach(x => x.classList.remove("active"));

        btn.classList.add("active");

        const page = btn.dataset.page;

        currentPage = page;

        updatePageTitle(page);

        updateTabBar(page, navConfig[page]);

        loadPageContent(
            page,
            page === "home"
                ? "statistik"
                : navConfig[page]
                  ? navConfig[page].split(",")[0]
                  : ""
        );
    };
});

/* =========================
   TOAST
========================= */

let toastTimer;

function showToast(message, type = "info") {
    const old = $(".toast");

    if (old) old.remove();

    clearTimeout(toastTimer);

    const toast = document.createElement("div");

    toast.className = `toast ${type}`;

    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("show");
    }, 10);

    toastTimer = setTimeout(() => {
        toast.classList.remove("show");

        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

window.showToast = showToast;

/* =========================
CONFIRM MODAL
========================= */

window.showConfirmModal = function (message, callback) {
    let old = document.getElementById("confirmModal");

    if (old) old.remove();

    document.body.insertAdjacentHTML(
        "beforeend",

        `
<div id="confirmModal"
class="modal-overlay show">

<div class="modal">

<p>${message}</p>

<div class="modal-actions">

<button
id="confirmYesBtn"
class="btn btn-approve">

Ya

</button>

<button
id="confirmNoBtn"
class="btn btn-outline">

Batal

</button>

</div>

</div>

</div>
`
    );

    document.getElementById("confirmYesBtn").onclick = () => {
        document.getElementById("confirmModal").remove();

        callback();
    };

    document.getElementById("confirmNoBtn").onclick = () => {
        document.getElementById("confirmModal").remove();
    };
};

/* =========================
SEARCHABLE DROPDOWN
========================= */

window.showSearchableDropdown = function (selectElement) {
    const options = Array.from(selectElement.options).map(o => ({
        value: o.value,
        label: o.text,
        selected: o.selected
    }));

    let overlay = document.createElement("div");
    overlay.className = "dropdown-overlay";
    overlay.innerHTML = `
        <div class="dropdown-modal">
            <input type="text" class="dropdown-search" placeholder="🔍 Cari...">
            <div class="dropdown-options"></div>
        </div>`;
    document.body.appendChild(overlay);

    const container = overlay.querySelector(".dropdown-options");
    const search = overlay.querySelector(".dropdown-search");

    const render = (filter = "") => {
        container.innerHTML = "";
        options.forEach(o => {
            if (o.label.toLowerCase().includes(filter.toLowerCase())) {
                let div = document.createElement("div");
                div.className =
                    "dropdown-option" + (o.selected ? " selected" : "");
                div.textContent = o.label;
                div.onclick = () => {
                    selectElement.value = o.value;
                    // Trigger change event agar event listener pada select asli berjalan
                    selectElement.dispatchEvent(
                        new Event("change", { bubbles: true })
                    );
                    console.log(
                        "[DEBUG] change triggered:",
                        selectElement.value
                    );
                    overlay.classList.remove("active");
                    setTimeout(() => overlay.remove(), 300);
                };
                container.appendChild(div);
            }
        });
    };

    search.oninput = e => render(e.target.value);
    overlay.onclick = e => {
        if (e.target === overlay) {
            overlay.classList.remove("active");
            setTimeout(() => overlay.remove(), 300);
        }
    };

    render();
    setTimeout(() => overlay.classList.add("active"), 10);
};

/* =========================
PROFILE
========================= */

$("#profileBtn").onclick = () => {
    currentPage = "profile";

    updatePageTitle("profile");

    tabBar.innerHTML = "";
    tabBar.classList.add("hidden");

    loadProfilePage();
};

/* =========================
NOTIF
========================= */

$("#notifBtn").onclick = () => {
    currentPage = "notifications";

    updatePageTitle("notifications");

    tabBar.innerHTML = "";
    tabBar.classList.add("hidden");

    loadNotificationsPage();
};

/* =========================
INIT
========================= */

document.addEventListener("DOMContentLoaded", () => {
    updatePageTitle("home");

    updateTabBar("home", navConfig.home);

    loadPageContent("home", "statistik");
});
