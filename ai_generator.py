import time
import logging
import requests
from config import POST_SYSTEM_PROMPT, POST_USER_PROMPT, GROQ_API_KEY

logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def generate_post(repo: dict) -> str:
    prompt = POST_USER_PROMPT.format(
        url=repo["url"],
        itch_url=repo.get("itch_url", ""),
        repo_name=repo["repo_name"],
        description=repo["description"],
        language=repo["language"],
        stars=repo["stars"],
        created_at=repo["created_at"],
        readme=repo["readme"][:2000],
    )
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
                    {"role": "system", "content": POST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1024,
                "temperature": 0.7,
            },
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        text_out = result["choices"][0]["message"]["content"].strip()
        logger.info(f"[AI] Пост сгенерирован: {repo['repo_name']}")
        return text_out
    except Exception as e:
        logger.error(f"[AI] Ошибка генерации: {e}")
        return f"[ОШИБКА ГЕНЕРАЦИИ] {repo['repo_name']}"
