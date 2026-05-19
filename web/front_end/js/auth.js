function showToast(message, type = 'error') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast-msg ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

async function performLogin(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (result.success) {
            showToast("Login berhasil!", "success");
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(result.message || "Login gagal");
        }
    } catch (error) {
        showToast("Terjadi kesalahan koneksi.");
    }
}

async function performLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.reload();
}
