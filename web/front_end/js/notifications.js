// web/front_end/js/notifications.js

async function loadNotificationPage() {
    try {
        const res = await fetch("/api/notifications");
        const data = await res.json();

        let html = "";

        if (!data.length) {
            html = `
            <div class="placeholder">
                <p>🔔 Belum ada notifikasi</p>
            </div>`;
        } else {
            data.forEach(n => {
                html += `
                <div class="card notif-card"
                    onclick="openNotification(
                    ${n.id},
                    '${n.page}',
                    '${n.tab}'
                )">

                    <div class="notif-title">
                        ${n.title}
                    </div>

                    <div class="notif-message">
                        ${n.message || ""}
                    </div>

                    <div class="notif-time">
                         ${formatNotifTime(n.created_at)}
                    </div>

                </div>`;
            });
        }

        document.getElementById("content").innerHTML = html;
    } catch (e) {
        console.log("notif load error", e);

        document.getElementById("content").innerHTML = `
        <div class="placeholder">
            <p>❌ Gagal memuat notif</p>
        </div>`;
    }
}

async function loadNotificationBadge() {
    try {
        const res = await fetch("/api/notifications/badge");

        const data = await res.json();

        let badge = document.querySelector(".notif-badge");

        if (!badge) {
            badge = document.createElement("span");

            badge.className = "notif-badge";

            const btn = document.getElementById("notifBtn");

            if (btn) {
                btn.appendChild(badge);
            }
        }

        if (data.count <= 0) {
            badge.style.display = "none";

            return;
        }

        badge.style.display = "flex";

        badge.textContent = data.count > 99 ? "99+" : data.count;
    } catch (e) {
        console.log("badge gagal", e);
    }
}

async function openNotification(id, page, tab) {
    try {
        await fetch(`/api/notifications/read/${id}`, {
            method: "POST"
        });

        loadNotificationBadge();

        currentPage = page;

        pageTitle.textContent =
            page === "orders" ? "📦 Pesanan" : "🔔 Notifikasi";

        tabBar.classList.remove("hidden");

        updateTabBar(page, "masuk,pending,riwayat");

        loadPageContent(page, tab);
    } catch (e) {
        console.log("notif error", e);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadNotificationBadge();

    setInterval(loadNotificationBadge, 10000);

    const notifButton = document.getElementById("notifBtn");

    if (notifButton) {
        notifButton.addEventListener("click", () => {
            pageTitle.textContent = "🔔 Notifikasi";

            tabBar.classList.add("hidden");

            loadNotificationPage();
        });
    }
});

function formatNotifTime(dateString) {
    const d = new Date(dateString);

    const parts = new Intl.DateTimeFormat("id-ID", {
        timeZone: "Asia/Jakarta",
        hour: "2-digit",
        minute: "2-digit",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour12: false
    }).formatToParts(d);

    const ambil = type => parts.find(x => x.type === type)?.value || "";

    const jam = ambil("hour");
    const menit = ambil("minute");
    const hari = ambil("day");
    const bulan = ambil("month");
    const tahun = ambil("year");

    return `${jam}:${menit} • ${hari}/${bulan}/${tahun} WIB`;
}
