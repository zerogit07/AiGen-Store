async function loadProfilePage() {
    try {
        const res = await fetch('/api/profile');
        const data = await res.json();

        let html = `
        <div class="card">
            <div class="card-row">
                <span class="card-label">User ID</span>
                <span class="card-value">${data.user_id}</span>
            </div>

            <div class="card-row">
                <span class="card-label">Username</span>
                <span class="card-value">${data.username}</span>
            </div>

            <div class="card-row">
                <span class="card-label">Role</span>
                <span class="card-value">${data.role}</span>
            </div>
        </div>

        <div style="margin-top: 20px;">
            <button id="logoutBtn" class="btn btn-reject" style="width: 100%;">Logout</button>
        </div>
        `;

        content.innerHTML = html;

        // Pasang event listener untuk logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            window.showConfirmModal("⚠️ Yakin ingin keluar?", async () => {
                await performLogout();
            });
        });

    } catch (e) {
        content.innerHTML =
        '<div class="placeholder"><p>❌ Gagal memuat profil.</p></div>';
    }
}