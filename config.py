import os

# ==================== TELEGRAM ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel")

CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Unity Projects")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")

# ==================== GITHUB ====================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Параметры поиска
GITHUB_MIN_STARS = 10
GITHUB_MAX_STARS = 500
GITHUB_MIN_YEAR = 2020

# ==================== GROQ ====================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ==================== РАСПИСАНИЕ ====================
# Каждые 6 часов = 4 поста в день
CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "6"))

# ==================== БАЗА ДАННЫХ ====================
DATABASE_URL = os.getenv("DATABASE_URL", "")

# ==================== ПРОМПТ ====================
POST_SYSTEM_PROMPT = """Ты — редактор Telegram-канала про Unity-проекты на GitHub.
Пишешь кратко, по делу, с энтузиазмом геймдева.
Используешь ТОЛЬКО HTML-разметку Telegram: <b>жирный</b>, <i>курсив</i>, <a href="...">ссылка</a>.
Никогда не используешь Markdown: **слово** — это не работает в Telegram.
Подпись канала НЕ добавляешь — она добавляется автоматически."""

POST_USER_PROMPT = """Напиши пост про этот Unity-проект с GitHub.

СТРУКТУРА ПОСТА:

1. Первая строка — эмодзи + цепляющий заголовок жирным шрифтом.
   Вставь ссылку на репозиторий в подходящее слово.
   Формат: <b>[эмодзи] [заголовок с ссылкой]</b>
   Примеры:
   <b>🎮 Открытый шутер на Unity — <a href="{url}">исходники на GitHub</a></b>
   <b>🧩 Процедурная генерация уровней — <a href="{url}">смотреть код</a></b>
   <b>🚀 Мобильная RPG с открытым кодом — <a href="{url}">разбираем</a></b>

2. Пустая строка

3. 2-3 коротких абзаца — что за проект, чем интересен, что можно взять на заметку.
   Между абзацами одна пустая строка.

4. Если есть ссылка на itch.io — добавь отдельной строкой:
   🕹 <a href="{itch_url}">Поиграть на itch.io</a>

Название репозитория: {repo_name}
Описание: {description}
Язык: {language}
Звёзды: {stars}
Создан: {created_at}
Ссылка: {url}
README (первые 2000 символов):
{readme}

Ответь только готовым текстом поста без пояснений. Без подписи канала в конце."""
