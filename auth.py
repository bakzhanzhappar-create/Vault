import os
from enigma import initialize_vault, load_dek, CONFIG_FILE


class VaultSession:
    def __init__(self):
        self._dek = None

    @property
    def is_active(self) -> bool:
        """Проверка, активна ли сессия (заменяет `if not CURRENT_DEK`)"""
        return self._dek is not None

    @property
    def dek(self) -> bytes:
        if not self._dek:
            raise RuntimeError("Сессия не активна!")
        return self._dek

    def authenticate(self):
        """Интерактивная авторизация или инициализация хранилища"""
        print("===== АВТОРИЗАЦИЯ / ИНИЦИАЛИЗАЦИЯ ХРАНИЛИЩА =====")

        if not os.path.exists(CONFIG_FILE):
            print("Конфигурация не найдена. Создадим новый мастер-пароль.")
            while True:
                password = input("Введите новый мастер-пароль: ")
                if password.strip():
                    if initialize_vault(password):
                        self._dek = load_dek(password)
                        print("Мастер-пароль успешно создан, сессия активна!")
                        return True
                    print("Ошибка инициализации.")
                else:
                    print("Пароль не может быть пустым.")
        else:
            while True:
                password = input("Введите мастер-пароль для разблокировки сессии: ")
                dek = load_dek(password)
                if dek is not None:
                    self._dek = dek
                    print("Сессия успешно разблокирована!\n")
                    return True
                else:
                    print("Неверный пароль или ошибка конфигурации! Попробуйте снова.")

    def set_dek(self, dek: bytes):
        """Полезно, например, после импорта бэкапа"""
        self._dek = dek