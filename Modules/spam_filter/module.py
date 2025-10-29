#!/usr/bin/env python3
"""
Spam Filter Module - Advanced spam detection and filtering
Protects chats from unwanted messages and users
"""

import re
import time
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque
from Systems.sdk import BaseModule, get_event_client


class SpamFilter(BaseModule):
    """Advanced spam filtering module"""

    name = "spam_filter"
    version = "1.0.0"
    description = "Advanced spam detection and filtering system"
    author = "SwiftDevBot"
    requires = ["eventbus", "storage", "admin_permissions"]

    def __init__(self):
        super().__init__(__file__.replace('/module.py', ''))

        # Spam detection settings
        self.max_messages_per_minute = 10
        self.max_duplicate_messages = 3
        self.ban_duration_hours = 24
        self.warning_count_before_ban = 3

        # Data structures for tracking
        self.user_messages: Dict[int, deque] = defaultdict(lambda: deque(maxlen=50))
        self.user_warnings: Dict[int, int] = defaultdict(int)
        self.banned_users: Dict[int, float] = {}  # user_id -> ban_expiry_timestamp
        self.message_hashes: Dict[str, List[int]] = defaultdict(list)  # hash -> user_ids

    async def on_load(self):
        await super().on_load()

        # Инициализируем EventBus клиент
        self.eventbus = get_event_client(self.name)

        # Загружаем настройки и статистику
        await self.storage.load()

        # Восстанавливаем заблокированных пользователей
        self._load_banned_users()

        # Регистрируем обработчики событий
        @self.on_event("message.received")
        async def handle_message(event_data):
            """Обработка входящих сообщений для фильтрации спама"""
            message = event_data.get("message", {})
            user = message.get("from_user", {})

            if not user or not message.get("text"):
                return  # Пропускаем не-текстовые сообщения

            user_id = user.get("id")
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "").strip()

            # Проверяем, не заблокирован ли пользователь
            if self._is_user_banned(user_id):
                self.logger.info(f"Banned user {user_id} tried to send message")
                # Здесь можно добавить логику удаления сообщения
                return

            # Выполняем проверки на спам
            spam_detected, spam_type = await self._check_spam(user_id, chat_id, text)

            if spam_detected:
                await self._handle_spam(user_id, chat_id, message, spam_type)
                return

            # Если не спам, обновляем статистику пользователя
            self._update_user_stats(user_id, text)

        @self.on_command("spam_stats")
        async def handle_spam_stats(message):
            """Показать статистику спам-фильтра"""
            if not self._is_admin(message.from_user.id):
                await self.eventbus.send_notification(
                    user_id=message.from_user.id,
                    message="❌ У вас нет прав для просмотра статистики спам-фильтра",
                    type="error"
                )
                return "Access denied"

            stats = self._get_stats()

            response = f"""🛡️ Spam Filter Statistics:

🚫 Banned users: {stats['banned_count']}
⚠️ Total warnings: {stats['total_warnings']}
📊 Messages processed: {stats['messages_processed']}
🎯 Spam detected: {stats['spam_detected']}

📈 Current active bans: {len(self.banned_users)}
🕐 Next ban expires in: {stats['next_expiry']}"""

            await self.eventbus.send_notification(
                user_id=message.from_user.id,
                message=response,
                type="info"
            )

            return "Stats sent"

        @self.on_command("unban")
        async def handle_unban(message):
            """Разблокировать пользователя"""
            if not self._is_admin(message.from_user.id):
                await self.eventbus.send_notification(
                    user_id=message.from_user.id,
                    message="❌ У вас нет прав для разблокировки пользователей",
                    type="error"
                )
                return "Access denied"

            args = message.text.split()[1:]
            if not args:
                await self.eventbus.send_notification(
                    user_id=message.from_user.id,
                    message="❌ Укажите ID пользователя для разблокировки: /unban <user_id>",
                    type="error"
                )
                return "Usage: /unban <user_id>"

            try:
                target_user_id = int(args[0])
                if target_user_id in self.banned_users:
                    del self.banned_users[target_user_id]
                    await self._save_banned_users()
                    await self.eventbus.send_notification(
                        user_id=message.from_user.id,
                        message=f"✅ Пользователь {target_user_id} разблокирован",
                        type="success"
                    )
                else:
                    await self.eventbus.send_notification(
                        user_id=message.from_user.id,
                        message=f"❌ Пользователь {target_user_id} не заблокирован",
                        type="warning"
                    )
            except ValueError:
                await self.eventbus.send_notification(
                    user_id=message.from_user.id,
                    message="❌ Неверный формат ID пользователя",
                    type="error"
                )

            return "Unban processed"

        @self.web_tab("Spam Filter", "🛡️")
        async def render_spam_tab():
            """Web-вкладка с настройками спам-фильтра"""
            stats = self._get_stats()

            html = f"""
            <div class="spam-filter">
                <h2>🛡️ Spam Filter Module</h2>
                <p class="description">Advanced spam detection and filtering system</p>

                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>🚫 Banned Users</h3>
                        <div class="stat-number">{stats['banned_count']}</div>
                    </div>

                    <div class="stat-card">
                        <h3>⚠️ Total Warnings</h3>
                        <div class="stat-number">{stats['total_warnings']}</div>
                    </div>

                    <div class="stat-card">
                        <h3>📊 Messages Processed</h3>
                        <div class="stat-number">{stats['messages_processed']}</div>
                    </div>

                    <div class="stat-card">
                        <h3>🎯 Spam Detected</h3>
                        <div class="stat-number">{stats['spam_detected']}</div>
                    </div>
                </div>

                <div class="settings-section">
                    <h3>⚙️ Filter Settings</h3>
                    <div class="settings-grid">
                        <div class="setting-item">
                            <label>Max messages per minute:</label>
                            <span>{self.max_messages_per_minute}</span>
                        </div>

                        <div class="setting-item">
                            <label>Max duplicate messages:</label>
                            <span>{self.max_duplicate_messages}</span>
                        </div>

                        <div class="setting-item">
                            <label>Ban duration (hours):</label>
                            <span>{self.ban_duration_hours}</span>
                        </div>

                        <div class="setting-item">
                            <label>Warnings before ban:</label>
                            <span>{self.warning_count_before_ban}</span>
                        </div>
                    </div>
                </div>

                <div class="active-bans">
                    <h3>🚫 Active Bans ({len(self.banned_users)})</h3>
                    <div class="bans-list">
            """

            if self.banned_users:
                for user_id, expiry in list(self.banned_users.items())[:10]:  # Show first 10
                    remaining = max(0, int((expiry - time.time()) / 3600))
                    html += f"""
                        <div class="ban-item">
                            <span>User ID: {user_id}</span>
                            <span>Expires in: {remaining} hours</span>
                        </div>
                    """
            else:
                html += '<p class="no-bans">No active bans</p>'

            html += """
                    </div>
                </div>

                <div class="commands-section">
                    <h3>💬 Available Commands</h3>
                    <div class="commands-list">
                        <div class="command-item">
                            <code>/spam_stats</code>
                            <p>Show spam filter statistics (admin only)</p>
                        </div>
                        <div class="command-item">
                            <code>/unban &lt;user_id&gt;</code>
                            <p>Unban a user (admin only)</p>
                        </div>
                    </div>
                </div>
            </div>

            <style>
            .spam-filter {{
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}

            .description {{
                font-size: 1.1em;
                color: #666;
                margin-bottom: 30px;
            }}

            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .stat-card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: 1px solid #e9ecef;
            }}

            .stat-card h3 {{
                margin: 0 0 10px 0;
                color: #666;
                font-size: 0.9em;
            }}

            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                color: #dc3545;
            }}

            .settings-section, .active-bans, .commands-section {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .settings-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }}

            .setting-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 4px;
            }}

            .setting-item label {{
                font-weight: bold;
                color: #495057;
            }}

            .bans-list {{
                max-height: 200px;
                overflow-y: auto;
            }}

            .ban-item {{
                display: flex;
                justify-content: space-between;
                padding: 10px;
                border-bottom: 1px solid #eee;
                background: #fff5f5;
                border-radius: 4px;
                margin-bottom: 5px;
            }}

            .no-bans {{
                text-align: center;
                color: #666;
                font-style: italic;
                padding: 20px;
            }}

            .commands-list {{
                display: grid;
                gap: 15px;
            }}

            .command-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                border-left: 4px solid #dc3545;
            }}

            .command-item code {{
                display: block;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                color: #dc3545;
                margin-bottom: 5px;
            }}

            .command-item p {{
                margin: 0;
                color: #666;
            }}
            </style>
            """

            return html

    async def _check_spam(self, user_id: int, chat_id: int, text: str) -> Tuple[bool, str]:
        """Check if message is spam"""
        current_time = time.time()

        # 1. Check message frequency (flood protection)
        user_msgs = self.user_messages[user_id]
        recent_messages = [msg_time for msg_time, _ in user_msgs if current_time - msg_time < 60]

        if len(recent_messages) >= self.max_messages_per_minute:
            return True, "flood"

        # 2. Check for duplicate messages
        message_hash = hash(text.lower().strip())
        duplicate_users = self.message_hashes[str(message_hash)]

        # Remove old duplicates (older than 5 minutes)
        duplicate_users = [uid for uid in duplicate_users
                          if any(msg_time for msg_time, msg_hash in self.user_messages[uid]
                                if current_time - msg_time < 300 and msg_hash == message_hash)]

        if len(duplicate_users) >= self.max_duplicate_messages:
            return True, "duplicate"

        # 3. Check for spam patterns
        if self._contains_spam_patterns(text):
            return True, "pattern"

        return False, ""

    def _contains_spam_patterns(self, text: str) -> bool:
        """Check text for spam patterns"""
        spam_patterns = [
            r'http[s]?://[^\s]+',  # URLs (basic spam detection)
            r'@\w+',               # Mentions (potential spam)
            r'[A-Z]{5,}',          # All caps words
            r'(.)\1{4,}',          # Character repetition
        ]

        for pattern in spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    async def _handle_spam(self, user_id: int, chat_id: int, message: Dict, spam_type: str):
        """Handle detected spam"""
        self.logger.warning(f"Spam detected from user {user_id}: type={spam_type}")

        # Increment warning count
        self.user_warnings[user_id] += 1

        # Update statistics
        stats = self._get_stats()
        stats['spam_detected'] += 1
        await self._save_stats(stats)

        # Check if user should be banned
        if self.user_warnings[user_id] >= self.warning_count_before_ban:
            await self._ban_user(user_id)
            spam_type = "banned"

        # Send notification
        notification_msg = f"⚠️ Spam detected ({spam_type}) from user {user_id}"
        if spam_type == "banned":
            notification_msg += f" - User banned for {self.ban_duration_hours} hours"

        await self.eventbus.send_notification(
            user_id=user_id,
            message=f"⚠️ Your message was flagged as spam ({spam_type}). Warning {self.user_warnings[user_id]}/{self.warning_count_before_ban}",
            type="warning"
        )

    async def _ban_user(self, user_id: int):
        """Ban a user for spam"""
        ban_expiry = time.time() + (self.ban_duration_hours * 3600)
        self.banned_users[user_id] = ban_expiry
        self.user_warnings[user_id] = 0  # Reset warnings

        await self._save_banned_users()

        self.logger.info(f"User {user_id} banned until {ban_expiry}")

    def _is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        if user_id in self.banned_users:
            if time.time() > self.banned_users[user_id]:
                # Ban expired, remove from banned list
                del self.banned_users[user_id]
                self._save_banned_users()
                return False
            return True
        return False

    def _update_user_stats(self, user_id: int, text: str):
        """Update user message statistics"""
        current_time = time.time()
        message_hash = hash(text.lower().strip())

        # Add to user's message history
        self.user_messages[user_id].append((current_time, message_hash))

        # Update message hash tracking
        hash_key = str(message_hash)
        if user_id not in self.message_hashes[hash_key]:
            self.message_hashes[hash_key].append(user_id)

        # Clean old message hashes (keep only recent ones)
        for h_key, users in list(self.message_hashes.items()):
            self.message_hashes[h_key] = [uid for uid in users
                                        if any(msg_time for msg_time, msg_hash in self.user_messages[uid]
                                              if current_time - msg_time < 300 and msg_hash == int(h_key))]

            if not self.message_hashes[h_key]:
                del self.message_hashes[h_key]

    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin (placeholder)"""
        # In real implementation, this would check against admin database
        return user_id == int(self.storage.get("admin_id", 0))

    def _get_stats(self) -> Dict[str, int]:
        """Get spam filter statistics"""
        return {
            'banned_count': len([u for u in self.banned_users.keys() if self._is_user_banned(u)]),
            'total_warnings': sum(self.user_warnings.values()),
            'messages_processed': sum(len(msgs) for msgs in self.user_messages.values()),
            'spam_detected': self.storage.get("spam_detected", 0),
            'next_expiry': self._get_next_ban_expiry()
        }

    def _get_next_ban_expiry(self) -> str:
        """Get time until next ban expires"""
        if not self.banned_users:
            return "No active bans"

        current_time = time.time()
        active_bans = [(uid, expiry) for uid, expiry in self.banned_users.items() if expiry > current_time]

        if not active_bans:
            return "No active bans"

        next_expiry = min(expiry for _, expiry in active_bans)
        hours_left = int((next_expiry - current_time) / 3600)

        return f"{hours_left} hours"

    async def _save_stats(self, stats: Dict[str, int]):
        """Save statistics to storage"""
        for key, value in stats.items():
            if key != 'next_expiry':  # Don't save computed values
                self.storage.set(key, value)
        await self.storage.save()

    def _load_banned_users(self):
        """Load banned users from storage"""
        banned_data = self.storage.get("banned_users", {})
        current_time = time.time()

        # Filter out expired bans
        self.banned_users = {int(uid): float(expiry)
                           for uid, expiry in banned_data.items()
                           if float(expiry) > current_time}

    async def _save_banned_users(self):
        """Save banned users to storage"""
        self.storage.set("banned_users", self.banned_users)
        await self.storage.save()


# Создаем экземпляр модуля
module = SpamFilter()
