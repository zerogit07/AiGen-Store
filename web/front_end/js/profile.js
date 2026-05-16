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
        `;

        content.innerHTML = html;

    } catch (e) {
        content.innerHTML =
        '<div class="placeholder"><p>❌ Gagal memuat profil.</p></div>';
    }
}