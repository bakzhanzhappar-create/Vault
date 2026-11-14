document.addEventListener("DOMContentLoaded", () => {
    loadVaultData();
    document.getElementById("refresh-btn").addEventListener("click", loadVaultData);
});

async function loadVaultData() {
    const listContainer = document.getElementById("vault-list");
    const badge = document.getElementById("count-badge");

    listContainer.innerHTML = `<div class="loading-state">Загрузка данных из базы...</div>`;

    try {
        const response = await fetch("/api/show");
        const data = await response.json();

        if (data.result && data.result.length > 0) {
            listContainer.innerHTML = "";
            badge.textContent = `${data.result.length} записей`;

            data.result.forEach(row => {
                const [sessionId, titleData, secretData] = row;

                const titleText = typeof titleData === 'object' ? (titleData.title || JSON.stringify(titleData)) : titleData;
                const secretText = typeof secretData === 'object' ? (secretData.secret || JSON.stringify(secretData)) : secretData;

                const card = document.createElement("div");
                card.className = "vault-card";
                card.innerHTML = `
                    <div class="card-header-row">
                        <h3>📌 ${titleText || 'Без названия'}</h3>
                        <span class="uuid">${sessionId.substring(0, 8)}...</span>
                    </div>
                    <div class="secret-container">
                        <span class="secret-label">Секрет / Данные</span>
                        <div class="secret-value">${secretText || 'Пусто'}</div>
                    </div>
                `;
                listContainer.appendChild(card);
            });
        } else {
            badge.textContent = "0 записей";
            listContainer.innerHTML = `<div class="empty-state">Хранилище пока пусто. Данные из БД не найдены.</div>`;
        }
    } catch (error) {
        console.error("Ошибка при загрузке данных:", error);
        badge.textContent = "Ошибка";
        listContainer.innerHTML = `<div class="empty-state" style="color: #ff6b6b;">Ошибка подключения к FastAPI серверу!</div>`;
    }
}