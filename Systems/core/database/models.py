"""
Database Models
---------------
ORM модели для SwiftDevBot
"""

from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from Systems.core.database.engine import Base


class User(Base):
    """Модель пользователя Telegram"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # Роли и права
    is_superadmin = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    
    # Метаданные
    language_code = Column(String(10), default="ru")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime, nullable=True)
    
    # Дополнительные данные
    extra_data = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


class Session(Base):
    """Модель сессии пользователя"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Тип сессии
    session_type = Column(String(50), default="web")  # web, bot, api
    
    # Временные метки
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    last_used = Column(DateTime, server_default=func.now())
    
    # Метаданные
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    extra_data = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, type={self.session_type})>"


class Module(Base):
    """Модель установленного модуля"""
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    
    # Статус модуля
    enabled = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    
    # Версия и метаданные
    version = Column(String(50), nullable=True)
    author = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Конфигурация модуля
    config = Column(JSON, nullable=True)
    permissions = Column(JSON, nullable=True)
    
    # Временные метки
    installed_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_loaded = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Module(id={self.id}, name={self.name}, enabled={self.enabled})>"


class Setting(Base):
    """Модель настроек системы"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    
    # Тип значения (для правильной десериализации)
    value_type = Column(String(50), default="string")  # string, int, bool, json
    
    # Категория настройки
    category = Column(String(100), default="general")
    
    # Описание
    description = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Setting(key={self.key}, value={self.value})>"


class AuditLog(Base):
    """Модель журнала аудита"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    
    # Действие
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)
    
    # Детали
    description = Column(Text, nullable=True)
    changes = Column(JSON, nullable=True)
    
    # Метаданные
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Временная метка
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"

