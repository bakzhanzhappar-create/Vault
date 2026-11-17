if (!sessionStorage.getItem("vault_dek")) {
    window.location.href = "/auth";
}

document.addEventListener("DOMContentLoaded", () => {
    loadVaultData();

    // Кнопки управления
    document.getElementById("refresh-btn").addEventListener("click", loadVaultData);

    const modal = document.getElementById("add-modal");
    const addBtn = document.getElementById("add-btn");
    const closeBtn = document.getElementById("modal-close");
    const saveBtn = document.getElementById("modal-save");

    // Открытие модалки
    addBtn.addEventListener("click", () => {
        modal.style.display = "flex";
    });

    // Закрытие модалки
    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.style.display = "none";
    });

    // Сохранение записи
    saveBtn.addEventListener("click", async () => {
        const titleInput = document.getElementById("input-title");
        const secretInput = document.getElementById("input-secret");

        const title = titleInput.value.trim();
        const secret = secretInput.value.trim();

        if (!title || !secret) {
            alert("Заполни оба поля!");
            return;
        }

        try {
            const response = await fetch(`http://127.0.0.1:9876/api/write?title=${encodeURIComponent(title)}&secret=${encodeURIComponent(secret)}`, {
                method: "POST"
            });

            if (response.ok) {
                titleInput.value = "";
                secretInput.value = "";
                modal.style.display = "none";
                loadVaultData(); // Перезагружаем список
            } else {
                alert("Ошибка при сохранении на сервере");
            }
        } catch (error) {
            console.error("Ошибка сети:", error);
            alert("Не удалось подключиться к серверу");
        }
    });
});

async function loadVaultData() {
    const listContainer = document.getElementById("vault-list");
    const badge = document.getElementById("count-badge");

    listContainer.innerHTML = `<div class="loading-state">Загрузка данных из базы...</div>`;

    try {
        const response = await fetch("http://127.0.0.1:9876/api/show");
        const data = await response.json();

        if (data.result && data.result.length > 0) {
            listContainer.innerHTML = "";
            badge.textContent = `${data.result.length} записей`;

            data.result.forEach(row => {
                const [sessionId, titleData, secretData] = row;

                const titleText = typeof titleData === 'object' && titleData !== null
                    ? (titleData.title || JSON.stringify(titleData))
                    : (titleData || 'Без названия');

                const secretText = typeof secretData === 'object' && secretData !== null
                    ? (secretData.secret || JSON.stringify(secretData))
                    : (secretData || 'Пусто');

                const card = document.createElement("div");
                card.className = "vault-card";
                card.innerHTML = `
                    <div class="card-header-row">
                        <h3>📌 ${titleText}</h3>
                        <span class="uuid">${sessionId ? sessionId.substring(0, 8) : ''}...</span>
                    </div>
                    <div class="secret-container">
                        <span class="secret-label">Секрет / Данные</span>
                        <div class="secret-value">${secretText}</div>
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