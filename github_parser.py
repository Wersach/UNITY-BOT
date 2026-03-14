import random
import logging
import requests
from datetime import datetime, timezone
from config import GITHUB_TOKEN, GITHUB_MIN_STARS, GITHUB_MAX_STARS, GITHUB_MIN_YEAR

logger = logging.getLogger(__name__)

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def _get(url: str, params: dict = None) -> dict | None:
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[GitHub] Ошибка запроса {url}: {e}")
        return None


def _get_readme(owner: str, repo: str) -> str:
    data = _get(f"https://api.github.com/repos/{owner}/{repo}/readme")
    if not data:
        return ""
    import base64
    try:
        content = data.get("content", "")
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        return decoded[:2000]
    except Exception:
        return ""


def _find_itch_url(readme: str) -> str:
    import re
    m = re.search(r"https?://[a-z0-9\-]+\.itch\.io/[^\s\)\"']+", readme, re.IGNORECASE)
    return m.group(0) if m else ""


def search_unity_repos() -> list[dict]:
    results = []

    # Случайная страница чтобы каждый раз разные репозитории
    total_pages = 10
    page = random.randint(1, total_pages)

    query = (
        f"topic:unity stars:{GITHUB_MIN_STARS}..{GITHUB_MAX_STARS} "
        f"created:>{GITHUB_MIN_YEAR}-01-01 language:C#"
    )

    data = _get(
        "https://api.github.com/search/repositories",
        params={
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": 10,
            "page": page,
        },
    )

    if not data or "items" not in data:
        logger.error("[GitHub] Не удалось получить список репозиториев")
        return []

    items = data["items"]
    random.shuffle(items)

    for item in items:
        owner = item["owner"]["login"]
        repo = item["name"]
        readme = _get_readme(owner, repo)
        itch_url = _find_itch_url(readme)

        created = item.get("created_at", "")[:10]

        results.append({
            "url": item["html_url"],
            "repo_name": f"{owner}/{repo}",
            "description": item.get("description") or "Описание отсутствует",
            "language": item.get("language") or "C#",
            "stars": item.get("stargazers_count", 0),
            "created_at": created,
            "readme": readme,
            "itch_url": itch_url,
            "image_url": f"https://opengraph.githubassets.com/1/{owner}/{repo}",
        })

    logger.info(f"[GitHub] Найдено репозиториев: {len(results)} (страница {page})")
    return results
