// web/front_end/js/app.js

// AiGen Store - Entry Point
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const sidebar = $('#sidebar');
const overlay = $('#overlay');
const sidebarToggle = $('#sidebarToggle');
const pageTitle = $('#pageTitle');
const tabBar = $('#tabBar');
const content = $('#content');

let currentPage = 'home';
let currentTab = '';
let sidebarOpen = false;

// ---------- SIDEBAR ----------
function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add('open');
    if (overlay) overlay.classList.add('show');
    sidebarOpen = true;}

function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('show');
    sidebarOpen = false;}

function toggleSidebar() {
    sidebarOpen ? closeSidebar() : openSidebar();}

if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
if (overlay) overlay.addEventListener('click', closeSidebar);

// Swipe gesture
let touchStartX = 0;
document.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
}, { passive: true });

document.addEventListener('touchend', (e) => {
    if (!sidebar) return;
    const diff = e.changedTouches[0].clientX - touchStartX;
    if (diff > 80 && touchStartX < 40 && !sidebarOpen) openSidebar();
});

// ---------- NAVIGASI ----------
function updatePageTitle(page) {
    if (!pageTitle) return;
    const titles = {
        home: '🏠 Home',
        products: '📂 Produk',
        orders: '📦 Pesanan',
        broadcast: '📣 Broadcast',
        settings: '⚙️ Pengaturan'
    };
    pageTitle.textContent = titles[page] || page;
}

function updateTabBar(page, tabs) {
    if (!tabBar) return;
    tabBar.innerHTML = '';
    if (!tabs || tabs.trim() === '') {
        tabBar.classList.add('hidden');
        return;
    }
    tabBar.classList.remove('hidden');
    const tabLabels = {
        data: 'Data',
        kategori: 'Kategori',
        subkategori: 'Subkategori',
        item: 'Item',
        masuk: 'Masuk',
        pending: 'Pending',
        riwayat: 'Riwayat',
        banner: 'Banner',
        qris: 'QRIS',
        autodelete: 'Auto Delete',
        manualdelete: 'Manual Delete'
    };
    tabs.split(',').forEach((tab, i) => {
        const name = tab.trim();
        const btn = document.createElement('button');
        btn.className = 'tab-btn';
        btn.textContent = tabLabels[name] || name;
        btn.dataset.tab = name;
        if (i === 0) btn.classList.add('active');
        btn.addEventListener('click', () => {
            $$('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTab = name;
            loadPageContent(page, name);
        });
        tabBar.appendChild(btn);
    });
}

const sidebarItems = $$('.sidebar-item');
sidebarItems.forEach(item => {
    item.addEventListener('click', () => {
        const page = item.dataset.page;
        const tabs = item.dataset.tabs;
        sidebarItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        updatePageTitle(page);
        updateTabBar(page, tabs);
        loadPageContent(page, tabs ? tabs.split(',')[0] : '');
        if (window.innerWidth < 768) closeSidebar();
        currentPage = page;
    });
});

// ---------- LOAD CONTENT ----------
async function loadPageContent(page, tab) {
    if (!content) return;
    content.innerHTML = '<div class="placeholder"><p>🔄 Memuat data...</p></div>';
    if (page === 'home') await loadHomePage();
    else if (page === 'orders') await loadOrdersPage(tab);
    else if (page === 'products') await loadProductsPage(tab);
    else if (page === 'broadcast') await loadBroadcastPage();
    else if (page === 'settings') await loadSettingsPage(tab);
    else content.innerHTML = '<div class="placeholder"><p>📄 Segera hadir.</p></div>';
}

// ---------- TOAST NOTIFICATION ----------
let toastTimer;
function showToast(message, type) {
    const old = $('.toast');
    if (old) old.remove();
    if (toastTimer) clearTimeout(toastTimer);
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    toastTimer = setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ---------- MODAL KONFIRMASI (GLOBAL) ----------
window.showConfirmModal = function(message, callback) {
    var oldModal = document.getElementById('confirmModal');
    if (oldModal) oldModal.remove();

    var html = '<div id="confirmModal" class="modal-overlay show">';
    html += '<div class="modal">';
    html += '<p>' + message + '</p>';
    html += '<div class="modal-actions">';
    html += '<button id="confirmYesBtn" class="btn btn-approve">Ya</button>';
    html += '<button id="confirmNoBtn" class="btn btn-outline">Batal</button>';
    html += '</div></div></div>';

    document.body.insertAdjacentHTML('beforeend', html);

    document.getElementById('confirmYesBtn').onclick = function() {
        var modal = document.getElementById('confirmModal');
        if (modal) modal.remove();
        callback();
    };
    document.getElementById('confirmNoBtn').onclick = function() {
        var modal = document.getElementById('confirmModal');
        if (modal) modal.remove();
    };
};

window.closeConfirmModal = function() {
    var modal = document.getElementById('confirmModal');
    if (modal) modal.remove();
};

// ---------- PROFIL ----------
const profileBtn = document.getElementById('profileBtn');
if (profileBtn) {
    profileBtn.addEventListener('click', () => {
        sidebarItems.forEach(i => i.classList.remove('active'));
        pageTitle.textContent = '👤 Profil Admin';
        tabBar.classList.add('hidden');
        loadProfilePage();
        if (window.innerWidth < 768) closeSidebar();
        currentPage = 'profile';
    });
}

// ---------- INIT ----------
document.addEventListener('DOMContentLoaded', () => {
    const home = $('.sidebar-item[data-page="home"]');
    if (home) home.classList.add('active');
    updatePageTitle('home');
    updateTabBar('home', '');
    loadPageContent('home', '');
});