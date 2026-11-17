document.addEventListener("DOMContentLoaded", () => {
    const unlockBtn = document.getElementById("unlock-btn");
    const passwordInput = document.getElementById("master-password");
    const errorBox = document.getElementById("auth-error");

    unlockBtn.addEventListener("click", handleUnlock);
    passwordInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleUnlock();
    });

    async function handleUnlock() {
        const password = passwordInput.value.trim();
        if (!password) {
            showError("Введите мастер-пароль!");
            return;
        }

        unlockBtn.textContent = "Проверка...";
        unlockBtn.disabled = true;
        errorBox.style.display = "none";

        try {
            // 1. Проверяем/получаем конфиг с сервера (соль и зашифрованный DEK)
            let response = await fetch("/api/config/get");

            if (response.status === 404) {
                // Если конфига нет — это первый запуск, инициализируем хранилище!
                await initializeNewVault(password);
                return;
            }

            const config = await response.json();

            // 2. Вычисляем KEK и расшифровываем DEK
            const saltBytes = vaultCrypto.base64ToArrayBuffer(config.salt);
            const kek = await vaultCrypto.deriveKey(password, saltBytes);

            const dek = await vaultCrypto.decryptDEK(kek, config.nonce, config.encrypted_dek);

            if (!dek) {
                throw new Error("Неверный мастер-пароль!");
            }

            // Сохраняем raw DEK во временную сессию (или экспортируем для сессии)
            // Для простоты сохраняем сериализованный DEK в sessionStorage
            const rawDekBuffer = await window.crypto.subtle.exportKey("raw", dek);
            sessionStorage.setItem("vault_dek", vaultCrypto.arrayBufferToBase64(rawDekBuffer));

            // Успех! Переходим на главную
            window.location.href = "/";

        } catch (error) {
            console.error(error);
            showError("Ошибка: Неверный мастер-пароль или сбой криптографии.");
            unlockBtn.textContent = "Разблокировать";
            unlockBtn.disabled = false;
        }
    }

    async function initializeNewVault(password) {
        try {
            // Генерируем соль и DEK
            const salt = vaultCrypto.generateRandomBytes(16);
            const kek = await vaultCrypto.deriveKey(password, salt);
            const dek = await vaultCrypto.generateDEK();

            // Шифруем DEK с помощью KEK
            const encryptedData = await vaultCrypto.encryptDEK(kek, dek);

            const payload = {
                salt: vaultCrypto.arrayBufferToBase64(salt),
                nonce: encryptedData.nonce,
                encrypted_dek: encryptedData.encrypted_dek
            };

            // Сохраняем конфиг на сервер
            const res = await fetch("/api/config/set", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Не удалось сохранить конфигурацию на сервере");

            // Экспортируем DEK в сессию
            const rawDekBuffer = await window.crypto.subtle.exportKey("raw", dek);
            sessionStorage.setItem("vault_dek", vaultCrypto.arrayBufferToBase64(rawDekBuffer));

            window.location.href = "/";
        } catch (e) {
            console.error(e);
            showError("Не удалось инициализировать хранилище.");
            unlockBtn.textContent = "Разблокировать";
            unlockBtn.disabled = false;
        }
    }

    function showError(msg) {
        errorBox.textContent = msg;
        errorBox.style.display = "block";
    }
});