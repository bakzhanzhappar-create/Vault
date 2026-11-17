// Проверка авторизации: если нет ключа в сессии, кидаем на /auth
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

    // Сохранение записи с шифрованием на клиенте
    saveBtn.addEventListener("click", async () => {
        const titleInput = document.getElementById("input-title");
        const secretInput = document.getElementById("input-secret");

        const rawTitle = titleInput.value.trim();
        const rawSecret = secretInput.value.trim();

        if (!rawTitle || !rawSecret) {
            alert("Заполни оба поля!");
            return;
        }

        try {
            // Восстанавливаем DEK из sessionStorage
            const rawDekBase64 = sessionStorage.getItem("vault_dek");
            const rawDekBuffer = vaultCrypto.base64ToArrayBuffer(rawDekBase64);
            const dek = await window.crypto.subtle.importKey(
                "raw",
                rawDekBuffer,
                { name: "AES-GCM", length: 256 },
                true,
                ["encrypt", "decrypt"]
            );

            const sessionId = crypto.randomUUID();

            // Шифруем заголовок и секрет на клиенте (с привязкой sessionId в качестве AAD)
            const encryptedTitle = await vaultCrypto.encryptItem(dek, sessionId, { text: rawTitle });
            const encryptedSecret = await vaultCrypto.encryptItem(dek, sessionId, { text: rawSecret });

            const payload = {
                session_id: sessionId,
                title: encryptedTitle,
                secret: encryptedSecret
            };

            const response = await fetch("http://127.0.0.1:9876/api/write", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
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
            console.error("Ошибка шифрования/сети:", error);
            alert("Не удалось зашифровать или отправить данные");
        }
    });
});

async function loadVaultData() {
    const listContainer = document.getElementById("vault-list");
    const badge = document.getElementById("count-badge");

    listContainer.innerHTML = `<div class="loading-state">Загрузка данных из базы...</div>`;

    try {
        // Восстанавливаем DEK для расшифровки
        const rawDekBase64 = sessionStorage.getItem("vault_dek");
        let dek = null;
        if (rawDekBase64) {
            const rawDekBuffer = vaultCrypto.base64ToArrayBuffer(rawDekBase64);
            dek = await window.crypto.subtle.importKey(
                "raw",
                rawDekBuffer,
                { name: "AES-GCM", length: 256 },
                true,
                ["encrypt", "decrypt"]
            );
        }

        const response = await fetch("http://127.0.0.1:9876/api/show");
        const data = await response.json();

        if (data.result && data.result.length > 0) {
            listContainer.innerHTML = "";
            badge.textContent = `${data.result.length} записей`;

            for (const row of data.result) {
                const [sessionId, titleData, secretData] = row;

                let titleText = 'Без названия';
                let secretText = 'Пусто';

                try {
                    // Безопасная расшифровка заголовка
                    if (dek && titleData && typeof titleData === 'object' && titleData.nonce && titleData.ciphertext) {
                        const decryptedTitleObj = await vaultCrypto.decryptItem(dek, sessionId, titleData);
                        titleText = decryptedTitleObj.text || JSON.stringify(decryptedTitleObj);
                    } else if (typeof titleData === 'string') {
                        titleText = titleData;
                    } else if (titleData && titleData.title) {
                        titleText = titleData.title;
                    }
                } catch (e) {
                    titleText = "[Зашифровано / Ошибка ключа]";
                }

                try {
                    // Безопасная расшифровка секрета
                    if (dek && secretData && typeof secretData === 'object' && secretData.nonce && secretData.ciphertext) {
                        const decryptedSecretObj = await vaultCrypto.decryptItem(dek, sessionId, secretData);
                        secretText = decryptedSecretObj.text || JSON.stringify(decryptedSecretObj);
                    } else if (typeof secretData === 'string') {
                        secretText = secretData;
                    } else if (secretData && secretData.secret) {
                        secretText = secretData.secret;
                    }
                } catch (e) {
                    secretText = "[Зашифровано / Ошибка ключа]";
                }

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
            }
        } else {
            badge.textContent = "0 записей";
            listContainer.innerHTML = `<div class="empty-state">Хранилище пока пусто. Данные из БД не найдены.</div>`;
        }
    } catch (error) {
        console.error("Ошибка при загрузке и расшифровке данных:", error);
        badge.textContent = "Ошибка";
        listContainer.innerHTML = `<div class="empty-state" style="color: #ff6b6b;">Ошибка подключения или расшифровки!</div>`;
    }
}