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
POST_SYSTEM_PROMPT = """Ты — редактор Telegram-канала про Unity-игры на GitHub.
Пишешь кратко, по делу, как геймдев-энтузиаст.
Используешь ТОЛЬКО HTML-разметку Telegram: <b>жирный</b>, <i>курсив</i>, <a href="...">ссылка</a>.
Никогда не используешь Markdown: **слово** — это не работает в Telegram.
Подпись канала НЕ добавляешь — она добавляется автоматически."""

IS_GAME_PROMPT = """Это Unity-репозиторий. Определи — это ИГРА или нет (тулза, SDK, ассет, плагин, шаблон, система).

Название: {repo_name}
Описание: {description}
README:
{readme}

Ответь ТОЛЬКО одним словом: YES если это игра, NO если это не игра."""

POST_USER_PROMPT = """Напиши пост про эту Unity-игру с GitHub строго по шаблону.

ШАБЛОН (соблюдай точно):

[эмодзи по жанру]<b>[Название игры]</b>
<blockquote>[1-2 предложения — суть игры, жанр, статус (готовая/alpha/demo)]</blockquote>

⚙️<b>Особенности:</b>
     • [особенность 1]
     • [особенность 2]
     • [особенность 3]

🔖<b>Теги:</b>
<b>[теги через пробел, например: #2D #Roguelike #PC #Unity]</b>

📂<b>Ссылка:</b>
<b><a href="{url}">{url}</a></b>

ВАЖНО:
- Описание (1-2 предложения) оборачивай в тег <blockquote>...</blockquote>
- Эмодзи выбирай по жанру: 🗡️ экшен, 🧩 головоломка, 🚀 шутер, 👻 хоррор, 🏰 стратегия, 🎲 roguelike и т.д.
- Теги на английском, с решёткой, сами теги внутри тега <b>
- Тег #C# НЕ используй — он в каждой Unity-игре, незачем
- Не придумывай то чего нет в README

Название репозитория: {repo_name}
Описание: {description}
Язык: {language}
Звёзды: {stars}
Создан: {created_at}
Ссылка: {url}
README (первые 2000 символов):
{readme}

Ответь только готовым текстом поста без пояснений. Без подписи канала в конце."""
