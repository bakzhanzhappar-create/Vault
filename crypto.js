// crypto.js — Клиентское шифрование на Web Crypto API

class VaultCrypto {
    constructor() {
        this.subtle = window.crypto.subtle;
    }

    // Генерация случайных байтов (для соли и IV/nonce)
    generateRandomBytes(length = 16) {
        return window.crypto.getRandomValues(new Uint8Array(length));
    }

    // Хелперы для конвертации ArrayBuffer <-> Base64
    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    base64ToArrayBuffer(base64) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    // 1. Вычисление KEK (Key Encryption Key) из мастер-пароля через PBKDF2 (600,000 итераций)
    async deriveKey(masterPassword, saltBytes) {
        const enc = new TextEncoder();
        const passwordKey = await this.subtle.importKey(
            "raw",
            enc.encode(masterPassword),
            { name: "PBKDF2" },
            false,
            ["deriveKey"]
        );

        return await this.subtle.deriveKey(
            {
                name: "PBKDF2",
                salt: saltBytes,
                iterations: 600000,
                hash: "SHA-256"
            },
            passwordKey,
            { name: "AES-GCM", length: 256 },
            true,
            ["encrypt", "decrypt"]
        );
    }

    // 2. Генерация мастер-ключа данных (DEK)
    async generateDEK() {
        return await this.subtle.generateKey(
            { name: "AES-GCM", length: 256 },
            true,
            ["encrypt", "decrypt"]
        );
    }

    // 3. Шифрование DEK с помощью KEK
    async encryptDEK(kek, dek) {
        const rawDek = await this.subtle.exportKey("raw", dek);
        const iv = this.generateRandomBytes(12);
        const ciphertext = await this.subtle.encrypt(
            { name: "AES-GCM", iv: iv },
            kek,
            rawDek
        );
        return {
            nonce: this.arrayBufferToBase64(iv),
            encrypted_dek: this.arrayBufferToBase64(ciphertext)
        };
    }

    // 4. Расшифровка DEK с помощью KEK
    async decryptDEK(kek, nonceBase64, encryptedDekBase64) {
        const iv = this.base64ToArrayBuffer(nonceBase64);
        const ciphertext = this.base64ToArrayBuffer(encryptedDekBase64);

        const rawDek = await this.subtle.decrypt(
            { name: "AES-GCM", iv: iv },
            kek,
            ciphertext
        );

        return await this.subtle.importKey(
            "raw",
            rawDek,
            { name: "AES-GCM", length: 256 },
            true,
            ["encrypt", "decrypt"]
        );
    }

    // 5. Шифрование элемента хранилища (заметки/пароля) с привязкой ID в качестве AAD
    async encryptItem(dek, itemId, dataObj) {
        const iv = this.generateRandomBytes(12);
        const enc = new TextEncoder();
        const plaintext = enc.encode(JSON.stringify(dataObj));
        const aad = enc.encode(itemId);

        const ciphertext = await this.subtle.encrypt(
            {
                name: "AES-GCM",
                iv: iv,
                additionalData: aad
            },
            dek,
            plaintext
        );

        return {
            nonce: this.arrayBufferToBase64(iv),
            ciphertext: this.arrayBufferToBase64(ciphertext)
        };
    }

    // 6. Расшифровка элемента хранилища
    async decryptItem(dek, itemId, encryptedItem) {
        try {
            const iv = this.base64ToArrayBuffer(encryptedItem.nonce);
            const ciphertext = this.base64ToArrayBuffer(encryptedItem.ciphertext);
            const enc = new TextEncoder();
            const aad = enc.encode(itemId);

            const decryptedBuffer = await this.subtle.decrypt(
                {
                    name: "AES-GCM",
                    iv: iv,
                    additionalData: aad
                },
                dek,
                ciphertext
            );

            const dec = new TextDecoder();
            return JSON.parse(dec.decode(decryptedBuffer));
        } catch (e) {
            console.error("Ошибка расшифровки элемента:", e);
            return { title: "[Зашифровано]", secret: "Неверный ключ или поврежденные данные" };
        }
    }
}

// Экспортируем глобальный экземпляр
const vaultCrypto = new VaultCrypto();