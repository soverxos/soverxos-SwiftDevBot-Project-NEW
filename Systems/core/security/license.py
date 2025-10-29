"""
License Validation System
------------------------
Базовая система валидации лицензионных ключей SwiftDevBot
"""

import os
import json
import hashlib
import hmac
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from Systems.core.logging.logger import logger
from Systems.core.config.settings import SDB_ENV
from Systems.core.database.engine import get_async_session
from Systems.core.database.models import Setting


class LicenseValidator:
    """Валидатор лицензионных ключей"""

    def __init__(self):
        self.license_key: Optional[str] = None
        self.license_data: Optional[Dict[str, Any]] = None
        self.secret_key = os.getenv("LICENSE_SECRET", "default_secret_change_in_prod")
        self._is_valid = False
        self._last_check = 0
        self.check_interval = 3600  # Проверка лицензии каждый час

    async def initialize(self):
        """Инициализация валидатора лицензии"""
        logger.info("🔐 LicenseValidator: initializing...")

        # Загрузка лицензионного ключа из переменных окружения или БД
        self.license_key = os.getenv("SDB_LICENSE_KEY")

        if not self.license_key and SDB_ENV != "dev":
            logger.warning("⚠️ LicenseValidator: no license key found in production environment")
            self._is_valid = False
            return

        # В dev режиме разрешаем работу без лицензии
        if SDB_ENV == "dev":
            logger.info("🔐 LicenseValidator: development mode - license validation disabled")
            self._is_valid = True
            return

        # Валидация лицензии
        is_valid, license_data = await self.validate_license()
        self._is_valid = is_valid
        self.license_data = license_data

        if self._is_valid:
            logger.info(f"✅ LicenseValidator: license validated successfully for {license_data.get('organization', 'unknown')}")
        else:
            logger.error("❌ LicenseValidator: license validation failed")

    def is_valid(self) -> bool:
        """Проверка валидности лицензии"""
        # Периодическая перепроверка
        if time.time() - self._last_check > self.check_interval:
            # Здесь можно добавить асинхронную перепроверку
            self._last_check = time.time()

        return self._is_valid

    def get_license_info(self) -> Optional[Dict[str, Any]]:
        """Получить информацию о лицензии"""
        return self.license_data

    def get_limits(self) -> Dict[str, Any]:
        """Получить лимиты лицензии"""
        if not self.license_data:
            return self._get_default_limits()

        return {
            "max_users": self.license_data.get("max_users", 10),
            "max_modules": self.license_data.get("max_modules", 5),
            "max_bots": self.license_data.get("max_bots", 1),
            "features": self.license_data.get("features", []),
            "expires_at": self.license_data.get("expires_at"),
        }

    def _get_default_limits(self) -> Dict[str, Any]:
        """Получить лимиты по умолчанию (для dev режима)"""
        return {
            "max_users": 100,
            "max_modules": 50,
            "max_bots": 10,
            "features": ["all"],
            "expires_at": None,
        }

    async def validate_license(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Валидация лицензионного ключа"""
        if not self.license_key:
            return False, None

        try:
            # Декодирование лицензии (простая реализация)
            license_data = self._decode_license(self.license_key)

            # Проверка подписи
            if not self._verify_signature(license_data):
                logger.error("❌ LicenseValidator: invalid license signature")
                return False, None

            # Проверка срока действия
            if not self._check_expiration(license_data):
                logger.error("❌ LicenseValidator: license expired")
                return False, None

            return True, license_data

        except Exception as e:
            logger.error(f"❌ LicenseValidator: license validation error: {e}")
            return False, None

    def _decode_license(self, license_key: str) -> Dict[str, Any]:
        """Декодирование лицензионного ключа"""
        # Простая реализация: license_key в формате base64
        import base64
        import json

        try:
            # Разделение на данные и подпись
            parts = license_key.split(".")
            if len(parts) != 2:
                raise ValueError("Invalid license format")

            data_b64, signature_b64 = parts

            # Декодирование данных
            data_json = base64.b64decode(data_b64).decode('utf-8')
            data = json.loads(data_json)

            # Декодирование подписи
            signature = base64.b64decode(signature_b64)

            # Сохранение подписи для проверки
            data['_signature'] = signature

            return data

        except Exception as e:
            raise ValueError(f"Failed to decode license: {e}")

    def _verify_signature(self, license_data: Dict[str, Any]) -> bool:
        """Проверка цифровой подписи лицензии"""
        try:
            signature = license_data.pop('_signature')

            # Создание данных для подписи
            data_str = json.dumps(license_data, sort_keys=True)
            expected_signature = hmac.new(
                self.secret_key.encode(),
                data_str.encode(),
                hashlib.sha256
            ).digest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception:
            return False

    def _check_expiration(self, license_data: Dict[str, Any]) -> bool:
        """Проверка срока действия лицензии"""
        expires_at = license_data.get("expires_at")
        if not expires_at:
            return True  # Бессрочная лицензия

        try:
            # expires_at может быть timestamp или ISO string
            if isinstance(expires_at, str):
                expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            else:
                expires_dt = datetime.fromtimestamp(expires_at)

            return datetime.now() < expires_dt

        except Exception:
            logger.error("❌ LicenseValidator: failed to parse expiration date")
            return False

    async def save_license_to_db(self):
        """Сохранение информации о лицензии в БД"""
        if not self.license_data:
            return

        try:
            async with get_async_session() as session:
                # Сохранение статуса лицензии
                setting = Setting(
                    key="license_status",
                    value="valid" if self._is_valid else "invalid",
                    value_type="string",
                    category="license"
                )
                session.add(setting)

                # Сохранение данных лицензии
                license_setting = Setting(
                    key="license_data",
                    value=json.dumps(self.license_data),
                    value_type="json",
                    category="license"
                )
                session.add(license_setting)

                await session.commit()

        except Exception as e:
            logger.error(f"❌ LicenseValidator: failed to save license to DB: {e}")


# Глобальный экземпляр валидатора
license_validator = LicenseValidator()
