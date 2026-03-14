import time
import logging
import requests
from config import POST_SYSTEM_PROMPT, POST_USER_PROMPT, IS_GAME_PROMPT, GROQ_API_KEY

logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _ask_groq(system: str, user: str, max_tokens: int = 10) -> str:
    try:
        time.sleep(2)
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"[AI] Ошибка запроса: {e}")
        return ""


def is_game(repo: dict) -> bool:
    prompt = IS_GAME_PROMPT.format(
        repo_name=repo["repo_name"],
        description=repo["description"],
        readme=repo["readme"][:1000],
    )
    result = _ask_groq("Ты определяешь является ли репозиторий игрой.", prompt, max_tokens=5)
    answer = result.upper().strip()
    logger.info(f"[AI] is_game для {repo['repo_name']}: {answer}")
    return answer.startswith("YES")


def generate_post(repo: dict) -> str:
    prompt = POST_USER_PROMPT.format(
        url=repo["url"],
        repo_name=repo["repo_name"],
        description=repo["description"],
        language=repo["language"],
        stars=repo["stars"],
        created_at=repo["created_at"],
        readme=repo["readme"][:2000],
    )
    result = _ask_groq(POST_SYSTEM_PROMPT, prompt, max_tokens=1024)
    if result:
        logger.info(f"[AI] Пост сгенерирован: {repo['repo_name']}")
        return result
    return f"[ОШИБКА ГЕНЕРАЦИИ] {repo['repo_name']}"
