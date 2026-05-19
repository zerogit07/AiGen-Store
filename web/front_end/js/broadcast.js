// web/front_end/js/broadcast.js

(() => {
    let broadcastTarget = '';
    let broadcastText = '';

    window.loadBroadcastPage = async function () {
        try {
            const res = await fetch('/api/broadcast/targets');
            const targets = await res.json();

            let html = `
                <div class="broadcast-header">
                    <div class="broadcast-title">
                        📣 Pilih Target
                    </div>
                </div>
            `;

            targets.forEach((t) => {
                html += `
                    <div
                        class="card broadcast-target-card"
                        onclick="selectBroadcastTarget(
                            '${t.key}',
                            '${t.label}',
                            ${t.count}
                        )"
                    >
                        <div class="card-row">
                            <span class="card-value">
                                ${t.label}
                            </span>

                            <span class="card-label">
                                ${t.count} user
                            </span>
                        </div>
                    </div>
                `;
            });

            content.innerHTML = html;

        } catch (e) {
            console.error(e);

            content.innerHTML = `
                <div class="placeholder">
                    <p>❌ Gagal memuat target.</p>
                </div>
            `;
        }
    };

    window.selectBroadcastTarget = function (
        key,
        label,
        count
    ) {
        broadcastTarget = key;

        const html = `
            <div class="broadcast-title broadcast-target-title">
                📣 Target: ${label}
                (${count} user)
            </div>

            <textarea
                id="broadcastMessage"
                class="broadcast-textarea"
                rows="5"
                placeholder="Tulis pesan..."
            >${broadcastText}</textarea>

            <button
                class="btn btn-primary btn-full"
                onclick="sendBroadcastNow()"
            >
                🚀 Kirim
            </button>

            <button
                class="btn btn-outline btn-full"
                onclick="loadBroadcastPage()"
            >
                ← Kembali
            </button>

            <div id="broadcastResult"></div>
        `;

        content.innerHTML = html;
    };

    window.sendBroadcastNow = async function () {
        const textarea =
            document.getElementById(
                'broadcastMessage'
            );

        broadcastText =
            textarea.value.trim();

        if (!broadcastText) {
            showToast(
                '⚠️ Pesan kosong',
                'error'
            );
            return;
        }

        showToast(
            '⏳ Mengirim...',
            'info'
        );

        try {
            const formData =
                new FormData();

            formData.append(
                'target',
                broadcastTarget
            );

            formData.append(
                'text',
                broadcastText
            );

            const res = await fetch(
                '/api/broadcast/send',
                {
                    method: 'POST',
                    body: formData
                }
            );

            const data =
                await res.json();

            if (data.success) {

                content.innerHTML = `
                    <div class="broadcast-title broadcast-report-title">
                         📣 Laporan Broadcast
                    </div>

                    <div class="card">
                        <div class="card-row">
                            <span>Total</span>
                            <span>${data.total}</span>
                        </div>

                        <div class="card-row">
                            <span>Terkirim</span>
                            <span style="color:var(--green)">
                                ${data.sent}
                            </span>
                        </div>

                        <div class="card-row">
                            <span>Gagal</span>
                            <span style="color:var(--red)">
                                ${data.failed}
                            </span>
                        </div>
                    </div>

                    <button
                        class="btn btn-primary btn-full"
                        onclick="loadBroadcastPage()"
                    >
                        Tutup
                    </button>
                `;

                broadcastText = '';

                showToast(
                    data.message,
                    'success'
                );

            } else {
                showToast(
                    data.message,
                    'error'
                );
            }

        } catch (e) {
            console.error(e);

            showToast(
                '❌ Gagal mengirim',
                'error'
            );
        }
    };
})();